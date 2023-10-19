#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

import sqlite3

testdb = sqlite3.connect("first.db")
cur = testdb.cursor()

try:
  id, text = reader.read()
  #print(hex(id))
  
  res = cur.execute("SELECT fullname,is_admin FROM users WHERE ramcard_uid = ?", [id])
  name, is_admin = res.fetchone()
  print("Hello, %s" % name)
  if is_admin == 1:
    print("you are an admin!")
  
  if(res.fetchone()):
    print('duplicate entry detected')
  
  #print(text)
finally:
  GPIO.cleanup()
  testdb.close()
