import numpy as np
import cv2
import math
import time
import os

help_message = '''
USAGE: opt_flow.py [<video_source>]

Keys:t
 1 - toggle HSV flow visualization
 2 - toggle glitch
 Points  Selection:
 Press: Enter and Esc, to accept or don't accept respectively  
Lst
'''
lista=[]
listaAux=[]
listaAux1=[]
listaAux2=[]
listCorteAltaRes=[]
file_Points='datos.npy'

directorioDeTrabajo = directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/'
directorioDeVideos = directorioDeTrabajo+'trialVideos/'
fileToWrite = directorioDeTrabajo+'prototipo11/installationFiles/datos.npy'

def get_Points(event,x,y,flags,param):
    global frame
    global Control_Z
    if event == cv2.EVENT_LBUTTONDOWN:
        listaAux.append((x,y))
        if len(lista)>0:
            listaAux1.append((x//2,y//2))
        else:
            listaAux1.append((x,y))
        if len(listaAux)!= 0:
            cv2.circle(frame, (x,y),2,(0,255,0),-1)
            cv2.imshow('First_Frame',frame)
            #print ('listaAux...: '+str(len(listaAux)))
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
            print('Press -e- to Save and Exit')
                        
            #cv2.destroyAllWindows()

if __name__ == '__main__':
    
    import sys
    print (help_message)
    try:
        nameSourceVideo = sys.argv[1]
        fileToWrite = fileToWrite[:-9]+nameSourceVideo[:-3]+'npy'
    except:
        nameSourceVideo = 1
    print('Cargando Video de: ', directorioDeVideos+nameSourceVideo)
    try:
        cap=cv2.VideoCapture(directorioDeVideos+nameSourceVideo)
        for i in range(100):
            ret, frame=cap.read()
        frame=cv2.resize(frame,(640,480))
        overlay=frame.copy() 
    except:
        print('Error Al cargar la camara de flujo')
    cv2.namedWindow('First_Frame')
    cv2.setMouseCallback('First_Frame', get_Points)
    
    while True:
        cv2.imshow('First_Frame',frame)
        keyPress = cv2.waitKey()
        if keyPress == ord('y'):
            print('_____Data accept..')
            print('*Select two points next press -a- to obtain Angle')
            lista.append((listaAux1))
            
            #print('lista: '+ str(lista) +'listaAux: '+ str(listaAux) )
            #print('lista:'+str(len(lista)))
            #print('constante : '+ str(Control_Z))
            vrx=np.array([[listaAux]],np.int32)
            pts=vrx.reshape((-1,1,2))
            cv2.polylines(frame,[pts],True,(0,255,255))
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
            print('Press -q- to save')
        if keyPress&0xFF==ord('q'):
            np.save(fileToWrite,lista)
            ## file2.write("\n".listFinal)         
            print('saved!!')
            data=np.load(fileToWrite)
            print (data)
            break
    cv2.destroyAllWindows()
    try:
        cap=cv2.VideoCapture(0)
        cap.set(3,2592)
        cap.set(4,1944)
        ret, frame1=cap.read()
        frame=cv2.resize(frame1,(648,486))
    except:
        print('Error Al cargar la camara de placas')
    cv2.namedWindow('FrameDeSltaResolucion')
    cv2.setMouseCallback('FrameDeSltaResolucion', get_BigRectangle)
    while(len(listaAux2)<3):
        cv2.imshow('FrameDeSltaResolucion',frame)
        keyPress = cv2.waitKey()
        if keyPress&0xFF==ord('e'):
            print('Full Resolution saved!!')
            data2=np.load(fileToWrite)
            print (data2)
            break
cv2.destroyAllWindows()