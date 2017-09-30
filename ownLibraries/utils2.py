# From http://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/

import cv2
import datetime
from threading import Thread
import sys
# import the Queue class from Python 3
if sys.version_info >= (3, 0):
    from queue import Queue
 
# otherwise, import the Queue class for Python 2.7
else:
    from Queue import Queue



class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()


class WebcamVideoStream:
    def __init__(self, src, width, height, queueSize=128):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        (self.grabbed, self.frame) = self.stream.read()

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False
        # initialize the queue used to store frames read from
        # the video file
        self.Q = Queue(maxsize=queueSize)


    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self




        # start the thread to read frames from the video stream
        #Thread(target=self.update, args=()).start()
        #return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        # keep looping infinitely
        while True:
        # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
 
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
 
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stop()
                    return
 
                # add the frame to the queue
                self.Q.put(frame)

            # if the thread indicator variable is set, stop the thread
            #if self.stopped:
            #    return

            # otherwise, read the next frame from the stream
            #(self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.Q.get()


    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
