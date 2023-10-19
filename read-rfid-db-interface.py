#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

import db_interface
db_interface.connect_to_db("first.db")

try:
  id, text = reader.read()
  #print(hex(id))
  #print(text)
  
  row, duplicate = db_interface.get_row_from_uid(id)
  
  name, is_admin = row[1:] # first element is uid; we already have it
  
  if name: print("Hello, %s" % name)
  if is_admin == 1: print("you are an admin!")
  if duplicate: print("duplicate detected")
finally:
  GPIO.cleanup()
  db_interface.close()
