# camPi2

# thanks to Adrian and his page pyimagesearch and his post about increasing
# the speed of fps in rapsberry pi

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2
import numpy as np

class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=32, vf=False, hf=False):

        print('HELLO FROM PICAMERA')
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.vflip = vf
        self.camera.hflip = hf
        
        print('FRAMRATE',framerate)

        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="bgr", use_video_port=True)
 
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = np.zeros(resolution, np.int8)
        print('RES', self.frame.shape)
        self.stopped = False


        #self.frame_resized =  cv2.resize(self.frame, (320,240))
        self.frame_resized = np.zeros((320,240), np.int8)
        
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            #print(self.frame_resized.shape)
            self.rawCapture.truncate(0)
 
            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

    def read(self):
        # return the frame most recently read
        return self.frame
 
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True