#!/usr/bin/env python

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)

from mfrc522 import SimpleMFRC522
reader = SimpleMFRC522()

import db_interface
db = db_interface.db_interface("first.db")

import RPi_I2C_driver as lcd_driver
lcd = lcd_driver.lcd()
lcd.backlight(1)

try:
  uid, text = reader.read()
  #print(hex(uid))
  #print(text)
  
  row, duplicate = db.get_row_from_uid(uid)
  
  if row:
    name = db._get_name(row)
    
    print("Hello, %s" % name)
    lcd.lcd_clear()
    lcd.lcd_display_string(name, 1)
    
    if db._is_admin(row): print("you are an admin!")
  if duplicate: print("duplicate detected")
  
  if db._check_uid(row):
    print("\nyou are authorized")
    GPIO.output(8, GPIO.HIGH)
finally:
  lcd.lcd_clear()
  lcd.backlight(0)
  #GPIO.cleanup()
  db.close()
