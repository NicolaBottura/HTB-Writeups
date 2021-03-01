#!/usr/bin/env python3
from Crypto.PublicKey import RSA
import math
from binascii import unhexlify
import base64
import re

'''
	HTB/Challenges/Crypto/TwoForOne

	First finds n, e from the RSA key and check them.
	We can notice that the n is the same(modulus).
	The same message is encrypted with two different keys, where the modulus is the same making 
	it possible to decrypt one and find the flag.

	c_1 = m^e_1 mod n
	c_2 = m^e_2 mod n

	If gcd(e_1, e_2) = 1 -> exists a, b s.t. e_1*a + e_2*b = 1;

	i = c_2^(-1) mod n
	flag = (c_1^a mod n) * (i^(-b) mod n) mod n

	c_1^a * c_2^b = (m^e_1)^a * (m^e_2)^b = m^(e_1 * a + e_2 * b) =
	we know that the exponent is = 1 -> m^1 = m

	Better explanation:
		https://crypto.stackexchange.com/questions/1614/rsa-cracking-the-same-message-is-sent-to-two-different-people-problem

'''

# Extended Euclidean Algorithm to find a,b and gcd
def extended_euclidean(a, b):
	if a == 0:
		return b, 0, 1

	gcd, x1, y1 = extended_euclidean(b%a, a)

	x = y1 - (b//a) * x1
	y = x1

	return gcd, x, y


f1 = open("key1.pem", "r")
f2 = open("key2.pem", "r")
f3 = open("message1", "rb")
f4 = open("message2", "rb")

key1 = RSA.importKey(f1.read())
key2 = RSA.importKey(f2.read())

N = key1.n # They have the same N
e1 = key1.e
e2 = key2.e

msg1 = f3.read()
temp1 = base64.b64decode(msg1)
c1 = int.from_bytes(temp1, byteorder='big')
msg2 = f4.read()
temp2 = base64.b64decode(msg2)
c2 = int.from_bytes(temp2, byteorder='big')

if math.gcd(e1, e2) != 1:
	raise Exception("Gcd between e_1 and e_2 not equal to 1")

g, a, b = extended_euclidean(e1, e2)

i = pow(c2, -1,  N)

flag = (pow(c1, int(a), N) * pow(i, -int(b), N)) % N
print("[*] FLAG: {}".format(flag.to_bytes(27, 'big')))
