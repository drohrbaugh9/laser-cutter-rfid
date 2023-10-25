#!/usr/bin/env python

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)

from mfrc522 import SimpleMFRC522 # /usr/local/lib/python3.9/dist-packages/mfrc522
reader = SimpleMFRC522()

import db_interface
db = db_interface.db_interface("prod.db")

import RPi_I2C_driver as lcd_driver
lcd = lcd_driver.lcd()
lcd.lcd_clear()
lcd.backlight(1)

import time

try:
  
  while True:
    
    uid = reader.read_id_no_block()
    
    if not uid:
      time.sleep(0.5) # query the reader every 0.5 seconds while no card is detected
      continue
    
    row, duplicate = db.get_row_from_uid(uid)
    
    if not row:
      lcd.lcd_display_string("not recognized", 1)
      time.sleep(2)
      lcd.lcd_clear()
      continue
    
    name = db._get_name(row)
    lcd.lcd_display_string(name, 1)
    
    if db._check_uid(row):
      lcd.lcd_display_string("AUTHORIZED", 2)
      GPIO.output(8, GPIO.HIGH) # laser and chiller ON
      
      times_card_missing = 0
      
      while True:
        time.sleep(1)
        
        uid = reader.read_id_no_block()
        
        if uid:
          row, duplicate = db.get_row_from_uid(uid)
          if row and db._check_uid(row):
            if times_card_missing >= 2: lcd.lcd_clear()
            times_card_missing = 0
            name = db._get_name(row)
            lcd.lcd_display_string(name, 1)
            lcd.lcd_display_string("AUTHORIZED", 2)
            continue
          else:
            lcd.lcd_display_string("not recognized  ", 1)
        
        times_card_missing += 1
        
        if times_card_missing > 6:
          lcd.lcd_display_string("time up!        ", 2)
          GPIO.output(8, GPIO.LOW) # laser and chiller OFF
          time.sleep(2)
          lcd.lcd_clear()
          break
        
        if times_card_missing >= 2:
          lcd.lcd_display_string("card missing!   ", 1)
          time_str = "%d sec to return" % ((7 - times_card_missing) * 10)
          lcd.lcd_display_string(time_str, 2)
          continue
        
        # TODO: need a way for user to indicate that they are done
  
finally:
  lcd.lcd_clear()
  lcd.backlight(0)
  db.close()