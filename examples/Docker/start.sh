#! /bin/bash

cd /app/

#Create main-local.php and params-local.php 
CONFD_OPTIONS=${CONFD_OPTIONS:-"-onetime -backend=env"}
/usr/local/bin/confd -log-level=debug $CONFD_OPTIONS -confdir=$PWD/confd 

cd /app/code
mkdir -p /app/apache/lock /app/apache/log /app/apache/run

export APACHE_LOCK_DIR=/app/apache/lock/      
export APACHE_LOG_DIR=/app/apache/log/
export APACHE_PID_FILE=/app/apache/run/apache2.pid
export APACHE_RUN_GROUP=app
export APACHE_RUN_USER=app

#Select the mode 
command="$1"
shift
case "$command" in
uwsgi)
  sed -i 's/uid = cronman/uid = app/g' uwsgi.ini
  sed -i 's/gid = cronman/gid = app/g' uwsgi.ini
  exec uwsgi --http-socket 0.0.0.0:3030 ./uwsgi.ini
  ;;
apache)
  exec apache2 -DFOREGROUND
  ;;
*)
  exec bash
esac

