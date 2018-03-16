"""
This new prototipe works with a Flask server the raspberry pi 
"""
import cv2
import time

#!/usr/bin/env python
import imutils
import time, sys

import main
import multiprocessing
import time
import numpy as np


# Función principal
def _mainProgram( ingest_queue = None):
    # Import some global varialbes
    miCamara = cv2.VideoCapture(0)
    time.sleep(2)

    while True:
        # Read camera
        ret, frameFlujo = miCamara.read()
        frameFlujo = cv2.resize(frameFlujo,(320,240))
        configs = np.load('./configs.npy')
        print('Configs in main are::', configs)
        #   pass
        if configs[0] == True:
            cv2.imwrite('cam.jpg',frameFlujo)








if __name__ == '__main__':

	vs = cv2.VideoCapture(0)
	time.sleep(1.0)

	while(True):

	   #read frame by frame the webcame stream
	   _,frame = vs.read()

	   # encode as a JPEG
	   res = bytearray(cv2.imencode(".jpeg", frame)[1])
	   size = str(len(res))

	   # stream to the stdout
	   sys.stdout.write("Content-Type: image/jpeg\r\n")
	   sys.stdout.write("Content-Length: " + size + "\r\n\r\n")
	   sys.stdout.write( str(res) )
	   sys.stdout.write("\r\n")
	   # we use 'informs' as a boundary   
	   sys.stdout.write("--informs\r\n")
	   

	   if cv2.waitKey(1) & 0xFF == ord('q'):
	      break

	cv2.destroyAllWindows()
	vs.stop()

	#_mainProgram()
