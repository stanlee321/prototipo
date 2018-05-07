import cv2
import numpy as np
import sys
import glob
import math
import time
import os

class PlateRegionDetector():
	"""
	Plate detection algo, 
		inputs: 
			RGB image of a car with exterior region around it, from disk or from memory

		outputs: list of posible plates as opencv image rectangles of shape 240 x 160 x 3

		process_image method  parameters:
			options: path:	  		Path to image or opencv image from disk
					 fromDisk  		Bool if True expect image path dirsk
					 type:			'rect' or 'square'
					 crop:			'rect' or 'warp'
					 draw: 			Bool if True draw rectangles
					 brightness:	Amount of applied brightness in image 
					 thresh:   		Control the aparition of plate, if is close to 0 , it creates more artifacts, stable value 0.4

	"""

	def __init__(self):
		pass

	def validate_contour(self, contour, img, aspect_ratio_range, area_range):

		rect = cv2.minAreaRect(contour)
		img_width = img.shape[1]
		img_height = img.shape[0]
		box = cv2.boxPoints(rect) 
		box = np.int0(box)

		X = rect[0][0]
		Y = rect[0][1]
		angle = rect[2] 
		width = rect[1][0]
		height = rect[1][1]

		angle = (angle + 180) if width < height else (angle + 90)

		output=False

		if (width > 0 and height > 0) and ((width < img_width/2.0) and (height < img_width/2.0)):
			aspect_ratio = (float(width)/height) if (width > height) else (float(height)/width)
			if (aspect_ratio >= aspect_ratio_range[0] and aspect_ratio <= aspect_ratio_range[1]):
				if((height*width > area_range[0]) and (height*width < area_range[1])):

					box_copy = list(box)
					point = box_copy[0]
					del(box_copy[0])
					dists = [((p[0]-point[0])**2 + (p[1]-point[1])**2) for p in box_copy]
					sorted_dists = sorted(dists)
					opposite_point = box_copy[dists.index(sorted_dists[1])]
					tmp_angle = 90

					if abs(point[0]-opposite_point[0]) > 0:
						tmp_angle = np.abs(float(point[1]-opposite_point[1]))/np.abs(point[0]-opposite_point[0])
						tmp_angle = self.rad_to_deg(np.arctan(tmp_angle))

					if tmp_angle <= 45:
						output = True
		return output

	def deg_to_rad(self, angle):
		return angle*np.pi/180.0

	def rad_to_deg(self, angle):
		return angle*180/np.pi

	def enhance(self, img):
		kernel = np.array([[-1,0,1],[-2,0,2],[1,0,1]])
		return cv2.filter2D(img, -1, kernel)


	def warptransformation(self, img, box):
		# now that we have our rectangle of points, let's compute
		# the width of our new image

		orig_pts = box
		dest_pts = np.float32([[0, -85], [500, -85], [0,350], [500, 350]])


		# Get perspective transform M
		M = cv2.getPerspectiveTransform(orig_pts, dest_pts)
		# warp image with M
		drawing = cv2.warpPerspective(img, M, (420, 240))
		# show the image

		return drawing


	def increase_contrast(self, img, kernel=(8,8)):
		# CLAHE (Contrast Limited Adaptive Histogram Equalization)
		clahe = cv2.createCLAHE(clipLimit=3., tileGridSize = kernel)

		lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # convert from BGR to LAB color space
		l, a, b = cv2.split(lab)  # split on 3 different channels

		l2 = clahe.apply(l)  # apply CLAHE to the L-channel

		lab = cv2.merge((l2,a,b))  # merge channels

		out = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)  # convert from LAB to BGR

		return out


	def increase_brightness(self, img, value=30):
	    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	    h, s, v = cv2.split(hsv)

	    lim = 255 - value
	    v[v > lim] = 255
	    v[v <= lim] += value

	    final_hsv = cv2.merge((h, s, v))
	    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
	    return img


	def process_image(self, name, **options):
		print('WORKING IN NAME', name)

		se_shape = (16,4)

		if options.get('type') == 'rect':
			se_shape = (17,4)

		elif options.get('type') == 'square':
			se_shape = (7,6)

		if options.get('fromDisk') is True:
			raw_image = cv2.imread(name, 1)
		else:
			raw_image = cv2.cvtColor(name, cv2.COLOR_BGR2GRAY)

		input_image = np.copy(raw_image)

		gray = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
		gray = self.enhance(gray)
		gray = cv2.GaussianBlur(gray, (5,5), 0)
		gray = cv2.Sobel(gray, -1, 1, 0)
		h,sobel = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		se 		= cv2.getStructuringElement(cv2.MORPH_RECT, se_shape)
		gray 	= cv2.morphologyEx(sobel, cv2.MORPH_CLOSE, se)
		ed_img 	= np.copy(gray)

		_,contours,_=cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

		font 		= cv2.FONT_HERSHEY_SIMPLEX
		counter 	= 0
		out_images = []
		for contour in contours:
			aspect_ratio_range = (2.2, 12)
			area_range = (500, 18000)

			if options.get('type') == 'rect':
				aspect_ratio_range = (1.2, 6)
				area_range = (500, 18000)

			elif options.get('type') == 'square':
				aspect_ratio_range = (1, 2)
				area_range = (300, 8000)

			if self.validate_contour(contour, gray, aspect_ratio_range, area_range):
				rect = cv2.minAreaRect(contour)  
				box = cv2.boxPoints(rect)
				box = np.int0(box)  
				Xs = [i[0] for i in box]
				Ys = [i[1] for i in box]
				x1 = min(Xs)
				x2 = max(Xs)
				y1 = min(Ys)
				y2 = max(Ys)

				angle = rect[2]

				if angle < -45:
					angle += 90 

				W = rect[1][0]
				H = rect[1][1]
				aspect_ratio = (float(W)/H) if W > H else (float(H)/W)

				center = ((x1+x2)/2,(y1+y2)/2)
				size = (x2-x1, y2-y1)
				M = cv2.getRotationMatrix2D((size[0]/2, size[1]/2), angle, 1.0);
				tmp = cv2.getRectSubPix(ed_img, size, center)
				tmp = cv2.warpAffine(tmp, M, size)
				TmpW = H if H > W else W
				TmpH = H if H < W else W
				tmp = cv2.getRectSubPix(tmp, (int(TmpW),int(TmpH)), (size[0]/2, size[1]/2))
				__,tmp = cv2.threshold(tmp,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

				white_pixels = 0

				for x in range(tmp.shape[0]):
					for y in range(tmp.shape[1]):
						if tmp[x][y] == 255:
							white_pixels += 1

				edge_density = float(white_pixels)/(tmp.shape[0]*tmp.shape[1])

				tmp = cv2.getRectSubPix(raw_image, size, center)
				tmp = cv2.warpAffine(tmp, M, size)
				TmpW = H if H > W else W
				TmpH = H if H < W else W
				tmp = cv2.getRectSubPix(tmp, (int(TmpW),int(TmpH)), (size[0]/2, size[1]/2))


				if edge_density > options.get('thresh'): # While less thresh, it creates more artifacts

					input_image = np.copy(raw_image)


					
					# Scaled Points
					
					input_image = self.increase_brightness(input_image, value = options.get('brightness'))
					input_image = self.increase_contrast(input_image, kernel = (32,32))

					scale = options.get('scale') # if 0.0 shows original points

					p1 = (box[0][0] + int(scale*box[0][0]) , box[0][1] + int(scale*box[0][1]))
					p2 = (box[1][0] - int(scale*box[1][0]), box[1][1] + int(scale*box[1][1]))
					p3 = (box[2][0] - int(scale*box[2][0]) , box[2][1] - int(scale*box[2][1]))
					p4 = (box[3][0] + int(scale*box[3][0]) , box[3][1] - int(scale*box[3][1]))

					# Drawing
					if options.get('draw') == True:

						cv2.circle(input_image,p1, 5, (0,0,0), -1) # Black
						cv2.circle(input_image,p2, 5, (225,255,0), -1)
						cv2.circle(input_image,p3, 5, (0,255,0), -1) # green
						cv2.circle(input_image,p4, 5, (225,255,255), -1) # White
						
						# Draw outer rectangle Blue line
						cv2.line(input_image, tuple(p1), tuple(p2), (255,0,0), 2)
						cv2.line(input_image, tuple(p2), tuple(p3), (255,0,0), 2)
						cv2.line(input_image, tuple(p3), tuple(p4), (255,0,0), 2)
						cv2.line(input_image, tuple(p4), tuple(p1), (255,0,0), 2)
						
						# Draw inner rectangle
						cv2.drawContours(input_image, [box], 0, (127,0,255),2)
					else:
						pass

					# Croping
					if options.get('crop') == 'rect':	# cut image	 with rect	
						input_image = input_image[p4[1]: p1[1], p3[0]: p4[0]]
					else:								# cut iamge with warp (dafault)
						orig_pts  = np.float32([p3,p4, p2,p1])
						input_image = self.warptransformation(input_image, orig_pts)

					input_image = cv2.resize(input_image, (240,160))

					out_images.append(input_image)

		return out_images


	def __call__(self, path_to_folder = '../'):

		#os.chdir("/mydir")
		paths_to_images = []
		# List directory
		for image in glob.glob("{}*.jpg".format(path_to_folder)):
			print('FOUND IMAGE', image)
			paths_to_images.append(image)


		print('FOUND TOTAL IMAGES ARE:', paths_to_images)
		for path in paths_to_images:
			out_images = self.process_image(path, fromDisk = True, type='rect', crop='rect', draw = False, brightness = 50, thresh = 0.40, scale=0.200) 
			#paths_to_images.extend(out_images)
			local_images_paths = []
			for i, image in enumerate(out_images):
				local_images_paths.append('{}-{}-detected.jpg'.format(path[:path.rfind('.')],i))
				cv2.imwrite('{}-{}-detected.jpg'.format(path[:path.rfind('.')],i), image)
			paths_to_images.extend(local_images_paths)

		return paths_to_images
if __name__ == '__main__':

	if len(sys.argv) < 2:
		print ('usage:\n python pyANPD.py <image_file_path>')
		exit(0)

	path = sys.argv[1]
	t1 = time.time()
	plateDetector = PlateDetector()
	o1 = plateDetector.process_image(path, fromDisk = True, type='rect', crop='rect', draw = False, brightness = 50, thresh = 0.40, scale=0.200)

	for i, image in enumerate(o1):
		cv2.imwrite('{}-{}-detected.png'.format(path[:path.rfind('.')],i), image)

	print ('Time taken: %d ms'%((time.time()-t1)*1000))
