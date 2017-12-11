import numpy as np
import cv2

path = 0
cap = cv2.VideoCapture(path)

def nothing(x):
    pass
# Creating a window for later use
cv2.namedWindow('result')

# Starting with 100's to prevent error while masking
h,s,v = 100,100,100

# Creating track bar
cv2.createTrackbar('h', 'result',0,179,nothing)
cv2.createTrackbar('s', 'result',0,255,nothing)
cv2.createTrackbar('v', 'result',0,255,nothing)

while(1):

    _, frame = cap.read()

    w,h = frame.shape[0], frame.shape[1]

    frame = frame[int(w*0.25):int(w*0.35), int(h*0.20):int(h*0.5)]
    #converting to HSV
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    # get info from track bar and appy to result
    h = cv2.getTrackbarPos('h','result')
    s = cv2.getTrackbarPos('s','result')
    v = cv2.getTrackbarPos('v','result')

    # Normal masking algorithm
    lower_blue = np.array([h,s,v])
    upper_blue = np.array([180,255,255])# 180,255,255 Blue nad red, 90,255,255  green

    mask = cv2.inRange(hsv,lower_blue, upper_blue)

    result = cv2.bitwise_and(frame,frame,mask = mask)

    s = cv2.resize(result, (320*2, 240*2))
    cv2.imshow('result', s)

    ch = 0xFF & cv2.waitKey(5)
    if ch == ord('q'):
        break

cap.release()

cv2.destroyAllWindows()