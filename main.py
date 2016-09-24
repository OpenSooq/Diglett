from bottle import Bottle,run, route, request, default_app, HTTPResponse, response
from ConfigParser import SafeConfigParser
from bson.json_util import dumps
from common import Functions
import bottle
import time
import os
import glob
import sys
import re
import logging
import datetime
import pymongo

# Config Parsing
config = SafeConfigParser()
config.read('config.ini')

# current working directory
here = os.path.dirname(__file__)

# logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logging.debug("logging started")
logger = logging.getLogger(__name__)

app = application = Bottle()
functions = Functions()

#/ping
@route('/ping',method='GET')
def ping():
	return 'pong@%d' %(int(time.time()))

#/started?taskname=task_name&time=12312131&host=172.16
@route('/started',method='GET')
def startSignal():
	task= request.query.get('taskname')
	start_time= int(request.query.get('time'))
	if None in [task,start_time]:
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	db_conn = functions.mongoConn('history')
	if not db_conn.insert_one({"name" : task,"start_time" : start_time}):
		return HTTPResponse(status=500,body=dumps({'status' : 'failed'}))
	return HTTPResponse(status=200,body=dumps({'status' : 'sucess'}))

#POST /finish -F log=@/path/log/file -F status=$? -F task=task_name
@route('/finished',method='POST')
def finishSignal():
	status= request.forms.get('status')
	task= request.forms.get('task')
	log_file= request.files.get('log')
	start_time = int(request.forms.get('start_time'))
	log_data = log_file.file.read()
	if not task:
		logger.info("invalid /finish request.")
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	if functions.insertFinishedTask(taskname=task,status_code=status,log=log_data,stime=start_time):
		return HTTPResponse(status=200,body=dumps({'status' : 'success'}))

#/hosts?project=project_name
@route('/hosts',method='GET')
def hostsOfProject():
	project_name = request.query.get('project')
	if not project_name : return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	return functions.hostsOfProject(project_name)

#/addhost?project=project_name&host=192.159.213.42:port
@route('/addhost',method='GET')
def addHostToProject():
	project_name = request.query.get('project')
	hoststr = request.query.get('host')
	host = hoststr.split(':')[0]
	port = hoststr.split(':')[1]
	if not project_name or not functions.checkVaildIP(host) or not str(port).isdigit():
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	db_projects = functions.mongoConn('projects')
	host_exists = db_projects.find({"name" : project_name, "hosts" : hoststr})
	if host_exists.count() > 0 : return HTTPResponse(status=200,body={'status' : 'failed, host already exists'})
	if functions.addHost(project=project_name,ipaddr=host,port=port) :
		return HTTPResponse(status=200,body={'status' : 'sucess'})
	return HTTPResponse(status=200,body={'status' : 'failed'})

#/delhost?project=project_name&host=192.1.1.1:22192
@route('/delhost',method='GET')
def delHostFromProject():
	project_name = request.query.get('project')
	hoststr = request.query.get('host')
	if None in [project_name,hoststr]:
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	db_projects = functions.mongoConn('projects')
	if db_projects.update_many({'name' : project_name},{'$pull' : { 'hosts' : hoststr }}).modified_count > 0 :
		return HTTPResponse(status=200,body={'status' : 'sucess'})
	else:
		return HTTPResponse(status=200,body={'status' : 'failed'})

#/cron?project=project_name
@route('/crons')
def cronsOfProject():
	project_name = request.query.get('project')
	if not project_name : return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	db_crons = functions.mongoConn('crons')
	crons = db_crons.find({"project" : project_name, 'active' : True },{ '_id' : False })
	return dumps(crons)

