import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

def blink():
	print("Ejecutando...")
	iteracion=0
	while iteracion<30:
		GPIO.output(21, True)
		time.sleep(0.5)
		GPIO.output(21, False)
		time.sleep(1.5)
		iteracion=iteracion+1
	print("Done!!")
	GPIO.cleanup()

blink()
