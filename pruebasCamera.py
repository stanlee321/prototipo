# Prueba camara
import os
import sys
import time
import picamera

directorioDeReporte = os.getenv('HOME')+'/imagenes'

piCamera = False
resolucion = 5

def __main_function__():
	print('Iniciando Prueba')
	# Encontrando la resolucion correspondiente:
	if resolucion == 5: 
		width = 2592
		height = 1944
		fov = 'full'
	elif resolucion == 8:
		width = 3280
		height = 2464
		fov = 'full'
	elif resolucion == 2:
		width = 1920
		height = 1080
		fov = 'partial'
	elif resolucion == 1.5:
		width = 1640
		height = 922
		fov = 'full'
	elif resolucion == 1:
		width = 1280
		height = 720
		fov = 'partial'
	elif resolucion == 0.3:
		width = 640
		height = 480
		fov = 'partial'
	elif resolucion == 0.1:
		width = 320
		height = 240
		fov = 'partial'

	print('Seleccionado ', width,' x ',height,' at ', fov, ' FOV')
	contador = 0
	camera = picamera.PiCamera()
	while True:
		tiempoAuxiliar = time.time()
		camera.capture(directorioDeReporte+'/image_{}.jpg'.format(contador))
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado)
		if contador >=10:
			break
		contador +=1


if __name__ == '__main__':
	for input in sys.argv:
		if input == 'picamera':
			piCamera = True
		if 'mp' in input:
			resolucion = float(input[:-2])
			print('Introducido ', resolucion,' MPx')
		if input == 'Show':
			mostrarImagen = True
		if 'fps' in input:
			mifps = int(input[:-3])
		if input =='Kill':
			topeEjecucion = int(input[:-1])
		if 'gamma' in input:
			gamma = float(input[:-5])
		if input == 'noDraw':
			noDraw = True

	__main_function__()