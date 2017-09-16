import time
import RPi.GPIO as GPIO

class IRSwitch():
	"""
	Controla un Filtro IR de tipo Switch empleando los pines 2, 3 y 4 para 
	"""
	def __init__(self,tiempoPulsoMiliSegundos = 10):
		self.tiempoParaPulso = tiempoPulsoMiliSegundos/1000
		self.tiempoDeInercia = self.tiempoParaPulso/10
		self.forwardPin = 2
		self.backwardPin = 3
		self.enable = 4
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(self.enable,GPIO.OUT)
		GPIO.output(self.enable,GPIO.LOW)
		GPIO.setup(self.forwardPin,GPIO.OUT)
		GPIO.setup(self.backwardPin,GPIO.OUT)
		self.ultimoEstado = 'Inicializado'
		
	def colocarFiltroIR(self):
		"""
		Genera la salida BCMGPIO02 -> HIGH (pin fisico 3)
		Genera la salida BCMGPIO03 -> LOW (pin fisico 5)
		Genera la salida BCMGPIO04 -> pulse high (pin fisico 7)
		"""
		GPIO.output(self.forwardPin,GPIO.HIGH)
		GPIO.output(self.backwardPin,GPIO.LOW)
		time.sleep(self.tiempoDeInercia)
		GPIO.output(self.enable,GPIO.HIGH)
		time.sleep(self.tiempoParaPulso)
		GPIO.output(self.enable,GPIO.LOW)
		self.ultimoEstado = 'Filtro Activo'

	def quitarFiltroIR(self):
		"""
		Genera la salida BCMGPIO02 -> LOW (pin fisico 3)
		Genera la salida BCMGPIO03 -> HIGH (pin fisico 5)
		Genera la salida BCMGPIO04 -> pulse high (pin fisico 7)
		"""
		GPIO.output(self.forwardPin,GPIO.LOW)
		GPIO.output(self.backwardPin,GPIO.HIGH)
		time.sleep(self.tiempoDeInercia)
		GPIO.output(self.enable,GPIO.HIGH)
		time.sleep(self.tiempoParaPulso)
		GPIO.output(self.enable,GPIO.LOW)
		self.ultimoEstado = 'Filtro Desactivado'

	def obtenerUltimoEstado(self):
		return self.ultimoEstado

if __name__ == '__main__':
	miFiltroPrueba = IRSwitch()
	counter = 0
	while (counter<10):
		miFiltroPrueba.colocarFiltroIR()
		time.sleep(1)
		miFiltroPrueba.quitarFiltroIR()
		time.sleep(2)
		counter+=1
