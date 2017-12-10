# cleanfolders.py

"""
Script to clean  sub folder that just has  *.jpg files in folder input.
Expected input /home/user/today_date/< folders to clean >

Use as :

python3 cleanfolders.py -folder <Y-m-d>
example : python3 cleanfolders.py -folder 2012-05-01

or leave black the -folder paramter to clean the folder with
the time of today_date

example : python3 cleanfolders.py

"""

import os
import glob
import shutil
import datetime
import argparse


parser = argparse.ArgumentParser(description='Process SubFolders in a Root folder')

parser.add_argument('-folder', '--cleanFolder',
                    default = None, type=str, help="format is Year-month-day")

args = parser.parse_args()


if args.cleanFolder != None:
	home_dir = os.getenv('HOME')
	today_date = datetime.datetime.now().strftime('%Y-%m-%d')
	path_to_clean = home_dir + '/' + args.cleanFolder + '/*'

else:
	home_dir = os.getenv('HOME')
	today_date = datetime.datetime.now().strftime('%Y-%m-%d')
	path_to_clean =  home_dir + '/' + today_date+ '/*'

print('Path to clean is: ', path_to_clean)

files = glob.glob(path_to_clean)

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

print('FOLDERS TO DELET: ', len(clean))
print('USEFULL FOLDERS: ', len(videos))
for i,c in enumerate(clean):
	print('{}/{}'.format(i+1, len(clean)))
	try:
		print('removing ...', c)
		shutil.rmtree(c)
	except:
		print('this is a log')
		print(c)
		#os.remove(c)
	print('DONE!')
