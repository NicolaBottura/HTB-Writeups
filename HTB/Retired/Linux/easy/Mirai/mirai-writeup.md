# Mirai - Linux, easy (10.10.10.48)

### Nmap scan:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 6.7p1 Debian 5+deb8u3 (protocol 2.0)
| ssh-hostkey: 
|   1024 aa:ef:5c:e0:8e:86:97:82:47:ff:4a:e5:40:18:90:c5 (DSA)
|   2048 e8:c1:9d:c5:43:ab:fe:61:23:3b:d7:e4:af:9b:74:18 (RSA)
|   256 b6:a0:78:38:d0:c8:10:94:8b:44:b2:ea:a0:17:42:2b (ECDSA)
|_  256 4d:68:40:f7:20:c4:e5:52:80:7a:44:38:b8:a2:a7:52 (ED25519)
53/tcp open  domain  dnsmasq 2.76
| dns-nsid: 
|_  bind.version: dnsmasq-2.76
80/tcp open  http    lighttpd 1.4.35
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
|_http-server-header: lighttpd/1.4.35
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

### Enumeration
The website at port 80 returns an empty page, so I tried a gobuster scan and found two pages, **/admin** and **/swfobject.js**.
The /admin page returns a **Pi-hole Admin Console** page, and also `curl http://10.10.10.48/swfobject.js` returns **var x = "Pi-hole: A black hole for Internet advertisements."**, which means that we are dealing with Pi-hole.

**Pi-hole** is a Linux application used to block AD and to track users on the internet a network level.
Designed to be used in a local network, it works as a DNS sinkhole (a DNS sever that returns a false result when a DNS name is requested) and optionally as a DHCP server.
Usually used in devices like Raspberry Pi.

Version: Pi-hole Version v3.1.4 Web Interface Version v3.1 FTL Version v2.10

For admin page, we do not have credentials, so there's not much we can do.
Checking all the open ports, there is also a website hosting plex, but also there we have not much to do.

### Mirai
Mirai is a real malware that formed a huge network of bots, and is used to conduct distributed denial of service (DDOS) attacks. 
The compromised devices are largely made up of internet of things (IoT) devices running embedded processors like ARM and MIPS. 
The most famous Mirai attack was in October 2016, when the botnet degraded the service of Dyn, a DNS service provider, 
which resulted in making major sites across the internet (including NetFlix, Twitter, and GitHub) inaccessible. 
The sites were still up, but without DNS, no one could access them.

Mirai’s go-to attack was to brute force common default passwords. In fact, mirai-botnet.txt was added to SecLists in November 2017.

### Obtaining user Pi
Default credentials for a Raspberry Pi device are **user: pi** and **password: raspberry**.
Trying ssh with these credentials works, and we get a shell as user Pi.

In ~/Desktop we can find the user flag!

### From Pi to Root
Just execute `sudo -l`:
```
User pi may run the following commands on localhost:
    (ALL : ALL) ALL
    (ALL) NOPASSWD: ALL
```

So, user Pi can run anything as user root.
Just `sudo /bin/bash` to get a shell as user root.

Entering in folder **/root**, we can see that the content of the root.txt file is:
```
root@raspberrypi:~# cat root.txt 
I lost my original root.txt! I think I may have a backup on my USB stick...
```

So, we need to find it.
The usb is mounted in **/media/usbstick**, and its device is **/dev/sdb**.
We can notice this executing `mount`:
```
root@raspberrypi:~# mount
...[snip]...
/dev/sdb on /media/usbstick type ext4 (ro,nosuid,nodev,noexec,relatime,data=ordered)
tmpfs on /run/user/999 type tmpfs ...[snip]...
```

or using `lsblk`:
```
root@raspberrypi:/# lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda      8:0    0   10G  0 disk 
├─sda1   8:1    0  1.3G  0 part /lib/live/mount/persistence/sda1
└─sda2   8:2    0  8.7G  0 part /lib/live/mount/persistence/sda2
**sdb      8:16   0   10M  0 disk /media/usbstick**
sr0     11:0    1 1024M  0 rom  
loop0    7:0    0  1.2G  1 loop /lib/live/mount/rootfs/filesystem.squashfs
```

In folder /media/usbstick we can find a file called **damnit.txt** with the following content:
```
Damnit! Sorry man I accidentally deleted your files off the USB stick. Do you know if there is any way to get them back? -James
```

When a file gets deleted, the structure of the filesystem removes the metadata about that file.
That includes the timestamps, filename, and a pointer to where the raw file is on disk. 
The delete operation does not go to that point on the disk and do anything to clean up the data, like write all nulls over it.
That means there’s a good chance that the contents of root.txt are still there, even if the filesystem no longer knows of a file by that name.

The raw USB device is /dev/sdb, and I can interact with that just like any other file.

Just run `strings /dev/sdb` to see the ascii strings and get the flag (it is pretty clear which is the flag).
