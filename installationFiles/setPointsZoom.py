import numpy as np
import cv2
import os
import math
import time


help_message= '''USAGE: opt_flow.py [<video_source>]

Keys:t
 1 - toggle HSV flow visualization
 2 - toggle glitch
 Points  Selection:
 Press: Enter and Esc, to accept or don't accept respectively  
Lst
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
##########################################
def get_PointsSemaforZona(event,x,y,flags,param):
	global frame
	if event == cv2.EVENT_LBUTTONDOWN:
		listaCorte.append((x,y))
		if len(listaCorte)!= 0:
			cv2.circle(frame, (x,y),2,(0,255,0),-1)
			cv2.imshow('semaforo_Zona',frame)
###	###########################################
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
###############################################################
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
		print('Accediendo a camara ',nameSourceVideo)
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
		print('Error Al cargar la camara de flujo')
		try:
			if sys.argv[1] == 'picam':
				cap=cv2.VideoCapture(1)
				fileToWrite = directorioDeTrabajo+'prototipo/installationFiles/datos.npy'
				cont=0
		except:
			cap=cv2.VideoCapture(0)
		for i in range(100):
			ret, frame=cap.read()
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
	cv2.destroyAllWindows()

######################################
###Selccion Semaforo:
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
####--------º--------------------------------            
			lista.append((listaSemFinal))
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
		#cap=cv2.VideoCapture(directorioDeVideos+nameSourceVideo)
		#cap=cv2.VideoCapture('officialTrialVideos/sar.mp4')
		cap=cv2.VideoCapture(1)
		cap.set(3,2592)
		cap.set(4,1944)
		ret, frame1=cap.read()
		frame=cv2.resize(frame1,(640,480))
	except:
		print('Error Al cargar la camara de placas')
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