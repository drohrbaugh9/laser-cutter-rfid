#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

import db_interface
db = db_interface.db_interface("prod.db")

try:
  fullname = input("enter your full name: ")
  
  uid, text = reader.read()
  #print(hex(uid))
  #print(text)
  
  db.add_admin(uid, fullname)
  
  result = db._db_cursor.execute("SELECT * from users WHERE ramcard_uid = ?", [uid])
  print(result.fetchall())
  
finally:
  GPIO.cleanup()
  db.close()
