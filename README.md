# Diglett
A cron management system that manage all your cronjobs over multiple servers without modifying crontab. Handles locking, logging, error emails, and more.


Installation
--------------------
This guide is orianted to CentOS/Fedora Systems.

- Install Nginx as a webserver and Mongodb as DB.
```
$ sudo dnf update -y
$ sudo dnf install -y nginx git python-pip mongodb-server mongodb
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
$ sudo pip install pymongo==3.0.0
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
