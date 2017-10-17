import os
import cv2
import bgsubcnt
from multiprocessing import Process, Queue, Pool
from math_and_utils import get_centroid
from math_and_utils import distance

directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'

class CreateBGCNT():
	"""
	CLASS used to create BGCNT for purposes of extract the rectangle where the 
	car is in the screen, inputs: cls.visual(frame), outputs: list((rectanglex, rectangley)) positions.
	"""
	def __init__(self):
		# Define the parameters needed for motion detection

		self.fgbg = bgsubcnt.createBackgroundSubtractor(3, False, 3*60)
		self.k = 31
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
		self.min_contour_width=30
		self.min_contour_height=30

		self.input_q = Queue(maxsize=5)
		self.output_q = Queue(maxsize=5)

		self.process = Process(target= self.worker, args=(self.input_q, self.output_q))
		self.process.daemon = True

		pool = Pool(2,self.worker, (self.input_q, self.output_q))

	def worker(self, input_q, output_q):

		while True:

			matches = []
			gray = cv2.cvtColor(input_q.get(), cv2.COLOR_BGR2GRAY)

			smooth_frame = cv2.GaussianBlur(gray, (self.k,self.k), 1.5)
			#smooth_frame = cv2.bilateralFilter(gray,4,75,75)
			#smooth_frame =cv2.bilateralFilter(smooth_frame,15,75,75)

			self.fgmask = self.fgbg.apply(smooth_frame, self.kernel, 0.1)

			im2, contours, hierarchy = cv2.findContours(self.fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
			for (i, contour) in enumerate(contours):
			    (x, y, w, h) = cv2.boundingRect(contour)
			    contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
			    if not contour_valid:
			        continue
			    centroid = get_centroid(x, y, w, h)

			    matches.append(((x, y, w, h), centroid))
			output_q.put(matches)


	def __call__(self, LOW_RES_FRAM):

		self.input_q.put(LOW_RES_FRAM)

		matches = self.output_q.get()
		
		return matches, LOW_RES_FRAM


if __name__ == '__main__':
	"""
	This small trial is a proff of work for the current class
	"""
	miSustraccionPrueba = CreateBGCNT()

	try:
		nombreDeVideo = directorioDeVideos+'/{}.mp4'.format(sys.argv[1])
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
	except:
		nombreDeVideo = directorioDeVideos+'/mSquare.mp4'
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
		
	ret, capturaDeFlujoInicial = camaraParaFlujo.read()

	while True:
		print(miSustraccionPrueba(capturaDeFlujoInicial))
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break
