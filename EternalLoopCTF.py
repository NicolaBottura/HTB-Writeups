#HTB/Challenges/Misc/Eternal Loop

import zipfile
import subprocess
import os

def extractor(filename):
	zip_file = zipfile.ZipFile(filename, 'r')
	file_info = zip_file.infolist()
	filename = file_info[0].filename # filename the variable that contains the file name
									 # of the zip in the infolist structure
	pwd = filename.split(".")[0]
	zip_file.extractall(pwd=str.encode(pwd))

	return filename

def main():
	path = "/home/kali/Downloads/"
	first_zip = "37366.zip"
	name = path + first_zip
	
	while True:
		name = extractor(name)
		print(name)
		if name == "6969.zip":
			break
		else:
			os.remove(name)

if __name__ == '__main__':
	main()