#/searchcron?project=project_name&namelike=dsadsa&tfrom=datetime&to=datetime
@route('/searchcron')
def searchCrons():
	project_name = request.query.get('project')
	namelike = request.query.get('namelike')
	tfrom = request.query.get('from')
	to = request.query.get('to')

	try: regex = re.compile(namelike,re.IGNORECASE)
	except: pass
	namelike = '^%s.*%s.*' %(project_name,namelike) if namelike != None else None
	db_crons = functions.mongoConn('crons')

	if namelike and (len(tfrom) + len(to)) == 0:
		db_result = db_crons.find({'project' : project_name ,'name' : { '$regex' : regex } })
		return dumps(db_result)

	if (len(tfrom) + len(to)) > 0 :
		today = datetime.datetime.now().strftime('%Y-%m-%d')
		if tfrom == '' : tfrom = '00:00:00'
		if to == '' : to = datetime.datetime.now().strftime('%H:%M:%S')
		tfrom = datetime.datetime.strptime('%s %s' %(today,tfrom), '%Y-%m-%d %H:%M:%S')
		to = datetime.datetime.strptime('%s %s' %(today,to), '%Y-%m-%d %H:%M:%S')
		if namelike :
			db_result = db_crons.find({'project' : project_name ,'name' : { '$regex' : regex } , 'last_run_at' : { '$gte' : tfrom, '$lt' : to}})
		else:
			db_result = db_crons.find({'project' : project_name ,'last_run_at' : { '$gte' : tfrom, '$lt' : to} })
		return dumps(db_result)

#/editcron?task=taskname&set=option&to=
#/editcron?name=taskname&time=
@route('/editcron')
def editCrons():
	taskname = request.query.get('task')
	options = request.query.get('set')
	new_value = request.query.get('to')
	if None in [taskname,options,new_value]:
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	options_list = options.split(',')
	new_value_list = new_value.split(',')
	db_crons = functions.mongoConn('crons')
	if 'name' in options:
		name_index = options.index('name')
		db_result = db_crons.find({'name' : new_value_list[name_index] })
		if db_result.count() > 0 :
			return HTTPResponse(status=200,body=dumps({'status' : 'failed, name already exists'}))
		new_name = new_value_list[name_index]
		db_result = db_crons.update_many({'name' : taskname},{'$set': {'name' : new_value_list[name_index]}})
	for option in options_list:
		index = options_list.index(option)
		if option == 'name' : pass
		else:
			try:
				new_name
				name = new_name
			except NameError: name = taskname
			db_result = db_crons.update_many({'name' : name },{'$set': { option : new_value_list[index]}})
	return HTTPResponse(status=200,body=dumps({'status' : 'sucess'}))

#/addcron?task=taskname&active=0&depends=example1.gulpin,example2.gulpin&
@route('/addcron',method='POST')
def addCronJob():
	taskname= request.forms.get('task')
	depends= request.forms.get('depends',[])
	project= request.forms.get('project')
	active= bool(request.forms.get('active',True))
	command= request.forms.get('command')
	time= request.forms.get('time')
	description = request.forms.get('description',' ')
	if None in [taskname,depends,command,time,project]:
		return HTTPResponse(status=400,body=dsumps({'error' : 'invalid request'}))
	db_crons = functions.mongoConn('crons')
	if db_crons.count({'name' : taskname}) > 0 :
		return HTTPResponse(status=400,body=dumps({'error' : 'taskname is already used'}))
	depends_list = [] if (depends == [])  else depends.split(',')
	if db_crons.insert({'name' : taskname, 'project' : project, 'description' :  description, 'depends_on' : depends_list, 'active' :active, 'command' : command, 'time' : time, 'last_run_at' : datetime.datetime.fromtimestamp(0)}):
		return HTTPResponse(status=200,body=dumps({'status' : 'success'}))

#/delcron?project=project_name&task=taskname
@route('/delcron',method='GET')
def deleteCron():
	project = request.query.get('project')
	taskname = request.query.get('task')
	if None in [project,taskname] :
		return HTTPResponse(status=400,body=dsumps({'error' : 'invalid request'}))
	db_crons = functions.mongoConn('crons')
	if db_crons.delete_many({'name' : taskname}).deleted_count > 0 :
		return HTTPResponse(status=200,body=dumps({'status' : 'success'}))
	else: return HTTPResponse(status=200,body=dumps({'status' : 'failed'}))

#/addproject?name=project_name&user=opensooq
@route('/addproject')
def addProject():
	name = request.query.get('name')
	user = request.query.get('user')
	if None in [name,user]:
		return HTTPResponse(status=400,body=dsumps({'error' : 'invalid request'}))
	db_projects = functions.mongoConn('projects')
	if db_projects.count({'name' : name}) > 0 :
		return HTTPResponse(status=200,body=dumps({'status' : 'failed, name already exist'}))
	if db_projects.insert_one({'name' : name, 'user' : user, 'hosts' : [], 'active_host' : ""}):
		if db_projects.count({'name' : name}) > 0 :
			return HTTPResponse(status=200,body=dumps({'status' : 'success'}))
	return HTTPResponse(status=200,body=dumps({'status' : 'failed'}))

