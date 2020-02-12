#! /bin/sh
chown -R pythonz:pythonz /etc/letsencrypt/archive/pythonz.net/.*
systemctl restart pythonz.service
