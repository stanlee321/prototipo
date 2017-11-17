# cleanfolders.py

"""
Script to clean *.jpg files  in a directory and sub folders.
"""

import os
import glob
import shutil

files = glob.glob('casosReportados/*')


videos = []
trash = []

for folder in files:
	trash.append(folder)
	for im in glob.glob(folder+'/*'):
		if '.avi' in im:
			videos.append(folder)
		else:
			pass
clean = list(set(trash)-set(videos))

print('FILES TO DELET: ', len(clean))
print('USEFULL FILES: ', len(videos))
for i,c in enumerate(clean):
	print('{}/{}'.format(i, len(clean)))
	shutil.rmtree(c)
	print('DONE!')
