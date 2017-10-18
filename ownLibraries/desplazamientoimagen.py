import os
import cv2
import sys
import numpy as np

class DesplazamientoImagen():
    """
    Esta clase es simplemente una lista de diccionarios consistentes en:
    {'index':0,'image':imgNPArray,'images':listaDeNumpyArray}
    que permite controlar la entrada en memoria RAM
    """
    def __init__(self,size = 20):
        self.maximotamano = size
        self.lista = []
        self.ultimoIndice = 0

    def introducirImagen(self,imagen):
        # Introducimos la imagen con el ultimo indice
        self.lista.insert(0,{'index':self.ultimoIndice,'image':imagen,'images':[]})
        self.ultimoIndice +=1
        if len(self.lista) >self.maximotamano:
            self.lista.pop()
        return self.ultimoIndice -1

    def reestablecerDesplazamiento(self,size = 20):
        self.maximotamano = size
        del self.lista
        self.lista = []
        self.ultimoIndice = 0

if __name__ == '__main__':
    miDesplazamiento = DesplazamientoImagen()
    if os.uname()[1] == 'alvarohurtado-305V4A':
        miCamara = cv2.VideoCapture(1)
    else:
        miCamara = cv2.VideoCapture(0)
        miCamara.set(3,3296)
        miCamara.set(4,2512)
    miCamara.set(3,3296)
    miCamara.set(4,2512)
    
    while True:
        ret, capturaInicial = miCamara.read()
        cv2.imshow('Muestra',cv2.resize(capturaInicial,(320,240)))
        miDesplazamiento.introducirImagen(capturaInicial)
        print(capturaInicial.shape)
        print(sys.getsizeof(miDesplazamiento))
        print(miDesplazamiento.ultimoIndice)
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[F")
        ch = 0xFF & cv2.waitKey(5)
        if ch == ord('q'):
            break
