import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)

#time.sleep(5)

#print("going hot!")
#GPIO.output(8, GPIO.HIGH)
