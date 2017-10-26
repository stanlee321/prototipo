import os
import time
if os.uname()[1] == 'raspberrypi':
	import RPi.GPIO as GPIO

class IRSwitch():
	"""
	Controla un Filtro IR de tipo Switch empleando los pines 2, 3 y 4 para 
	Especificaciones:
		- Rated voltage: DC 3.3V~12V
		- DC resistance: 42ohm (at 20'C)
		- Action voltage: DC 3.3V~12V
		- Minimum pulse width: 0.05s
		- Working temperature range: -20'C~70'C
		- Working normal after place 48H under 70'C / 90% humidity 
		- Switch control time: 50~200ms
		- Switch time: >100,000 times 
		- Drop test from 6 sides, 70g pressure
		- Visual window size: 8mm (diameter)
	"""
	def __init__(self,tiempoPulsoMiliSegundos = 50):
		self.tiempoParaPulso = tiempoPulsoMiliSegundos/1000
		self.tiempoDeInercia = self.tiempoParaPulso/10
		self.forwardPin = 3
		self.backwardPin = 4
		self.enable = 2
		self.ultimoEstado = 'On debug'
		if os.uname()[1] == 'raspberrypi':
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
		if os.uname()[1] == 'raspberrypi':
			GPIO.output(self.forwardPin,GPIO.HIGH)
			GPIO.output(self.backwardPin,GPIO.LOW)
			time.sleep(self.tiempoDeInercia)
			GPIO.output(self.enable,GPIO.HIGH)
		time.sleep(self.tiempoParaPulso)
		if os.uname()[1] == 'raspberrypi':
			GPIO.output(self.enable,GPIO.LOW)
		self.ultimoEstado = 'Filtro Activado'

	def quitarFiltroIR(self):
		"""
		Genera la salida BCMGPIO02 -> LOW (pin fisico 3)
		Genera la salida BCMGPIO03 -> HIGH (pin fisico 5)
		Genera la salida BCMGPIO04 -> pulse high (pin fisico 7)
		"""
		if os.uname()[1] == 'raspberrypi':
			GPIO.output(self.forwardPin,GPIO.LOW)
			GPIO.output(self.backwardPin,GPIO.HIGH)
			time.sleep(self.tiempoDeInercia)
			GPIO.output(self.enable,GPIO.HIGH)
		time.sleep(self.tiempoParaPulso)
		if os.uname()[1] == 'raspberrypi':
			GPIO.output(self.enable,GPIO.LOW)
		self.ultimoEstado = 'Filtro Desactivado'

	def obtenerUltimoEstado(self):
		return self.ultimoEstado

if __name__ == '__main__':
	miFiltroPrueba = IRSwitch(50)
	counter = 0
	while (counter<100):
		miFiltroPrueba.colocarFiltroIR()
		print(miFiltroPrueba.obtenerUltimoEstado())
		time.sleep(1)
		miFiltroPrueba.quitarFiltroIR()
		print(miFiltroPrueba.obtenerUltimoEstado())
		time.sleep(3)
		counter+=1
