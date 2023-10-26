#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # /usr/local/lib/python3.9/dist-packages/mfrc522
import db_interface
import RPi_I2C_driver as lcd_driver
import time

LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 10
LASER_ON_GRACE_PERIOD_SECONDS  = 60

def main():
  
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)
  
  reader = SimpleMFRC522()
  
  db = db_interface.db_interface("prod.db")
  
  lcd = my_lcd()
  lcd.setup()
  
  try:
    
    while True:
      
      uid = reader.read_id_no_block()
      
      if not uid:
        time.sleep(LASER_OFF_POLLING_RATE_SECONDS)
        continue
      
      row, duplicate = db.get_row_from_uid(uid)
      
      if not row:
        lcd.display_uid_not_recognized()
        continue
      
      name = db._get_name(row)
      lcd.display_string(name, 1)
    
      if not db._check_uid(row):
        lcd.display_uid_not_authorized()
        continue
      
      lcd.display_uid_authorized()
      GPIO.output(8, GPIO.HIGH) # laser and chiller ON
      
      times_card_missing = 0
      max_times_card_missing = LASER_ON_GRACE_PERIOD_SECONDS / LASER_ON_POLLING_RATE_SECONDS
      
      while True:
        time.sleep(LASER_ON_POLLING_RATE_SECONDS)
        
        uid = reader.read_id_no_block()
        
        if not uid: uid = reader.read_id_no_block() # try again immediately if first read failed
        
        if uid:
          row, duplicate = db.get_row_from_uid(uid)
          
          if row
            name = db._get_name(row)
            lcd.display_string(name, 1)
            
            if db._check_uid(row):
              #if times_card_missing >= 2: lcd.lcd_clear()
              times_card_missing = 0
              lcd.display_uid_authorized()
              continue
            
            lcd.display_uid_not_authorized(clear = False)
          
          else:
            lcd.display_uid_not_recognized(clear = False)
        
        times_card_missing += 1
        
        if times_card_missing > max_times_card_missing:
          lcd.display_string("time up!", 2)
          GPIO.output(8, GPIO.LOW) # laser and chiller OFF
          time.sleep(2)
          lcd.lcd_clear()
          break
        
        if times_card_missing > 0:
          lcd.display_string("card missing!", 1)
          time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
          lcd.lcd_display_string(time_str, 2)
          continue
        
        # TODO: need a way for user to indicate that they are done
  
  finally:
    lcd.lcd_clear()
    lcd.backlight(0)
    db.close()

class my_lcd(lcd_driver.lcd):
  
  def setup(self):
    self.lcd_clear()
    self.backlight(1)
  
  def display_string(self, short_str, row):
    padded_str = short_str + (' ' * (16 - len(short_str)))
    self.lcd_display_string(padded_str, row)
  
  def display_uid_not_recognized(self, clear = True):
    self.display_string("not recognized", 1)
    
    if clear:
      time.sleep(2)
      self.lcd_clear()
  
  def display_uid_not_authorized(self, clear = True):
    self.display_string("not authorized", 2)
    
    if clear:
      time.sleep(2)
      self.lcd_clear()
  
  def display_uid_authorized(self):
    lcd.display_string("AUTHORIZED", 2)

if __name__ == "__main__":
  main()