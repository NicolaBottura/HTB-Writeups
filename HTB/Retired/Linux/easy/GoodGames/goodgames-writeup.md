# GoodGames - Linux, easy (10.10.11.130)

### Nmap scan:
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.51
|_http-title: GoodGames | Community and Store
|_http-server-header: Werkzeug/2.0.2 Python/3.9.2
```
Notice that the server is using Python!

### Obtaining User
Most the links on the page just point back to the page itself, but there are links to “Blog” (/blog) and “Store” (/coming-soon). 
In the footer there’s a reference to “GoodGames.HTB”, that I added in my hosts file.

In the top right corner of the website there is a little user icon that by clicking it, it pops a sign-in box that contains also a link to a sign-up page.
These forms are vulnerable to **SQLi**, we can see this by trying to log in with credentials **admin** and password **'OR 1=1-- -;**.
