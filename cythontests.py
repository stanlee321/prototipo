

import cython
import cv2


@cython.boundscheck(False)
cdef unsigned char[:, :] threshold_fast(int T, unsigned char [:, :] image):
	# set the variable extension types
	cdef int x, y, w, h

	# grab the image dimensions
	h = image.shape[0]
	w = image.shape[1]

	# loop over the image
	for y in range(0, h):
		for x in range(0, w):
			# threshold the pixel
			image[y, x] = 255 if image[y, x] >= T else 0

	# return the thresholded image
	return image


image = cv2.imread("a9am.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

threshold_fast(5, image)