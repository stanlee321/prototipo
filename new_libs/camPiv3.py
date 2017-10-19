import picamera



with picamera.PiCamera() as camera:
    camera.resolution = (3264, 2448)
    camera.framerate = 12
    camera.start_recording('highres.mjpg')
    camera.start_recording('lowres.h264', splitter_port=2, resize=(320, 240))
    camera.wait_recording(30)
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()