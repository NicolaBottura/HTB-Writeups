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

Note that if we do not append `-- -` in the country, we will receive the following error `Uncaught Error: Call to a member function fetch_assoc() on bool in /var/www/html/account.php:33`.

To test this vulnerability in a easier way we can open two Repeater tabs in Burp, one with the POST request where we can modify username and country, and one with the GET request to /account.php where we can inspect the result.

### SQLi UNION attack
When an application is vulnerable to SQL injection and the results of the query are returned within the application's responses, 
the UNION keyword can be used to retrieve data from other tables within the database. This results in an SQL injection UNION attack.
The UNION operator is used to combine the result-set of two or more SELECT statements:
1. Every SELECT statement within UNION must have the same number of columns
2. The columns must also have similar data types
3. The columns in every SELECT statement must also be in the same order



