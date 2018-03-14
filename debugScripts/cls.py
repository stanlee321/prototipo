# cleanfolders.py

"""
Script to clean *.jpg files  in a directory and sub folders.
"""

import os
import glob
import shutil

files = glob.glob('casosReportados/*')




trash = []
for folder in files:
	if folder[-2:] == '0i':
		print(folder)
		trash.append(folder)
	else:
		pass


print('TRASH IS SIZE : ', len(trash))

for i,c in enumerate(trash):
	print(i,':', c)
	print('{}/{}'.format(i+1, len(trash)))
	shutil.rmtree(c)
	print('DONE!')