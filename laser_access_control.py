#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # /usr/local/lib/python3.9/dist-packages/mfrc522
import db_interface
import improved_lcd
import time

LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 20

LASER_RELAY_PIN_NUMBER = 8

DONE_BUTTON_PIN_NUMBER = 10

RED_LED_PIN_NUMBER = 32
GREEN_LED_PIN_NUMBER = 33
BLUE_LED_PIN_NUMBER = 35

def activate_keyboard_and_get_name():
  return "Test User"

def main():
  
  # -- GPIO setup --
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup(LASER_RELAY_PIN_NUMBER, GPIO.OUT, initial=GPIO.LOW)
  GPIO.setup(DONE_BUTTON_PIN_NUMBER, GPIO.IN)
  
  GPIO.setup(RED_LED_PIN_NUMBER, GPIO.OUT); red = GPIO.PWM(RED_LED_PIN_NUMBER, 2); red.start(0)
  GPIO.setup(GREEN_LED_PIN_NUMBER, GPIO.OUT); green = GPIO.PWM(GREEN_LED_PIN_NUMBER, 2); green.start(0)
  GPIO.setup(BLUE_LED_PIN_NUMBER, GPIO.OUT); blue = GPIO.PWM(BLUE_LED_PIN_NUMBER, 2); blue.start(0)
  
  # -- rfid setup --
  reader = SimpleMFRC522()
  
  # connect to database
  #  use absolute path because when this script runs at boot, it is not launched
  #  from this folder that it is in
  db = db_interface.db_interface("/home/pi/senior_design_FA23/laser-cutter-rfid/prod.db")
  
  # -- LCD setup --
  lcd = improved_lcd.lcd()
  lcd.setup()
  
  laser_just_finished_normally = False
  
  try:
    
    while True:
      
      uid = reader.read_id_no_block()
      
      # if a user just finished using the laser cutter ...
      if laser_just_finished_normally:
        time.sleep(2)
        # ... wait for the user to remove their card
        lcd.display_string("please remove", 1)
        lcd.display_string("your RamCard", 2)
        time.sleep(5)
        
        laser_just_finished_normally = False
        continue
      
      # if no card is detected ...
      if not uid:
        # ... display the idle message, wait,
        #  and then go back to the top of this while loop
        lcd.display_string("scan your", 1)
        lcd.display_string("RamCard to use", 2)
        blue.ChangeDutyCycle(100)
        red.ChangeDutyCycle(0)
        green.ChangeDutyCycle(0)
        time.sleep(LASER_OFF_POLLING_RATE_SECONDS)
        continue
      
      row, duplicate = db.get_row_from_uid(uid)
      
      # if the uid is not in the database ...
      if not row:
        # ... indicate that the card is not recognized
        #  and then go back to the top of this while loop
        red.ChangeDutyCycle(100)
        blue.ChangeDutyCycle(0)
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
        red.ChangeDutyCycle(100)
        blue.ChangeDutyCycle(0)
        lcd.display_uid_not_authorized()
        continue
      
      # if the DONE button is pressed and an admin has scanned their card...
      if GPIO.input(DONE_BUTTON_PIN_NUMBER) and db._is_admin(row):
        # ... wait until a different uid is scanned
        lcd.display_string("adding a user!", 1)
        lcd.display_string("scan new RamCard", 2)
        time.sleep(5)
        uid_to_add = reader.read_id_no_block()
        if not uid_to_add: uid_to_add = reader.read_id_no_block()
        
        if not uid_to_add:
          lcd.display_string("no card detected", 1)
          lcd.display_string("admin, re-scan", 2)
          time.sleep(2)
          lcd.display_string("admin, re-scan", 1)
          lcd.display_string("your RamCard", 2)
          continue
        
        data, duplicate = db.get_row_from_uid(uid_to_add)
        if (data):
          lcd.display_string("update entry for", 1)
          existing_name = db._get_name(row)[:15] + "?"
          lcd.display_string(existing_name, 2)
          time.sleep(2)
          lcd.display_string(existing_name, 1)
          lcd.display_string("press and hold", 2)
          time.sleep(2)
          lcd.display_string("press and hold", 1)
          lcd.display_string("DONE to confirm", 2)
          time.sleep(1)
          
          if not GPIO.input(DONE_BUTTON_PIN_NUMBER):
            continue
        
        #  prompt the user to enter their name with the keyboard
        lcd.display_string("enter your name", 1)
        lcd.display_string("on the keyboard", 2)
        time.sleep(2)
        lcd.display_string("press enter key", 1)
        lcd.display_string("when done", 2)
        
        name_to_add = activate_keyboard_and_get_name()
        
        #  and add them to the database as a user
        print("would have added a user with name %s, uid %d" % (name_to_add, uid_to_add))
        #db.add_user(uid_to_add, name_to_add)
        continue
      
      # this user is authorized, so turn on the laser
      lcd.display_uid_authorized()
      green.ChangeDutyCycle(100)
      blue.ChangeDutyCycle(0)
      GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.HIGH)
      
      times_card_missing = 0
      max_times_card_missing = LASER_ON_GRACE_PERIOD_SECONDS / LASER_ON_POLLING_RATE_SECONDS
      current_user_uid = uid
      
      while True:
        time.sleep(LASER_ON_POLLING_RATE_SECONDS)
        
        display_card_missing = True
        
        # if the user is pressing the DONE button ...
        if GPIO.input(DONE_BUTTON_PIN_NUMBER):
          # ... turn off the laser and break out of this inner while loop
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW)
          lcd.display_string(name, 1)
          lcd.display_string("DONE", 2)
          laser_just_finished_normally = True
          #time.sleep(2)
          #lcd.lcd_clear()
          break
        
        # if the card is missing for too long, shut off the laser
        #  and break out of this inner while loop
        if times_card_missing >= max_times_card_missing:
          lcd.display_string("", 1)
          lcd.display_string("time up!", 2)
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW) # laser and chiller OFF
          red.ChangeDutyCycle(100)
          green.ChangeDutyCycle(0)
          time.sleep(2)
          lcd.lcd_clear()
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
              green.ChangeDutyCycle(100)
              red.ChangeDutyCycle(0)
              lcd.display_uid_authorized()
              continue
            
            red.ChangeDutyCycle(100)
            green.ChangeDutyCycle(0)
            display_card_missing = False
            lcd.display_uid_not_authorized(clear = False, row = 1)
            
            # the card detected is not authorized,
            #  so increment the number of times a check has not detected an authorized card
            #  and go back to the top of this inner while loop
            #times_card_missing += 1
            #continue
          
          else:
            red.ChangeDutyCycle(100)
            green.ChangeDutyCycle(0)
            display_card_missing = False
            lcd.display_uid_not_recognized(clear = False, row = 1)
            
            # the card detected is not recognized,
            #  so increment the number of times a check has not detected an authorized card
            #  and go back to the top of this inner while loop
            #times_card_missing += 1
            #continue
        
        # a card is not present,
        #  so increment the number of times a check has not detected a card
        times_card_missing += 1
        
        if display_card_missing:
          red.ChangeDutyCycle(50) # blink at 2 Hz
          green.ChangeDutyCycle(0)
        
        # alert the user that they need to return their card to the reader
        #  and update how much time they have left to do so
        if times_card_missing > 0:
          if display_card_missing: lcd.display_string("card missing!", 1)
          time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
          lcd.display_string(time_str, 2)
          continue
  
  # if this program errors out,
  #  "turn off" the lcd and close the connection to the database
  #  before exiting
  finally:
    lcd.lcd_clear()
    lcd.backlight(0)
    db.close()
    # TODO print error for debugging purposes?

if __name__ == "__main__":
  main()
