'''
HTB/Challenges/Misc/Deterministic

There is a locked door in front of us that can only be opened with the secret passphrase. 
There are no keys anywhere in the room, only this .txt. There is also a writing on the wall.. "State 0: 69420, State N: 999, flag ends at state N, key 
length: one".. Can you figure it out and open the door? 
'''
first_state = 69420
last_state = 999

f_in = open("deterministic.txt", "r")

next = first_state
dic = {}

with open("deterministic.txt") as f_in:
	for _ in range(2):
		f_in.next()

	for line in f_in:
		values = line.strip().split(" ") # split the line in [state, value, next_state]

		# dic[state] = (value, next_state)
		try:
			dic[int(values[0])] = (int(values[1]), int(values[2])) # with int() ignore the ascii values
		except:
			pass

result = []

while next != last_state:
	temp = dic[next]
	result.append(temp[0])
	next = temp[1]

print(' '.join(str(i) for i in result))

'''
Here you find a list of values which are the middle part of the lines of the deterministic.txt file given

Looking at the file, it says that the characters of the password are XORED with a key, so, in order to
find the key, we have to XOR brute-force the value obtained after executing this script.
Use CyberChef with as recipe:
	1. From Decimal
	2. XOR bruteforce(lenght 1 as said in htb)
Checking the result, we can see at key 69 the following ascii characters:

Key = 69: You managed to pass through all the correct states of the automata and reach the final state. Many p

so the key is actually 69!
Now, again on CyberChef put as recipe simple XOR with key 69 and get the flag!
'''
