"""import time
import picamera
frames = 2
def filenames():
	frame = 0
	while frame < frames:
		yield "image%02d.jpg" % frame
		frame += 1

with picamera.PiCamera() as camera:
	camera.resolution = (3240,2464)
	camera.framerate = 3
	camera.start_preview()
	# Give the camera some warm-up time
	time.sleep(2)
	start = time.time()
	camera.capture_sequence(filenames(), use_video_port=True)
	finish = time.time()

print("Captured %d frames at %.2ffps" % (frames,frames / (finish - start)))

"""

import picamera
import time

my_file = 'test.jpg'
with picamera.PiCamera() as camera:
    camera.resolution = camera.MAX_RESOLUTION
    camera.framerate = 5
    #camera.zoom = (0.25, 0.25, 0.25, 0.25)
    camera.shutter_speed = 190000
    camera.iso = 800
    camera.start_preview()
    time.sleep(5)
    camera.capture(my_file)