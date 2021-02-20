'''
HTB/Challenges/Misc/Eternal Loop

After unzipping the file downloaded from HTB you obtain another zip, called 37366.zip.
The password used to unzip this file is the name of the file obtained after unzipping this, which is another zip file.
Keep unzipping the files until you obtain zip 6969.zip which contains a file called DoNotTouch.
The password to unzip 6969.zip can be found using fcrackzip and the flag using Strings on the file obtained.
'''

import zipfile
import os

def extractor(filename):
	zip_file = zipfile.ZipFile(filename)
	file_info = zip_file.infolist()
	filename = file_info[0].filename # filename the variable that contains the file name
									 # of the zip in the infolist structure
	pwd = filename.split(".")[0]
	zip_file.extractall(pwd=str.encode(pwd))

	return filename

def main():
	first_zip = "37366.zip"
	name = first_zip
	
	while True:
		name = extractor(name)
		print(name)
		if name == "6969.zip":
			break

if __name__ == '__main__':
	main()
