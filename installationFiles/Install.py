import numpy as np
import cv2
import os
import math
import time


help_message= '''Selección zona de análisis 

'''
listaSemFinal=[]
listaCorte=[]
listaSem=[]
lista=[]
listaAux=[]
listaAux1=[]
listaAux2=[]
listCorteAltaRes=[]
file_Points='datos.npy'


directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/'
directorioDeVideos = directorioDeTrabajo+'trialVideos/'
fileToWrite = directorioDeTrabajo+'prototipo/installationFiles/datos.npy'
###############Get indices#################
def obtenerIndicesSemaforo(poligono640):
	punto0 = poligono640[0]
	punto1 = poligono640[1]
	punto2 = poligono640[2]
	punto3 = poligono640[3]

	vectorHorizontal = punto3 - punto0
	vectorVertical = punto1 - punto0
	pasoHorizontal = vectorHorizontal//8
	pasoVertical = vectorVertical//24

	indices = []

	for j in range(24):
		for i in range(8):
			indices.append((punto0+i*pasoHorizontal+j*pasoVertical).tolist())
	#print('len of indices', len(indices))
	#print('single index', indices[0])
	indices = [[round(x[0]),round(x[1])] for x in indices]
	return indices

###########Calculate new Points############
def transformIma(lista):
	x2=lista[0][0]
	y2=lista[0][1]
	x3=lista[1][0]
	y3=lista[1][1]
	distancia=math.sqrt((x2-x3)**2+(y2-y3)**2)
	altura=distancia/3
	if y2>y3:
		print('caso1')
		anguloInicial=math.asin((y2-y3)/distancia)
		anguloInicialGrados=anguloInicial*180/(math.pi)
		anguloGrados=180-90-anguloInicialGrados
		anguloRadians=anguloGrados*(math.pi)/180
		y=altura*math.sin(anguloRadians)
		x=altura*math.cos(anguloRadians)
		x1=x2-x
		y1_0=y2-y
		y1=y1_0-altura
		x4=x3-x
		y4_0=y3-y
		y4=y4_0-altura
		poligon=[(x1,y1_0),(x2,y2),(x3,y3),(x4,y4_0)]
		poligonAdd=[(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
	if y3==y2:
		print('caso2')
		x1=x2
		y1_0=altura
		y1=2*altura
		x4=x3
		y4_0=altura
		y4=2*altura
		poligon=[(x1,y1_0),(x2,y2),(x3,y3),(x4,y4_0)]
		poligonAdd=[(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
	if y3>y2:
		print('caso3')
		anguloInicial=math.asin((y3-y2)/distancia)
		anguloInicialGrados=anguloInicial*180/(math.pi)
		anguloGrados=180-90-anguloInicialGrados
		anguloRadians=anguloGrados*(math.pi)/180
		y=altura*math.sin(anguloRadians)
		x=altura*math.cos(anguloRadians)
		x1=x2+x
		y1_0=y2-y
		y1=y1_0-altura
		x4=x3+x
		y4_0=y3-y
		y4=y4_0-altura
		poligon=[(x1,y1_0),(x2,y2),(x3,y3),(x4,y4_0)]
		poligonAdd=[(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
	return poligon, poligonAdd
###### Get points with the mouse click######
def get_PointsSemaforZona(event,x,y,flags,param):
	global frame
	if event == cv2.EVENT_LBUTTONDOWN:
		listaCorte.append((x,y))
		if len(listaCorte)!= 0:
			cv2.circle(frame, (x,y),2,(0,255,0),-1)
			cv2.imshow('semaforo_Zona',frame)
		if len(listaCorte)== 2:
			frame=cv2.rectangle(frame,listaCorte[0],listaCorte[1],(0,0,255),3)
			cv2.imshow('semaforo_Zona',frame)
########## Traffic light Selection##########
def get_PointsSema(event,x,y,flags,param):
	global imag
	if event == cv2.EVENT_LBUTTONDOWN:
		listaSem.append((x,y))
		if len(listaSem)!= 0:
			cv2.circle(imag, (x,y),2,(0,0,255),-1)
			cv2.imshow('semaforo',imag)
##########################################
def get_Points(event,x,y,flags,param):
	global frame
	if event == cv2.EVENT_LBUTTONDOWN:
		listaAux.append((x,y))
		if len(lista)>0:
			listaAux1.append((x//2,y//2))
		else:
			listaAux1.append((x//2,y//2))
		if len(listaAux)!= 0:
			cv2.circle(frame, (x,y),2,(0,255,255),-1)
			cv2.imshow('First_Frame',frame)
		if len(listaAux)>= 2:
			cv2.line(frame,listaAux[len(listaAux)-1],listaAux[len(listaAux)-2],(0,255,255),1)
		if len(listaAux)>= 4:
			cv2.line(frame,listaAux[len(listaAux)-1],listaAux[len(listaAux)-len(listaAux)],(0,255,255),1)
		cv2.imshow('First_Frame',frame)
############High resolution#############
def get_BigRectangle(event,x,y,flags,param):
	global frame
	if event == cv2.EVENT_LBUTTONDOWN:
		listaAux2.append((x,y))
		if len(listaAux2)<3:
			listCorteAltaRes.append((x*4,y*4))
			cv2.circle(frame, (x,y),3,(0,255,0),-1)
			cv2.imshow('FrameDeSltaResolucion',frame)
		if len(listaAux2)==2:        
			lista.append((listCorteAltaRes))
			frame=cv2.rectangle(frame,listaAux2[0],listaAux2[1],(0,0,255),3)      
			cv2.imshow('FrameDeSltaResolucion',frame)
			np.save(fileToWrite,lista)
			## file2.write("\n".listFinal)         
			print('Press -q- to Save and Exit')

def calcPoints(imag,listaS):
	imag=imag
	ancho=imag.shape[1]
	largo=imag.shape[0]
	x1=listaS[0]
	y1=listaS[1]
	x=listaCorte[0][0]+(x1*ancho)//640
	y=listaCorte[0][1]+(y1*largo)//480
	return x, y


if __name__ == '__main__':
    
	import sys
	print (help_message)
	try:
		nameSourceVideo = sys.argv[1]
		fileToWrite = fileToWrite[:-9]+nameSourceVideo[:-3]+'npy'
		
	except:
		nameSourceVideo = 0
		#print('Accediendo a camara ',nameSourceVideo)
###Semaforo zona:

	try:
		cap=cv2.VideoCapture(directorioDeVideos+nameSourceVideo)
		#cap=cv2.VideoCapture('officialTrialVideos/sar.mp4')
		for i in range(100):
			ret, frame=cap.read()
		frame=cv2.resize(frame,(640,480))
		frame2=frame.copy()
		fram=frame.copy()
		 
	except:
		try:
			if sys.argv[1] == 'picam':
				cap=cv2.VideoCapture(1)
				fileToWrite = directorioDeTrabajo+'prototipo/installationFiles/datos.npy'
				cont=0
				for i in range(50):
					ret, frame=cap.read()
		except:
			print('Accdiendo a imagen de flujo...')
			frame=cv2.imread('flujo.jpg')
		frame=cv2.resize(frame,(640,480))
		frame2=frame.copy()
		fram=frame.copy()
		 
	cv2.namedWindow('semaforo_Zona')
	cv2.setMouseCallback('semaforo_Zona', get_PointsSemaforZona)
	while True:
		print('press -z- to do zoom ')
		cv2 .imshow('semaforo_Zona',frame)
		keyPress = cv2.waitKey()
		if keyPress == ord('z'):
			#np.save(reAdjust,listaCorte)
			## file2.write("\n".listFinal)         
			#print('saved to ReAjust!!')
			#dataReAjust=np.load(reAdjust)
			#print ('file:..'+str(dataReAjust))
			print('listaCorte..'+str(listaCorte))
			break            
		if keyPress == ord('q'):
			print ('Interrumpido...')
			break
	cv2.destroyAllWindows()

######################################
###Selección Semáforo:
	imag1=frame2[listaCorte[0][1]:listaCorte[1][1],listaCorte[0][0]:listaCorte[1][0]]
	imag=imag1.copy()
	imag=cv2.resize(imag,(640,480))
	cv2.namedWindow('semaforo')
	cv2.setMouseCallback('semaforo', get_PointsSema)
	while(1):
		print('press -q- to accept the traffic light points and exit')
		cv2.imshow('semaforo',imag)
		keyPress = cv2.waitKey()
		if keyPress&0xFF==ord('q'):
			print('listaSemaforo..'+str(listaSem))
			rang=len(listaSem)
##TRansformando a coordenadas origen
			for i in range(0,len(listaSem)):
				x,y=calcPoints(imag1,listaSem[i])
				listaSemFinal.append((x,y))
				print(listaSemFinal)
####----------------------------------------- 
			indices=obtenerIndicesSemaforo(np.array(listaSemFinal))          
			lista.append((indices))
			break
		
	cv2.destroyAllWindows()
######################	
	#try:
	##	cap=cv2.VideoCapture(directorioDeVideos+nameSourceVideo)
	#	#cap=cv2.VideoCapture('officialTrialVideos/sar.mp4')
	#	ret, frame=cap.read()
	#	frame=cv2.resize(frame,(640,480))
	#	overlay=frame.copy() 
	#except:
	#	print('Error Al cargar la camara de flujo')
	frame=fram.copy()
	overlay=frame.copy()
	cv2.namedWindow('First_Frame')
	cv2.setMouseCallback('First_Frame', get_Points)
	
	while True:
		#print('press ESC to not accept and -y- to accept')
		cv2.imshow('First_Frame',frame)
		keyPress = cv2.waitKey()
		if keyPress == ord('y'):
			####listaAux1=listaAux(en magnitud)
			####listaAux1:contine valores para 320x240  ;listaAux:Valores para 640x480
			if len(listaAux)==2:
				pol1,polAdd=transformIma(listaAux)
				pol320,polAdd320=transformIma(listaAux1)
				lista.append((polAdd320))
				vrx=np.array([[pol1]],np.int32)
				pts=vrx.reshape((-1,1,2))
				cv2.polylines(frame,[pts],True,(255,0,0))
				print(pol1)
				########################
				vrx=np.array([[polAdd]],np.int32)
				pts=vrx.reshape((-1,1,2))
				cv2.polylines(frame,[pts],True,(0,0,255))
				print(polAdd)
				listaAux=[]
				listaAux1=[]
				cv2.imshow('First_Frame',frame)                

			if len(listaAux)>2:
				print('_____Data accept..')
				print('*Select two points next press -a- to obtain Angle')
				lista.append((listaAux1))
				vrx=np.array([[listaAux]],np.int32)
				pts=vrx.reshape((-1,1,2))
				cv2.polylines(frame,[pts],True,(0,0,255))
				cv2.imshow('First_Frame',frame)
				#print('lista: '+str(lista))
				listaAux=[]
				listaAux1=[]
				#print('ListaAux Removed...'+ str(listaAux))
				overlay=frame.copy()
		if keyPress == 27:
			print('_____Data not accept..')
			print('*Select two points next press -a- to obtain Angle')
			#print('lista no append: '+str(lista))
			listaAux=[]
			listaAux1=[]
			#print('ListaAux Removed...'+ str(listaAux))
			frame=overlay.copy()
			cv2.imshow('First_Frame',frame)
		if keyPress == ord('a'):
			
			vrx=np.array([[listaSemFinal]],np.int32)
			pts=vrx.reshape((-1,1,2))
			cv2.polylines(frame,[pts],True,(0,255,255))
			cv2.line(frame,(listaAux[0]),(listaAux[1]),(255,0,0),2)
			##Angle:
			x1=listaAux[0][0]
			y1=listaAux[0][1]
			x2=listaAux[1][0]
			y2=listaAux[1][1]
			nume=-(y2-y1) # por la inversion que se maneja al emplear imagenes
			deno=x2-x1
			if deno ==0:
			    alpha = np.sign(nume)*90
			else:
			    alpha=math.atan(nume/deno)
			alpha=alpha*180/(math.pi)
			if (deno<0):
			    alpha=alpha+180
			#print('angule:.'+str(alpha))
			lista.append([alpha])
			print('Press -q- to go a Full Resolution')
		if keyPress&0xFF==ord('q'):
			print ('lista:  ---' +str(lista))
			break
	cv2.destroyAllWindows()
	#Capture of High Resolution
	try:
		cap=cv2.VideoCapture(directorioDeVideos+nameSourceVideo)
		#cap=cv2.VideoCapture('officialTrialVideos/sar.mp4')
		ret, frame1=cap.read()
		frame=cv2.resize(frame1,(640,480))
	except:
		print('accediendo a imagen de placas...')
		frame=cv2.imread('placa.jpg')
		frame=cv2.resize(frame1,(640,480))
	overlayHigh=frame.copy()
	cv2.namedWindow('FrameDeSltaResolucion')
	cv2.setMouseCallback('FrameDeSltaResolucion', get_BigRectangle)
	while(len(listaAux2)<3):
		cv2.imshow('FrameDeSltaResolucion',frame)
		keyPress = cv2.waitKey()
		if keyPress&0xFF==ord('q'):
			print('Full Resolution saved!! and file saved')
			data2=np.load(fileToWrite)
			print (data2)
			break
cv2.destroyAllWindows()	