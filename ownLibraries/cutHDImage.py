
# import the necessary packages
from threading import Thread
from multiprocessing import Queue
import cv2
import datetime
import bgsubcnt
import time
#from semaforo import CreateSemaforo
import numpy as np

class cutHDImage():
	def __init__(self, shapeHR = None, shapeLR = None):

		print('<<<<< cutHDImage started! >>>>>')
		# values to upscale the LowRes image in x and y 

		self.scale_inx = shapeHR[0] / shapeLR[0]
		self.scale_iny = shapeHR[1] / shapeLR[1]

		self.listaderecortados = []


		self.HDframedemo = np.zeros(shapeHR)
		self.demodata = [(241, 96, 36, 48), (259, 120)], [(222, 27, 33, 56), (238, 55)]

	def __call__(self, HDframe = None, matches = None):
		
		#self.information = {}
		self.listaderecortados = []

		if len(matches) > 0:

			for match in matches:
				box = match[0]
				x = box[0]
				y = box[1]
				w = box[2]
				h = box[3]

				x1, y1 = x, y 
				x2, y2 = x + w - 1, y + h - 1
				# Upscale
				nx1, ny1 = self.scale_inx*x1, self.scale_iny*y1
				nx2, ny2 = self.scale_inx*x2, self.scale_iny*y2
				recortado = HDframe[int(ny1): int(ny2), int(nx1): int(nx2)]
				self.listaderecortados.append(recortado)
			return self.listaderecortados

		else:
			pass


if __name__ == '__main__':
	"""
	Debugss

	"""
	from videostreamv2 import VideoStream
	#shapeHR = (3264,2448)
	shapeHR = (640,480)
	shapeLR = (320,240)

	demodata = [(241, 96, 36, 48), (259, 120)], [(222, 27, 33, 56), (238, 55)]

	vs = VideoStream(src = 0, resolution = shapeHR).start()
	# Init cutimage
	cutImage = cutHDImage(shapeHR = shapeHR, shapeLR = shapeLR)

	time.sleep(1.0)


	# loop over frames from the video file stream
	while True:
		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale (while still retaining 3
		# channels)

		data = vs.read()

		frame = data['frame']
		LRFrame = data['LRFrame']

		# CutImage
		listaderecortados = cutImage(HDframe = frame, matches = demodata)

		for i, image in enumerate(listaderecortados):
			cv2.imwrite('imagen_{}_.jpg'.format(i), image)
		break
		#frame = np.dstack([frame, frame, frame])
	 
		# show the frame and update the FPS counter
		#cv2.imshow("Frame", frame_resized)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	# stop the timer and display FPS information
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()
