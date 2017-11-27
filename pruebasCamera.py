# Prueba camara
import os
import sys
import time
import picamera
import numpy as np
import io, time, picamera, cv2

directorioDeReporte = os.getenv('HOME')+'/imagenes'

piCamera = False
resolucion = 5
numeroImagenes = 6

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
	
	miCamara = cv2.VideoCapture(1) 
	miCamara.set(cv2.CAP_PROP_FRAME_WIDTH, width) 
	miCamara.set(cv2.CAP_PROP_FRAME_HEIGHT, height) 
	for captura in range(numeroImagenes):
		print('captura Numero: ', captura)
		# Read plate
		tiempoAuxiliar = time.time()
		_, placa = miCamara.read()
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado,' con shape: ', placa.shape)
		#placaActual = placa[self.primerPunto[1]:self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
		#self.input_q.put((placaActual, captura, self.saveDir, self.fechaInfraccion))
	miCamera.release()
	print('Iniciando prueba con Picamera')
	#Prueba con stream
	frames = 0
	stream = io.BytesIO()
	with picamera.PiCamera() as camera:
		camera.resolution = (width, height)
		camera.start_preview()
		time.sleep(2)
		start = time.time()
		for i in range(0, numeroImagenes):
			camera.capture(stream, format='jpeg')
			stream.seek(0)
			data = np.fromstring(stream.getvalue(), dtype=np.uint8)
			image = cv2.imdecode(data, 1)
			(h,w,cols) = image.shape
			(xc,yc) = (h/2,w/2)
			frames = frames + 1
			#print("%02d center: %s (BGR)" % (frames,image[xc,yc]))

	print('Framerate %.2f fps' %  (frames / (time.time() - start)) )
	# 0.65 fps for 8MP
	# 1.51 fps for 0.3MPx for stream
	print('Iniciando prueba con Picamera direct SD')
	
	camera = picamera.PiCamera()
	camera.led= False
	camera.resolution = (width, height)
	output = np.empty((height, width, 3), dtype=np.uint8)
	while True:
		tiempoAuxiliar = time.time()
		camera.capture(directorioDeReporte+'/piCamMod_{}.jpg'.format(contador))
		#camera.capture(output, 'bgr')
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado)
		if contador >= numeroImagenes:
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
		if 'pic' in input:
			numeroImagenes = int(input[:-3])
		if input == 'noDraw':
			noDraw = True

	__main_function__()