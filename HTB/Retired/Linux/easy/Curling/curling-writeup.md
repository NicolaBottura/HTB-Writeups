# Curling - Linux, easy (10.10.10.150)

### Nmap scan:
```
PORT   STATE SERVICE
22/tcp open  ssh
| ssh-hostkey: 
|   2048 8a:d1:69:b4:90:20:3e:a7:b6:54:01:eb:68:30:3a:ca (RSA)
|   256 9f:0b:c2:b2:0b:ad:8f:a1:4e:0b:f6:33:79:ef:fb:43 (ECDSA)
|_  256 c1:2a:35:44:30:0c:5b:56:6a:3f:a5:cc:64:66:d9:a9 (ED25519)
80/tcp open  http
|_http-generator: Joomla! - Open Source Content Management
|_http-title: Home
```

Here we can check the version of Joomla!: http://10.10.10.150/administrator/manifests/files/joomla.xml
```
<extension version="3.6" type="file" method="upgrade">
<name>files_joomla</name>
<author>Joomla! Project</author>
<authorEmail>admin@joomla.org</authorEmail>
<authorUrl>www.joomla.org</authorUrl>
<copyright>(C) 2005 - 2018 Open Source Matters. All rights reserved</copyright>
<license>GNU General Public License version 2 or later; see LICENSE.txt</license>
**<version>3.8.8</version>**
<creationDate>May 2018</creationDate>
<description>FILES_JOOMLA_XML_DESCRIPTION</description>
<scriptfile>administrator/components/com_admin/script.php</scriptfile>
```



```
echo "Q3VybGluZzIwMTgh" | base64 -d
Curling2018!
```