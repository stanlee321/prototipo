import os
import logging
import datetime

class MiReporte():
	"""
	Crea un archivo de logging de nombre especificado con por defecto con un nivel de logging.
	Al cambiar el reporte este se traspasa a una carpeta dentro del directorio de trabajo con el mismo nombre del directorio
	"""
	level = logging.INFO
	def __init__(self, levelLogging, nombre = __name__,directorio=os.getenv('HOME')+'/'+datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'):
		try:
			levelLogging
		except:
			levelLogging = level
		else:
			MiReporte.level = levelLogging
		self.logger = logging.getLogger(nombre)
		self.logger.setLevel(levelLogging)
		self.formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s\t\t%(message)s')
		# Diarios:
		self.directorioDeTrabajo = ''
		self.fileHandlerActual = ''
		self.initDirectory(directorio)

		self.stream_handler = logging.StreamHandler()

		self.logger.addHandler(self.fileHandlerActual)
		self.logger.addHandler(self.stream_handler)
		self.info('Started Reporte with level '+str(MiReporte.level))
		
	def moverRegistroACarpeta(self,nombreDeCarpeta = datetime.datetime.now().strftime('%m-%d_%H:%M')):
		self.logger.removeHandler(self.fileHandlerActual)
		self.fileHandlerActual = logging.FileHandler(self.directorioDeTrabajo+'/'+nombreDeCarpeta+'/LOG_'+directorio[-18:-8]+'.log')
		self.fileHandlerActual.setFormatter(self.formatter)
		self.logger.addHandler(self.fileHandlerActual)

	def initDirectory(self,directorio):
		self.directorioDeTrabajo = directorio
		if not os.path.exists(self.directorioDeTrabajo):
			os.makedirs(self.directorioDeTrabajo)
		self.fileHandlerActual = logging.FileHandler(self.directorioDeTrabajo+'/LOG_'+directorio[-18:-8]+'.log')
		self.fileHandlerActual.setFormatter(self.formatter)
		self.stream_handler = logging.StreamHandler()
		self.logger.addHandler(self.fileHandlerActual)

	def setDirectory(self,directorio):
		self.logger.removeHandler(self.fileHandlerActual)
		self.initDirectory(directorio)
		
	def setLevel(self):
		MiReporte.level = 'info'


	def trace(self,mensaje):
		self.logger.trace(mensaje)

	def debug(self,mensaje):
		self.logger.debug(mensaje)

	def info(self,mensaje):
		self.logger.info(mensaje)

	def warning(self,mensaje):
		self.logger.warning(mensaje)

	def error(self,mensaje):
		self.logger.error(mensaje)

	def critical(self,mensaje):
		self.logger.critical(mensaje)