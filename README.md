# Smarth-Embeded-Camera and Traffic Light infractor
Implemation of a Smart Embedded Camera, this repo contains the necesary code to 
implement a Traffic Light infraction detector using a Raspberry Pi, Cameras and 
computer vision  and machine learning techniques.

In Bolivia there is a huge problem regarding Road culture, this project intends to solve this problem with the use of Artificial Inteliligence and Internet of things devices.

## SmartCamera project

Implementation SmartCamera with a picam, python, opencv and machine learning techniques.


You can see our results in our page [here](http://deepmicrosystems.com/)

And a video demo also 

[![Video visualization demo](https://github.com/AlvaroRQ/prototipo/blob/master/demo/demo.gif)](https://youtu.be/nVQm3AYlGUo)

## Getting Started
1. `pip3 install -r requirements.txt`
2. `python3 prototipo25.py Show` 
    Optional arguments (default value a folder with todays date):
    * Folder to workon `Show'`
    * Test in custom video `myVideo.mp4'`

## Requirements
### Hardware 
- Your RPi3 must be conected to
- 5 or 8 MP NoIR PiCamera ( for take the HD shoots )
- Simple USB WebCam (camera for detect the flow of cars)
- Embeded circuit to control a IR filter for NoIR PiCamera (Optional)

### Software
- [Python 3.5](https://www.continuum.io/downloads)
- [OpenCV 3.X](http://opencv.org/) (just for write the plates in the image )
- [scipy] (for write the images into disk)
- [scikit-learn] (for run the trafficlight color detector sensor)
- [sqlite3] (for track information about the Shutter PiCamera class)


## Notes
- Work in progress...
- Still working in a better ML model to get better results in the colors of the trafficlight.
- Still working in getting work the algorith with just one camera, the PiCamera.
- We are still recolecting video data from infractions to reemplace critical parts of the algorithm with RLL the learn the events of cars.

## Copyright
See [LICENSE](LICENSE) for details.

Copyright (c) 2018 (http://deepmicrosystems.com/).

