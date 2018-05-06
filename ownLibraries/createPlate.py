import scipy.misc
import cv2

class WritePlate():
	def __init__(self):
		self.font = cv2.FONT_HERSHEY_SIMPLEX
	def __call__(self, path_to_image = '', region = '', plate = ''):

		path_to_new_image = path_to_image[:path_to_image.rfind('.')]

		px0 = region[0]['x']
		py0 = region[0]['y']
		px1 = region[2]['x']
		py1 = region[2]['y']

		textx = region[0]['x']
		texty = region[0]['y']

		img = cv2.imread(path_to_image)
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		img = cv2.rectangle(img,(px0,py0),(px1,py1),(0,255,0),3)

		img = cv2.putText(img, plate,(textx,int(texty*0.95)), self.font, 1,(0,255,3),2,cv2.LINE_AA)
		save_in = "{}_detected.jpg".format(path_to_new_image)
		scipy.misc.imsave(save_in, img)




