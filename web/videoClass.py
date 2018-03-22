import numpy as np
import os
import cv2

class FeedVideo():
    configs_server_path = os.getenv('HOME') +'/'+ 'trafficFlow' + '/'+ 'prototipo' + '/' +'web' + '/configs_server.npy'
    def __init__(self):
        # Create placeholder for imagen
        self.imagen     = None
        # Where to save the configs

        # Create configs for show and turnoff the feeds
        self.configs    = np.array([False,False])
        self.saveConfigsToDisk(path = FeedVideo.configs_server_path)

    # Some properties
    @property
    def imagen(self):
        return self.__imagen
    @property
    def configs(self):
        return self.__configs

    # Setters
    @configs.setter
    def configs(self, newConfigs):
        self.__configs = newConfigs
    @imagen.setter
    def imagen(self, newFrame):
        self.__imagen = newFrame


    def saveConfigsToDisk(self, path='./configs_server.npy'):
        print('saving configs to...', path)
        np.save('{}'.format(path), self.configs)

    # Getters
    def __call__(self):
        while True:
            ret, jpeg   =   cv2.imencode('.jpeg', self.imagen)
            framebytes  =   jpeg.tobytes()
            yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' +  framebytes + b'\r\n\r\n')
