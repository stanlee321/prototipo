# Smarth-Embeded-Camera and Traffic Light infractor
Implemation of a Smart Embedded Camera, this repo contains the necesary code to 
implement a Traffic Light infraction detector using a Raspberry Pi, Cameras and 
computer vision  and machine learning techniques.

In Bolivia there is a huge problem regarding Road culture, this project intends to solve this problem with the use of Artificial Inteliligence and Internet of things devices.

## SmartCamera project

Implementation SmartCamera with a picam, python, opencv and machine learning techniques.


You can see our results in our page [here](http://deepmicrosystems.com/)

And a video demo also 
[[![Video visualization demo](https://i.ytimg.com/vi/4Ew56N_uMIk/2.jpg)](https://youtu.be/4Ew56N_uMIk)


## Getting Started
1. `pip3 install -r requirements.txt`
2. `python3 prototipo25.py Show` 
    Optional arguments (default value a folder with todays date):
    * Folder to workon `Show'`
    * Test in custom video `myVideo.mp4'`

## Requirements
### Hardware 
- Your RPi3 must have conected to
- 5 or 8 MP NoIR PiCamera ( for take the HD shoots )
- Simple USB WebCam (camera for detec the flow of cars)
- Optional ( embeded circuit to control the IR filter)

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

