from ConfigParser import SafeConfigParser
from common import DiglettCommon
import logging
import time
import os 

# Logger
logger = logging.getLogger(__name__)

# Config Parsing
config = SafeConfigParser()
config.read('config.ini')

# Get common functions
common = DiglettCommon()

def get_all_projects():
    db_projects = common.mongo_connect('projects')
    return db_projects.find({},{"name" : 1, '_id' : False})

def get_active_host(project):
    db_projects = common.mongo_connect('projects')
    db_projects.find_one({"name" : project},{"active_host" : 1, '_id' : False})

def host_is_up(ip):
    return True if os.system("ping -c 1 " + ip) is 0 else False

def activate_host(host,project):
    db_projects = common.mongo_connect('projects')
	project_info = db_projects.find_one({'name' : project},{'hosts' : 1,'active_host' : 1, 'user' : 1})
    update = db_projects.update_one({'name' : project},{'$set': { 'active_host' : host } })
	if update.modified_count == 1 :
	    logger.warning('number of modified projects while activating a host is not 1, \n the request : %r',request.body.read())
        exit(3)
    else :
        crontab = common.create_crontab(project=project,manager_url=config.get('manager','manager_url'),enabled=True)
		status = common.brodcast_crontab(host=host.split(':')[0],port=host.split(':')[1],user=project_info['user'],filename=crontab)
        if not status :
			message = '[ERROR] Broadcasting crontab to host=%s from project=%s failed.\n Sending email to infrateam.' %(ipaddr,project_name)
			common.notify_admin(subject='Diglett : Brodcasting Failed',message=message)

while True:
    for project in get_all_projects():
        hosts=common.hosts_of_project(project)
        active_host=get_active_host(project)
        if not host_is_up(active_host.split(':')[0]) : 
            for host in hosts:
                if host_is_up(host.split(':')[0]):
                    message='Project=%s Host=%s is down, WatchDog is trying to activate another host.' %(project,active_host)
                    common.notify_admin(subject='Diglett : Active Host is Down',message=message)
                    activate_host(host=host,project=project)
                    continue
    time.sleep(int(config.get('watchdog','interval')))