#/generate?project=project_name&update=[0,1]
# update = 0 view # update = 1 update on all hosts
@route('/generate')
def update():
	project_name = request.query.get('project')
	update = int(request.query.get('update'))
	if None in [project_name,update] : return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	if not update:
		crontab_file = functions.createCrontab(project=project_name,manager_url=config.get('manager','manager_url'),enabled=True)
		return open(crontab_file,'r').read()
	else:
		db_projects = functions.mongoConn('projects')
		project_info = db_projects.find_one({'name' : project_name},{'hosts' : 1,'active_host' : 1, 'user' : 1})
		try : project_info['hosts']
		except Exception as e :
			logger.error(' requested project does not exist in db : %r',e)
			return HTTPResponse(status=400,body=dumps({'error' : 'this project is not in database'}))
		failed_host = {}; failed_count=0;
		for host in project_info['hosts']:
			ipaddr = host.split(':')[0]
			port = host.split(':')[1]
			enable_flag = True if host in project_info['active_host'] else False
			crontab = functions.createCrontab(project=project_name,manager_url=config.get('manager','manager_url'),enabled=enable_flag)
			status = functions.broadcastCronJob(host=ipaddr,port=port,user=project_info['user'],filename=crontab)
			if not status :
				failed_count += 1
				failed_host[failed_count] = host
				message = '[ERROR] Broadcasting crontab to host=%s from project=%s failed.\n Sending email to infrateam.' %(ipaddr,project_name)
				functions.notifyAdmin(subject='Diglett : Brodcasting Failed',message=message)
				if not failed_count :
					return HTTPResponse(status=200,body=dumps({'status' : 'success'}))
				else:
					return HTTPResponse(status=400,body=dumps({'error' : 'failed to update some hosts','hosts' : failed_host}))

#/activehost?project=project_name
@route('/activehost')
def activeHost():
	project_name = request.query.get('project')
	db_projects = functions.mongoConn('projects')
	if not project_name or db_projects.find({'name' : project_name}).count() != 1 :
		return HTTPResponse(status=400,body=dumps({'error' : 'invalid request'}))
	hosts = db_projects.find_one({"name" : project_name},{"active_host" : 1, '_id' : False})
	return HTTPResponse(status=200,body=dumps({"active_host" : hosts['active_host']}))

#!/projects
@route('/projects')
def listProjects():
	db_projects = functions.mongoConn('projects')
	projects = db_projects.find({},{"name" : 1, '_id' : False})
	return HTTPResponse(status=200,body=dumps(projects))

#!/activate_host?project=project_name&host=host:PORT
@route('/activate_host')
def activateHost():
	project = request.query.get('project')
	host = request.query.get('host')
	if None in [project,host]: return HTTPResponse(status=400,body={'error' : 'invalid request'})
	db_projects = functions.mongoConn('projects')
	update = db_projects.update_one({'name' : project},{'$set': { 'active_host' : host } })
	if update.modified_count == 1 :
		return HTTPResponse(status=200,body=dumps({'status' : 'success'}))
	logger.warning('number of modified projects while activating a host is not 1, \n the request : %r',request.body.read())
	return HTTPResponse(status=200,body=dumps({'error' : 'something went wrong.'}))

#!/last_log?taskname=task_name
@route('/last_log')
def lastLog():
	taskname = request.query.get('taskname')
	if None in [taskname]: return HTTPResponse(status=400,body={'error' : 'invalid request'})
	db_history = functions.mongoConn('history')
	#db.history.find({name : "gulpin.notify_no_posts", log : {$exists : true}},{log : 1, _id : 0}).sort({start_time : -1}).limit(1)
	log = db_history.find({'name' : taskname, "log" : {"$exists" : True}},{"log" : True, "_id" : False},sort=[('start_time', pymongo.DESCENDING)], limit=1)
	for doc in log :
		data = '<pre>%s</pre>' %doc['log']
		break
	return HTTPResponse(status=200,body=data)
	
############
#### MAIN
############
if __name__ == "__main__" :
	run(host=config.get('bottle','host'), port=config.get('bottle','port'), debug=True)
else:
	application = default_app()
