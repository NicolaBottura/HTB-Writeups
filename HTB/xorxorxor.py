#!/usr/bin/env python3
from binascii import unhexlify

'''
	HTB/Challenges/Crypto/xorxorxor

	We know that the flag is encoded by XORing it with a secret key.
				+--------------------------------------+
				|									   |
				|   cipher = plain_text(flag) ^ key    |
				|									   |
				+--------------------------------------+
	To find the key I just need to XOR out from the cipher the first part of the
	plain text that I know, which is "HTB{".
'''


def xorxorxor(strstr, str):
	if len(strstr) != len(str):
		raise Exception("Wrong cipher/key size")

	output = b""
	for a,b in zip(strstr, str):	# Pair the cipher and the key and XOR them char by char
		output += bytes([a ^ b])

	return output


cipher = "134af6e1297bc4a96f6a87fe046684e8047084ee046d84c5282dd7ef292dc9"
decoded = unhexlify(cipher)

key = xorxorxor(decoded[:4], "HTB{".encode()) # Send the first 4 characters and "HTB{" to find the key

while len(key) < len(decoded):	# Generate the full key, which is just the one found for "HTB{" repeated
	key += key					# until the length is the same as the cipher

key = key[:-1]	# Adjust the key

flag = xorxorxor(decoded, key)
print("[*] FLAG: {}".format(flag))
