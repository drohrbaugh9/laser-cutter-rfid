#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
  id, text = reader.read()
  print(hex(id))
  if id == 0x2345b6f929:
    print('Hi, David!')
  #print(text)
finally:
  GPIO.cleanup()
