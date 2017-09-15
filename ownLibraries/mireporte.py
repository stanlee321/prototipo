import os
import logging
import datetime

class MiReporte():
	"""
	Crea un archivo de logging de nombre especificado con por defecto con un nivel de logging.
	Al cambiar el reporte este se traspasa a una carpeta dentro del directorio de trabajo con el mismo nombre del directorio
	"""
	def __init__(self, levelLogging=logging.INFO, nombre = __name__, nombreDeArchivoSinExtension = datetime.datetime.now().strftime('%m-%d_%H:%M')):
		self.directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo11/casosDebug'
		if not os.path.exists(self.directorioDeTrabajo):
			os.makedirs(self.directorioDeTrabajo)
		self.logger = logging.getLogger(nombre)
		self.logger.setLevel(levelLogging)
		self.formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s\t\t%(message)s')

		self.file_handler_global = logging.FileHandler(self.directorioDeTrabajo+'/LOG_'+nombreDeArchivoSinExtension+'.log')
		self.file_handler_global.setFormatter(self.formatter)

		self.stream_handler = logging.StreamHandler()

		self.logger.addHandler(self.file_handler_global)
		self.logger.addHandler(self.stream_handler)
		
		self.file_handler_actual = logging.FileHandler(self.directorioDeTrabajo+'/LOG_'+nombreDeArchivoSinExtension+'.log')
		self.file_handler_actual.setFormatter(self.formatter)

	def moverRegistroACarpeta(self,nombreDeCarpeta = datetime.datetime.now().strftime('%m-%d_%H:%M')):
		self.logger.removeHandler(self.file_handler_global)
		self.file_handler_actual = logging.FileHandler(self.directorioDeTrabajo+'/'+nombreDeCarpeta+'/LOG_'+nombreDeCarpeta+'.log')
		self.file_handler_actual.setFormatter(self.formatter)
		#self.stream_handler = logging.StreamHandler()		# Revisar el efecto de StreamHandler
		self.logger.addHandler(self.file_handler_actual)

	def retornarACarpetaPrincipal(self):
		self.logger.removeHandler(self.file_handler_actual)
		self.logger.addHandler(self.file_handler_global)

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