# Blocky - Linux, easy (10.10.10.37)

### Enumeration
```
PORT     STATE  SERVICE VERSION
21/tcp   open   ftp     ProFTPD 1.3.5a
22/tcp   open   ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 d6:2b:99:b4:d5:e7:53:ce:2b:fc:b5:d7:9d:79:fb:a2 (RSA)
|   256 5d:7f:38:95:70:c9:be:ac:67:a0:1e:86:e7:97:84:03 (ECDSA)
|_  256 09:d5:c2:04:95:1a:90:ef:87:56:25:97:df:83:70:67 (ED25519)
80/tcp   open   http    Apache httpd 2.4.18
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Did not follow redirect to http://blocky.htb
8192/tcp closed sophos
```

### Obtaining User
FTP is a dead end, so check the website and run gobuster to see how it looks like `gobuster dir -u http://blocky.htb/ -w <wordlist>`.
Different interesting pages are found, for example a WordPress and phpMyAdmin login page. But the most interesting is the directory **/plugins**.
Here we can find two .jar files, and if e download and unzip them, we can notice in the first one (BlockyCore.jar) some credentials:
**root:8YsqfCTnvxAUeduzjNSXe22**.

Unfortunately, these are not useful for what concern the two login pages found, neither for an ssh login!
But looking at the posts on the website, we can notice that there is a single post made by a user called **Notch**.
If we ssh as this user with the obtained password we can get a shell as user Notch and the first flag!

### From User to Root
Pretty standard vulnerability, `sudo -l` reveals that we can run amnything with sudo, so just execute `sudo /bin/bash` to get a shell as user root and then its flag.
