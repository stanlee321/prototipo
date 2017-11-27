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


	frames = 0
	stream = io.BytesIO()
	with picamera.PiCamera() as camera:
		camera.resolution = (width, height)
		camera.start_preview()
		time.sleep(2)
		start = time.time()
		for i in range(0, 10):
			camera.capture(stream, format='jpeg')
			stream.seek(0)
			data = np.fromstring(stream.getvalue(), dtype=np.uint8)
			image = cv2.imdecode(data, 1)
			(h,w,cols) = image.shape
			(xc,yc) = (h/2,w/2)
			frames = frames + 1
			print("%02d center: %s (BGR)" % (frames,image[xc,yc]))

	print('Framerate %.2f fps' %  (frames / (time.time() - start)) )

	"""
	camera = picamera.PiCamera()
	camera.led= False
	camera.resolution = (width, height)
	output = np.empty((height, width, 3), dtype=np.uint8)
	while True:
		tiempoAuxiliar = time.time()
		#camera.capture(directorioDeReporte+'/image_{}.jpg'.format(contador))
		camera.capture(output, 'bgr')
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado)
		if contador >=10:
			break
		contador +=1
	"""

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