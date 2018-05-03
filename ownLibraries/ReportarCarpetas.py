import pandas as pd


class ReportarCarpetas():
	"""
	Method that keep track of files in folders sync

	"""

	def __init__(self, path_to_folder = ''):
		self.path_to_folder = path_to_folder

	def reporteAutomatico(self):

		# tCreacion = Datetime.now()							# obtain acutal time when you access to this class

		# carpetas = checkDBforFolders							# return list of carpetas dict where status is False
		# for folder in carpetas:
			# tCreacion = folder['tCreacion']					# Obtain the tCreation from actual folder
			## IF tCreacion - tActual < 4 min:					# if time difference is less of 4 minutes
				# videos, images = getAssetsInFolder(folder) 	# Check folder for video inside
				# if  (len(videos) > 0) and (len(images) > 0)   # if exist videos and images
					# listLike: cropedImages = cropImages(images )			
					# for cropped in croopedImages:
						# respuesta, placa = sendToAWS(crooped, video)
						# if respuesta is OK:
							# change status for carpetas to True #
							#break

				# else:
					# rm-rf (folder)

	def checkDBforFolders(self, path_to_DB):
		## input: DB 
		# TODO revisar base de datos por state = False

		## Output: list of folders with False status.