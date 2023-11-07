#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # /usr/local/lib/python3.9/dist-packages/mfrc522
import db_interface
import RPi_I2C_driver as lcd_driver
import time

LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 6

def main():
  
  # -- GPIO setup --
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup(8, GPIO.OUT, initial=GPIO.LOW)
  GPIO.setup(10, GPIO.IN)
  
  # -- rfid setup --
  reader = SimpleMFRC522()
  
  # connect to database
  db = db_interface.db_interface("/home/pi/senior_design_FA23/laser-cutter-rfid/prod.db")
  
  # -- LCD setup --
  lcd = my_lcd()
  lcd.setup()
  
  try:
    
    while True:
      
      uid = reader.read_id_no_block()
      
      # if the DONE button is pressed
      #  because a user just finished using the laser cutter ...
      if GPIO.input(10):
        # ... wait for it to be released AND
        #  wait for the user to remove their card
        while GPIO.input(10) or uid:
          time.sleep(LASER_OFF_POLLING_RATE_SECONDS)
          uid = reader.read_id_no_block()
          if not uid: uid = reader.read_id_no_block()
        time.sleep(2)
      
      # if no card is detected ...
      if not uid:
        # ... display the idle message, wait,
        #  and then go back to the top of this while loop
        lcd.display_string("scan your", 1)
        lcd.display_string("RamCard to use", 2)
        time.sleep(LASER_OFF_POLLING_RATE_SECONDS)
        continue
      
      row, duplicate = db.get_row_from_uid(uid)
      
      # if the uid is not in the database ...
      if not row:
        # ... indicate that the card is not recognized
        #  and then go back to the top of this while loop
        lcd.display_uid_not_recognized()
        continue
      
      # this uid is in the database,
      #  so get corresponding name from uid and display it
      name = db._get_name(row)
      lcd.display_string(name, 1)
      
      # if this user is not authorized to use the laser
      #  (i.e. if their acces has expired) ...
      if not db._check_uid(row):
        # ... indicate that this user is not authorized
        # and then go back to the top of this while loop
        lcd.display_uid_not_authorized()
        continue
      
      # TODO process to add a user
      # if the NEXT button is pressed and an admin has scanned their card...
      '''if GPIO.input(<next button pin number>) and db._is_admin(row):
        # ... wait until a different uid is scanned
        #  prompt the user to enter their name with the four buttons
        #  and add them to the database as a user: db.add_user(uid, name)
        continue'''
      
      # this user is authorized, so turn on the laser
      lcd.display_uid_authorized()
      GPIO.output(8, GPIO.HIGH)
      
      times_card_missing = 0
      max_times_card_missing = LASER_ON_GRACE_PERIOD_SECONDS / LASER_ON_POLLING_RATE_SECONDS
      current_user_uid = uid
      
      while True:
        time.sleep(LASER_ON_POLLING_RATE_SECONDS)
        
        # if the user is pressing the DONE button ...
        if GPIO.input(10):
          # ... turn off the laser and break out of this inner while loop
          GPIO.output(8, GPIO.LOW)
          lcd.display_string("DONE", 2)
          time.sleep(2)
          #lcd.lcd_clear()
          break
        
        # begin checking that a card is still present
        uid = reader.read_id_no_block()
        if not uid: uid = reader.read_id_no_block() # try again immediately if first read failed
        
        # if a card is present, check it against the database
        if uid:
          row, duplicate = db.get_row_from_uid(uid) # TODO check if uid == current_user_uid first?
          
          if row:
            name = db._get_name(row)
            lcd.display_string(name, 1)
            
            # if the uid has not changed since the last check OR
            #  the new uid is authorized,
            #  go back to the top of this inner while loop
            if uid == current_user_uid or db._check_uid(row):
              current_user_uid = uid
              times_card_missing = 0
              lcd.display_uid_authorized()
              continue
            
            lcd.display_uid_not_authorized(clear = False)
          
          else:
            lcd.display_uid_not_recognized(clear = False)
        
        # a card is not present,
        #  so increment the number of times a check has not detected a card
        times_card_missing += 1
        
        # if the card is missing for too long, shut off the laser
        #  and break out of this inner while loop
        if times_card_missing > max_times_card_missing:
          lcd.display_string("time up!", 2)
          GPIO.output(8, GPIO.LOW) # laser and chiller OFF
          time.sleep(2)
          lcd.lcd_clear()
          break
        
        # alert the user that they need to return their card to the reader
        #  and update how much time they have left to do so
        if times_card_missing > 0:
          lcd.display_string("card missing!", 1)
          time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
          lcd.lcd_display_string(time_str, 2)
          continue
  
  # if this program errors out,
  #  "turn off" the lcd and close the connection to the database
  #  before exiting
  finally:
    lcd.lcd_clear()
    lcd.backlight(0)
    db.close()
    # TODO print error for debugging purposes?

# TODO move this to its own file
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
    self.display_string("AUTHORIZED", 2)

if __name__ == "__main__":
  main()
