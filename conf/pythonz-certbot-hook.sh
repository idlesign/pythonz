#! /bin/sh
chown -R pythonz:pythonz /etc/letsencrypt/archive/pythonz.net/.*
pythonz uwsgi_reload
