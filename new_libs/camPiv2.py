# camPi2

# thanks to Adrian and his page pyimagesearch and his post about increasing
# the speed of fps in rapsberry pi

# import the necessary packages
#from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2






class PiRGBAArray(picamera.array.PiRGBArray):
    ''' PiCamera module doesn't have 4 byte per pixel RGBA/BGRA version equivalent, so this inherits from the 3-bpp/RGBA/BGRA version to provide it
    '''
    def flush(self):
        self.array = self.bytes_to_rgba(self.getvalue(), self.size or self.camera.resolution)

    def bytes_to_rgba(self, data, resolution):
        ''' Converts a bytes objects containing RGBA/BGRA data to a `numpy`_ array.  i.e. this is the 4 byte per pixel version.
            It's here as a class method to keep things neat - the 3-byte-per-pixel version is a module function. i.e. picamera.array.bytes_to_rgb()
        '''
        width, height = resolution
        fwidth, fheight = picamera.array.raw_resolution(resolution)
        # Workaround: output from the video splitter is rounded to 16x16 instead
        # of 32x16 (but only for RGB, and only when a resizer is not used)
        bpp = 4
        if len(data) != (fwidth * fheight * bpp):
            fwidth, fheight = picamera.array.raw_resolution(resolution, splitter=True)
            if len(data) != (fwidth * fheight * bpp):
                raise PiCameraValueError('Incorrect buffer length for resolution %dx%d' % (width, height))
        # Crop to the actual resolution
        return np.frombuffer(data, dtype=np.uint8).reshape((fheight, fwidth, bpp))[:height, :width, :]



class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=32, vf=False, hf=False):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.vflip = vf
        self.camera.hflip = hf


        self.HDrawCapture = PiRGBArray(self.camera)
        self.LRrawCapture = PiRGBArray(self.camera, size=(320,240))


        self.hiResStream = self.camera.capture_continuous(self.HDrawCapture, format="bgr", use_video_port=True)
        self.lowResStream = self.camera.capture_continuous(self.LRrawCapture, format="bgr", use_video_port=True, splitter_port=2, resize=(320,240))
        
        self.stream = self.camera.capture_continuous(self.rawCapture,format="bgr", use_video_port=True)
 
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frameLR = None
        self.frameHD = None
        self.stopped = False


        self.frame_resized = None
        
    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            #for f in self.stream:
            lrs  = self.lowResStream.next()
            self.frameLR = lrs.array
            self.lowResStream.truncate(0)
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            
            hdf = self.hiResStream.next()
            self.frameHD = hdf.array
            self.hiResStream.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.HDrawCapture.close()
                self.LRrawCapture.close()
                self.hiResStream.close()
                self.lowResStream.close()
                self.camera.close()
                return

    def read(self):
        # return the frame most recently read
        return self.frameHD, self.frameLR
 
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True