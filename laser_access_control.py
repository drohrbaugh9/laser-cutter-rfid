#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # /usr/local/lib/python3.9/dist-packages/mfrc522
import db_interface
import improved_lcd
import time
import keyboard

LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 20

LASER_RELAY_PIN_NUMBER = 8

DONE_BUTTON_PIN_NUMBER = 10

RED_LED_PIN_NUMBER = 32
GREEN_LED_PIN_NUMBER = 33
BLUE_LED_PIN_NUMBER = 35

# ---------- keyboard handling stuff ---------

shift_pressed = False
accepting_keyboard_input = False

def activate_keyboard_and_get_name(lcd):
  global name_from_keyboard, keyboard_done, accepting_keyboard_input
  
  name_from_keyboard = ""
  keyboard_done = False
  accepting_keyboard_input = True
  
  # allow last message to stay for a little while
  # TODO: move instructions to enter name into here?
  #  and maybe enable the keyboard before displaying instructions,
  #  to capture any keys pressed as instructions are being displayed
  #  if the user knows what to do already
  time.sleep(2)
  
  lcd.lcd_clear()
  
  while not keyboard_done:
    #print(name_from_keyboard)
    lcd.display_string(name_from_keyboard, 1)
    time.sleep(0.25)
  
  accepting_keyboard_input = False
  keyboard_done = False
  
  return name_from_keyboard

def process_key_press(event):
  global name_from_keyboard, keyboard_done, shift_pressed, accepting_keyboard_input
  
  if event.name == 'shift':
    shift_pressed = True
  
  if not accepting_keyboard_input:
    return
  
  if event.name == 'enter':
    keyboard_done = True
    return
  
  if event.name == 'backspace':
    name_from_keyboard = name_from_keyboard[:-1]
  
  elif event.name == 'delete':
    name_from_keyboard = ''
  
  elif event.name == 'space':
    name_from_keyboard += ' '
  
  elif len(event.name) == 1:
    if shift_pressed:
      name_from_keyboard += event.name.upper()
    else:
      name_from_keyboard += event.name

def process_shift_release(event):
  global shift_pressed
  
  shift_pressed = False

# ---------- end keyboard handling stuff -----

# standardize checking done button
#  since the button is connected between the input pin and ground
#  when pressed it will pull the pin LOW
#  when not pressed, the pin is pulled high by a built-in pull-up resistor on the Pi
def is_done_button_pressed():
  return not GPIO.input(DONE_BUTTON_PIN_NUMBER)

def main():
  # -- keyboard setup --
  
  keyboard.on_press(process_key_press)
  keyboard.on_release_key('shift', process_shift_release)
  
  # -- GPIO setup --
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup(LASER_RELAY_PIN_NUMBER, GPIO.OUT, initial=GPIO.LOW)
  GPIO.setup(DONE_BUTTON_PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP) # enable Pi's built-in pull-up resistor for this pin
  
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
      
      # if a user just finished using the laser cutter ...
      if laser_just_finished_normally:
        time.sleep(2)
        # ... wait for the user to remove their card
        lcd.display_string("please remove", 1)
        lcd.display_string("your RamCard", 2)
        time.sleep(5)
        
        laser_just_finished_normally = False
        continue
      
      uid = reader.read_id_no_block()
      
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
      
      # if the DONE button is pressed
      if is_done_button_pressed():
        # ... and an admin has scanned their card ...
        if row and db._is_admin(row):
          # TODO: enter a loop here so admin does not have to re-scan their card
          #  to add multiple users in one go?
          
          # ... wait until a different uid is scanned
          red.ChangeDutyCycle(100)
          blue.ChangeDutyCycle(100)
          green.ChangeDutyCycle(0)
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
            time.sleep(2)
            continue
          
          data, duplicate = db.get_row_from_uid(uid_to_add)
          if (data):
            existing_name = db._get_name(data)[:15]
            lcd.display_list_of_strings(["update entry for", "%s?" % existing_name, "press and hold", "DONE to confirm"])
            
            lcd.display_string(existing_name, 1)
            if not is_done_button_pressed():
              lcd.display_string("entry unchanged", 2)
              time.sleep(2)
              continue
            
            lcd.display_string("will be updated", 2)
            time.sleep(2)
          
          #  prompt the user to enter their name with the keyboard
          lcd.display_string("enter your name", 1)
          lcd.display_string("on the keyboard", 2)
          time.sleep(2)
          lcd.display_string("press enter key", 1)
          lcd.display_string("when done", 2)
          
          name_to_add = activate_keyboard_and_get_name(lcd)
          
          #  and add them to the database as a user
          #print("would have added a user with name %s, uid %d" % (name_to_add, uid_to_add))
          db.add_user(uid_to_add, name_to_add)
          
          lcd.display_list_of_strings(["added user", name_to_add[:16], "with uid", hex(uid_to_add)])
          
          continue
        
        elif row:
          lcd.display_string(db._get_name(row)[:16], 1)
          
        else:
          lcd.display_string("card uid:", 1)
        
        lcd.display_string(hex(uid), 2)
        time.sleep(2)
        continue
      
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
        if is_done_button_pressed():
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
          
          else:
            red.ChangeDutyCycle(100)
            green.ChangeDutyCycle(0)
            display_card_missing = False
            lcd.display_uid_not_recognized(clear = False, row = 1)
        
        # a card is not present or the card is not valid,
        #  so increment the number of times a check has not detected a valid card
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
