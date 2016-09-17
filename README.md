# Diglett
A cron management system that manage all your cronjobs over multiple servers without modifying crontab. Handles locking, logging, and more.

![screen shot 2016-06-15 at 10 38 34 pm](https://cloud.githubusercontent.com/assets/4533327/16156450/fd6a956a-34bc-11e6-9cb5-15c9a236772e.png)

You can choose any project you have and see all crons with time of execution and last status of every cron. In addition to manage these crons via UI. 

<img width="981" alt="screen shot 2016-06-17 at 6 58 50 pm" src="https://cloud.githubusercontent.com/assets/4533327/16156559/8e663f56-34bd-11e6-99f1-48b297cd24f3.png">

You can broadcast your task to all your servers. 

![screen shot 2016-06-15 at 10 39 21 pm](https://cloud.githubusercontent.com/assets/4533327/16156543/7c52f458-34bd-11e6-8de1-897b5b236d1f.png)

Read More 
--------------------
On Opensooq Engineering Blog : http://engineering.opensooq.com/manage-cronjobs-over-multiple-servers/

Alerting
--------------------
Diglett uses two methods of alerting for now, Email and Push Notifications.

- Emails

Mainly depends on mail-utlis on linux system, therefore it should be installed on your Diglett Server.

- Push Notification

For now, Diglett is using only one push notification backend called SimplePush. To use it, you should install the application on your Android and insert the key in config.ini file.

Also, you can disable the push notification feature from the same file.

Installation
--------------------
This guide is orianted to CentOS/Fedora Systems.

- Install Nginx as a webserver and Mongodb as DB.
```
$ sudo yum update -y
$ sudo yum install -y nginx git mongodb-server mongodb
```

- Clone diglett
```
$ git clone https://github.com/OpenSooq/Diglett.git ~/diglett
```
- Copy systemd service file and nginx configuration file.
```
$ sudo cp ~/diglett/examples/diglett@.service /etc/systemd/system/
$ sudo cp ~/diglett/examples/nginx.conf /etc/nginx/conf.d/diglett.conf
```
- Install required packages
```
$ cat ~/diglett/requirements.txt | grep -v ^# | xargs sudo dnf install -y
$ sudo yum install python-pip && sudo pip install pymongo==3.0.0
```

- Change the UID and GID in uwsgi.ini and in diglett@.service :
```
$ vim ~/diglett/uwsgi.ini and change the following :
...
uid = username
gid = username
...
$ sudo vim /etc/systemd/system/diglett@.service
...
User= username
Group= username
...
```
- Change the admin user to a user that has root/sudo access to all servers.
```
$ vim  ~/diglett/config.ini
...
[manager]
admin= username
manager_url= http://PROJECT_IP
...
```
- Initialize the database
```
$ mongo diglett < examples/initialize_db.js
```
- Start and enable services :
```
$ sudo systemctl enable nginx && sudo systemctl start nginx
$ sudo systemctl enable mongod && sudo systemctl start mongod
$ sudo systemctl start diglett@3030
```
