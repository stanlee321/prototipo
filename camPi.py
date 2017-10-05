import picamera as pc
import picamera.array


from collections import deque
from threading import Thread


class Video_Camera(Thread):
    def __init__(self,fps,width,height,vflip,hflip,mins):
        self.input_deque = deque(maxlen=fps*mins*60) 
        self.fps = fps

        #self.resolution = (width, height)
        self.vflip = vflip
        self.hflip = hflip
        self.mins = mins
        self.camera = pc.PiCamera( resolution=(width,height), framerate=int(self.fps))
        self.stream = 0
        #...
         
    def initialize_camera(self):
        self.camera = pc.PiCamera(
            resolution=(self.width,self.height), 
            framerate=int(self.fps))
            #...     
    def initialize_video_stream(self):
        self.rawCapture = picamera.array.PiRGBArray(self.camera, size=self.camera.resolution) 
        self.stream = self.camera.capture_continuous(self.rawCapture,format='jpeg', use_video_port=True)

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.run, args=()).start()
        return self
         
    def run(self):
        #This method is run when the command start() is given to the thread
        for f in self.stream:
            #add frame with timestamp to input queue
            #self.input_deque.append({
            #    'time':time.time(),
            #    'frame_raw':f.array})
            self.frame_array = f

    def read(self):
        #return self.input_deque.pop()
        return self.frame_array


