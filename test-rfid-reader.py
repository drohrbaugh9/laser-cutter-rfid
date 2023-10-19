#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

EXPECTED_TEXT_LEN = 48
EXPECTED_TEXT = '\0' * EXPECTED_TEXT_LEN
EXPECTED_UID = 0x140ad12be4

reader = SimpleMFRC522()

print("testing rfid reader\nthis test expects the card labeled 'test'")

try:
  id, text = reader.read()
  #print(hex(id))
  #print(text)
  
  if id == EXPECTED_UID:
    print("SUCCESS read uid matches expected:\n read %s, expected %s" % (hex(id), hex(EXPECTED_UID)))
  else:
    print("FAIL\n read %s, expected %s" % (hex(id), hex(EXPECTED_UID)))
  
  '''
  if len(text) == EXPECTED_TEXT_LEN and text == EXPECTED_TEXT:
    print("SUCCESS read text matches expected")
  else:
    print("FAIL    read text does not match expected") 
  '''
  
except Exception as e:
  print("exception occured")
  print(e)
finally:
  GPIO.cleanup()