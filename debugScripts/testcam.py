import cv2
import sys

#print "Before cv2.VideoCapture(0)"
#print cap.grab()
cap = cv2.VideoCapture(0)

print ("After cv2.VideoCapture(0): cap.grab() --> " + str(cap.grab()) + "\n")

while True:
    ret, frame = cap.read()
    if frame is None:
        print ("BYE")
        break

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print ("After breaking, but before cap.release(): cap.grab() --> " + str(cap.grab()) + "\n")

cap.release()

print ("After breaking, and after cap.release(): cap.grab() --> " + str(cap.grab()) + "\n")

cap.open(0)
print ("After reopening cap with cap.open(0): cap.grab() --> " + str(cap.grab()) + "\n")

cv2.destroyAllWindows()

while True:
    cv2.waitKey(1)
