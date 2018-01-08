#  folders_cleaner.py


import os
import glob
import shutil


class FoldersCleaner():

	"""
		Class to clean single folders in a absolute folder
		Expected use:
		input: String ; path_to_clean  = './2012-05-01'

		output: Print Statement with the signal of job Done!
	"""
	def __init__(self):
		# Not need to acces to atributes
		self.folders_to_clean = []
		self.total_folders = []
	def get_files(self, path_to_clean):
		"""
			Get a list of the clean folders (usefull)
			, folders with jpg's and avi in folder
		"""
		print('Path to clean is: ', path_to_clean)	
		
		# List of folders in the <path_to_clean> input
		files = glob.glob(path_to_clean)
		for folder in files:
			# Get the whole names in the directory
			self.total_folders.append(folder)

			# Count for the elements in this folder
			try:
				files_in = os.listdir(folder) # folder is your directory path to look
				number_files = len(files_in)
				# If number of files in dir is <4 , append to the list of folders_to_clean
				if number_files < 4:
					print('Number of files in this folder {} : '. format(folder), number_files)
					self.folders_to_clean.append(folder)
				else:
					pass
			except Exception as e:
				print('U are a log or something else:', e)
		return  self.folders_to_clean

	def delete_folders(self, path_to_clean):

		# Get the  folders to delete
		clean = self.get_files(path_to_clean)
		usefull_folders = list(set(self.total_folders) - set(clean))
		
		print('TOTAL FOLDERS:', len(self.total_folders))
		print('FOLDERS TO DELET: ', len(clean))
		print('USEFULL FOLDERS: ', len(usefull_folders ))
		
		for i,c in enumerate(clean):
			print('{}/{}'.format(i+1, len(clean)))
			try:
				print('removing ...', c)
				shutil.rmtree(c)
			except:
				print('this is a log or something else passing...')
				print(c)
				#os.remove(c)
			print('DONE!')


if __name__ == '__main__':
	
	import argparse
	import datetime

	parser = argparse.ArgumentParser(description='Process SubFolders in a Root folder')

	parser.add_argument('-folder', '--cleanFolder',
	                    default = None, type=str, help="format is Year-month-day")

	args = parser.parse_args()


	# If -folder flag is set, path_to_clean = <-folder flab>
	if args.cleanFolder != None:
		home_dir = os.getenv('HOME')
		today_date = datetime.datetime.now().strftime('%Y-%m-%d')
		path_to_clean = home_dir + '/' + args.cleanFolder + '/*'

	# Else it will search for the todays report and set path_to_clean to actual day
	else:
		home_dir = os.getenv('HOME')
		today_date = datetime.datetime.now().strftime('%Y-%m-%d')
		path_to_clean =  home_dir + '/' + today_date + '_reporte' + '/*'

	# Create Object

	limpiador  = FoldersCleaner()
	limpiador.delete_folders(path_to_clean)

