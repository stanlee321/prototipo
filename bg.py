
#bg.py

import os
import logging
import logging.handlers
import random

import numpy as np
#import skvideo.io
import cv2
#import matplotlib.pyplot as plt

import some_math
# without this some strange errors happen
cv2.ocl.setUseOpenCL(False)
random.seed(123)


from pipeline import (
    PipelineRunner,
    ContourDetection,
    VehicleCounter,
    Visualizer)

# ============================================================================
IMAGE_DIR = "./out"
VIDEO_SOURCE = "input.mp4"
SHAPE = (720, 1280)  # HxW
EXIT_PTS = np.array([
    [[732, 720], [732, 590], [1280, 500], [1280, 720]],
    [[0, 400], [645, 400], [645, 0], [0, 0]]
])
# ============================================================================

class BackgroundSub(object):
    def __init__(self, bg = None):

        # creating exit mask from points, where we will be counting our vehicles

        # there is also bgslibrary, that seems to give better BG substruction, but
        # not tested it yet

        # processing pipline for programming conviniance
        self.pipeline = PipelineRunner(pipeline=[
            ContourDetection(bg_subtractor = bg,save_image=True, image_dir=IMAGE_DIR),
            VehicleCounter( y_weight=2.0),
            Visualizer(image_dir = IMAGE_DIR)
            #OutScale(self.frame_number)
            ], log_level=logging.DEBUG)

        # Set up image source
        # You can use also CV2, for some reason it not working for me
        self._frame_number = -1
        self.frame_number = -1
        self.original_shape = None

    def train_bg_subtractor(self, inst, cap, num=500):
        '''
            BG substractor need process some amount of frames to start giving result
        '''
        print ('Training BG Subtractor...')
        i = 0
        for frame in cap:
            inst.apply(frame, None, 0.001)
            i += 1
            if i >= num:
                return cap


    def injector(self, frame_real=None, frame_resized=None, frame_number=None):

        #print(frame_real.shape)
        self.frame_number = frame_number

        self.original_shape = frame_real.shape

        self.pipeline.set_context({
            'frame': frame_resized,
            'frame_number': self.frame_number,
        })
        self.pipeline.run()

# ============================================================================

if __name__ == "__main__":
    log = some_math.init_logging()

    if not os.path.exists(IMAGE_DIR):
        log.debug("Creating image directory `%s`...", IMAGE_DIR)
        os.makedirs(IMAGE_DIR)

    main()
