from ConfigParser import SafeConfigParser
from pymongo import MongoClient
from subprocess import Popen,PIPE,STDOUT
from bson.json_util import dumps
from IPy import IP
import paramiko
import datetime
import logging
import time
import re
import os
import sys

# Logger
logger = logging.getLogger(__name__)

# Config Parsing
config = SafeConfigParser()
config.read('config.ini')

# current working directory
here = os.path.dirname(__file__)

class Functions(object):
	def mongoConn(self,collection):
		client = MongoClient(host=config.get('mongo','host'),port=int(config.get('mongo','port')))
		db_conn = client[config.get('mongo','dbname')]
		return db_conn[collection]

	def sshConnect(self,host,port,user=config.get('manager','admin')):
		try:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(hostname=host,port=port,username=user)
			return ssh
		except Exception as e:
			logger.error('failed to connect to host=%r on port=%r with user=%r, error : %r',host,port,user,e)
			return None

	def checkVaildIP(self,ipaddr):
		if "." not in ipaddr: return False
		try:
			IP(ipaddr)
			return True
		except ValueError:
			return False

	def getProjectHosts(self,project):
		projects = self.mongoConn('projects')
		hosts = projects.find_one({"name" : project},{"hosts" : 1})
		return hosts['hosts']

	def listCronJobsOnHost(self,host,port,user):
		try:
			ssh_conn = self.sshConnect(host=host,port=port,user=config.get('manager','admin'))
			if ssh_conn:
				command = 'sudo crontab -u %r -l' %user
				stdin, stdout, stderr = ssh_conn.exec_command(command)
				if not stderr and stdout : ssh_conn.close(); return stdout.read()
				else: logger.error("executing command %r on host=%r failed with : %r",command,host,stderr); return False
			else:
				logger.info('could not connect to host=%r.\n INFO: Connecting to another host if there is any.',host)
		except Exception as e:
			logger.error("exception in connecting to host=%r on port=%r : %r",host,port,e)
		return False

	def checkDepend(self,task):
		crons = self.mongoConn('crons')
		result = crons.find_one({"name" :task},{"depends_on" : 1})
		if not result['depends_on']: return True
		else:
			for dependency in str(result['depends_on']).split(','):
				chk_query = crons.find_one({"name" : dependency},{"last_run_status" :1})
				if chk_query['last_run_status']:
					return False
			return True

	def insertFinishedTask(self,taskname,status_code,log,stime):
		now = datetime.datetime.now()
		running_time = (now - datetime.datetime.fromtimestamp(stime)).total_seconds()
		try:
			crons = self.mongoConn('crons')
			history = self.mongoConn('history')
			if int(status_code) != 0 :
				try: self.emailInfraTeam(emails=config.get('alert','emails'),object=log,subject='%s failed' %taskname)
				except: pass
			update_cron = crons.update_one({ "name" : taskname},{ "$set" : { "last_run_at" : now, "last_run_status" : status_code }})
			update_history = history.update_one({"name" : taskname, "start_time" : stime},{ "$set" : {"status_code" : status_code, "running_time" : running_time , "log" : log}})
		except Exception as e:
			logger.error("could not update history document : %r",e)
			try: self.emailInfraTeam(emails=config.get('alert','emails'),subject='Insert tasks log in mongo failed',object=e)
			except: pass
			if not os.path.isdir('%s/failed' %here): os.mkdir('%s/failed' %here)
			fname = '%s/failed/%s_log_%s' %(here,taskname,str(now))
			temp_log = open(fname,'w')
			data= '''
				name : %s
				status_code  : %s
				running_time : %s
				log : %s
				''' %(taskname,status_code, running_time,log)
			temp_log.write(data)
			temp_log.close()
		return True

	def emailInfraTeam(self,emails,subject,message):
		command = 'echo \'%r\' | mail -s \'%s\' %r' %(message,subject,emails)
		process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
		out, err = process.communicate()
		if err:
			logger.error('failed to send email %r',err)
			return False
		else:
			return not int(process.returncode)

	def hostsOfProject(self,project):
		db_projects = self.mongoConn('projects')
		hosts = db_projects.find_one({"name" : project},{"hosts" : 1})
		if not hosts : return 'no project named %r' %project
		list_hosts = {}
		i=0
		for host in hosts['hosts']:
			list_hosts[i]= host.encode('utf8')
			i+= 1
		return dumps(list_hosts)

	def addHost(self,project,ipaddr,port):
		db_projects = self.mongoConn('projects')
		hosts = db_projects.find_one({"name" : project},{"hosts" : 1})
		list_hosts = hosts['hosts']
		list_hosts.append("%s:%d" %(ipaddr,int(port)))
		hosts = db_projects.update_one({"name" : project},{"$set" : {"hosts" : list_hosts}})
		if hosts.modified_count == 1 : return True
		else : return False

	def createCrontab(self,project,manager_url,enabled):
		db_crons = self.mongoConn('crons')
		crons= db_crons.find({'project' : project, 'active' : True },{'time' : 1, 'command' : 1, 'name' : 1})
		fname= '%s/crons/%s.cron.%d' %(here,project,int(time.time()))
		if not os.path.isdir('crons') : os.mkdir('crons')
		with open(fname,'w') as file:
			file.write('SHELL=/bin/bash \n\n')
			for doc in crons:
				flog = '/tmp/%s.cron.log' %doc['name']
				comment = '' if (enabled) else '#'
				line = '''%s%s\t TIME=$(date '+\%%s'); curl -s "%s/started?taskname=%s&time=$TIME" &>> /dev/null;{ time %s; } &> %s;curl -s -XPOST %s/finished -F "log=@%s" -F "status=$?" -F "task=%s" -F "start_time=$TIME" &>> /dev/null \n''' %(comment,doc['time'],manager_url,doc['name'],doc['command'],flog,manager_url,flog,doc['name'])
				file.write(line)
			file.close()
		return fname

	def broadcastCronJob(self,host,port,user,filename,adminuser=config.get('manager','admin')):
		if not self.checkVaildIP(ipaddr=host): return False
		ssh = self.sshConnect(str(host),int(port))
		dest = '/home/%s/crontab' %adminuser
		command = '/usr/bin/sudo /usr/bin/crontab -u %s %s' %(user,dest)
		try:
			sftp = ssh.open_sftp()
			sftp.put(filename,dest)
			stdin, stdout, stderr = ssh.exec_command(command,get_pty=True)
			if not stderr.readlines() : return True
			else :
				logger.error('error in running ssh.exec_command : %r',stderr.readlines())
				return False
		except Exception as e:
			logger.error('exception while trying to open_sftp or exec_command : %r',e)
			return False
