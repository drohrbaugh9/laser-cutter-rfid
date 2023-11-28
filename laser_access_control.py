#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # https://pypi.org/project/mfrc522/
import db_interface
import improved_lcd
import time
import keyboard # https://pypi.org/project/keyboard/

# timing constants
LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 20

# pin number constants
LASER_RELAY_PIN_NUMBER = 8
DONE_BUTTON_PIN_NUMBER = 10
RED_LED_PIN_NUMBER = 32
GREEN_LED_PIN_NUMBER = 33
BLUE_LED_PIN_NUMBER = 35

def GPIO_setup():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setwarnings(False)
  GPIO.setup(LASER_RELAY_PIN_NUMBER, GPIO.OUT, initial=GPIO.LOW)
  GPIO.setup(DONE_BUTTON_PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP) # enable Pi's built-in pull-up resistor for this pin
  
  GPIO.setup(RED_LED_PIN_NUMBER, GPIO.OUT);
  GPIO.setup(GREEN_LED_PIN_NUMBER, GPIO.OUT);
  GPIO.setup(BLUE_LED_PIN_NUMBER, GPIO.OUT);

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
  GPIO_setup()
  red = GPIO.PWM(RED_LED_PIN_NUMBER, 2); red.start(0)
  green = GPIO.PWM(GREEN_LED_PIN_NUMBER, 2); green.start(0)
  blue = GPIO.PWM(BLUE_LED_PIN_NUMBER, 2); blue.start(0)
  
  # -- rfid setup --
  reader = SimpleMFRC522()
  
  # connect to database
  #  use absolute path because when this script runs at boot (using /etc/rc.local),
  #  it is not launched from this folder that it is in
  db = db_interface.db_interface("/home/pi/senior_design_FA23/laser-cutter-rfid/prod.db")
  
  # -- LCD setup --
  lcd = improved_lcd.lcd()
  
  # status variable
  laser_just_finished_normally = False
  
  try:
    
    while True:
      
      # if a user just finished using the laser cutter ...
      if laser_just_finished_normally:
        time.sleep(2)
        # ... wait for the user to remove their card ...
        lcd.display_list_of_strings(["please remove", "your RamCard"], sleep_time=5)
        
        # ... and then go back to the top of this while loop
        laser_just_finished_normally = False
        continue
      
      uid = reader.read_id_no_block()
      
      # if no card is detected ...
      if not uid:
        # ... display the idle message, wait,
        #  and then go back to the top of this while loop
        blue.ChangeDutyCycle(100)
        red.ChangeDutyCycle(0)
        green.ChangeDutyCycle(0)
        lcd.display_list_of_strings(["scan your", "RamCard to use"], sleep_time=LASER_OFF_POLLING_RATE_SECONDS)
        continue
      
      row = db.get_row_from_uid(uid)
      
      # if the DONE button is pressed
      if is_done_button_pressed():
        # ... and an admin has scanned their card ...
        if row and row.is_admin():
          # TODO: enter a loop here so admin does not have to re-scan their card
          #  to add multiple users in one go?
          
          # ... wait until a different uid is scanned
          red.ChangeDutyCycle(100)
          blue.ChangeDutyCycle(100)
          green.ChangeDutyCycle(0)
          lcd.display_list_of_strings(["adding a user!", "scan new RamCard"], sleep_time=5)
          
          uid_to_add = reader.read_id_no_block()
          if not uid_to_add: uid_to_add = reader.read_id_no_block()
          
          if not uid_to_add:
            lcd.display_list_of_strings(["no card detected", "admin, re-scan", "your RamCard"])
            continue
          
          data = db.get_row_from_uid(uid_to_add)
          if (data):
            existing_name = data.get_name()[:15]
            lcd.display_list_of_strings(["update entry for", "%s?" % existing_name, "press and hold", "DONE to confirm"])
            
            lcd.display_string(existing_name, 1)
            if not is_done_button_pressed():
              lcd.display_string("entry unchanged", 2)
              time.sleep(2)
              continue
            
            lcd.display_string("will be updated", 2)
            time.sleep(2)
          
          # user types in their name on the keyboard
          name_to_add = activate_keyboard_and_get_name(lcd)
          
          # add them to the database as a user
          db.add_user(uid_to_add, name_to_add)
          
          lcd.display_list_of_strings(["added user", name_to_add, "with uid", hex(uid_to_add)], display_last_16=False)
          
          continue
        
        elif row:
          lcd.display_string(row.get_name(), 1, display_last_16=False)
          
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
        lcd.display_list_of_strings("card", lcd.NOT_RECOGNIZED)
        lcd.clear()
        continue
      
      # this uid is in the database,
      #  so get corresponding name from uid and display it
      name = row.get_name()
      lcd.display_string(name, 1)
      
      # if this user is not authorized to use the laser
      #  (i.e. if their acces has expired) ...
      if not db._check_uid(row):
        # ... indicate that this user is not authorized
        # and then go back to the top of this while loop
        red.ChangeDutyCycle(100)
        blue.ChangeDutyCycle(0)
        lcd.display_string(lcd.NOT_AUTHORIZED, 2)
        time.sleep(2)
        lcd.clear()
        continue
      
      # this user is authorized, so turn on the laser
      lcd.display_string(lcd.AUTHORIZED, 2)
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
          #lcd.clear()
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
          lcd.clear()
          break
        
        # begin checking that a card is still present
        uid = reader.read_id_no_block()
        if not uid: uid = reader.read_id_no_block() # try again immediately if first read failed
        
        # if a card is present, check it against the database
        if uid:
          
          if uid == current_user_uid:
            times_card_missing = 0
            green.ChangeDutyCycle(100)
            red.ChangeDutyCycle(0)
            lcd.display_string(name, 1)
            lcd.display_string(lcd.AUTHORIZED, 2)
            continue
          
          row = db.get_row_from_uid(uid)
          
          if row:
            name = row.get_name()
            lcd.display_string(name, 1)
            
            # if the new uid is authorized,
            #  update LED and LCD and go back to the top of this inner while loop
            if db._check_uid(row):
              current_user_uid = uid
              times_card_missing = 0
              green.ChangeDutyCycle(100)
              red.ChangeDutyCycle(0)
              display_string(self.AUTHORIZED, 2)
              continue
            
            red.ChangeDutyCycle(100)
            green.ChangeDutyCycle(0)
            display_card_missing = False
            lcd.display_string(lcd.NOT_AUTHORIZED, 1)
          
          else:
            red.ChangeDutyCycle(100)
            green.ChangeDutyCycle(0)
            display_card_missing = False
            lcd.display_string(lcd.NOT_RECOGNIZED, 1)
        
        # a card is not present or the card is not valid,
        #  so increment the number of times a check has not detected a valid card
        times_card_missing += 1
        
        # alert the user that they need to return their card to the reader
        #  and update how much time they have left to do so
        if display_card_missing:
          lcd.display_string("card missing!", 1)
          red.ChangeDutyCycle(50) # blink at 2 Hz
          green.ChangeDutyCycle(0)
        time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
        lcd.display_string(time_str, 2)
  
  # if this program errors out,
  #  "turn off" the lcd and close the connection to the database
  #  before exiting
  finally:
    lcd.clear()
    lcd.backlight(0)
    db.close()
    # TODO print error for debugging purposes?

# ---------- keyboard handling stuff ---------

shift_pressed = False
accepting_keyboard_input = False

shift_chars = {'1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')', '-':'_', '=':'+', '\\':'|', '`':'~', '[':'{', ']':'}', ';':':', '\'':'"', ',':'<', '.':'>', '/':'?'}

def activate_keyboard_and_get_name(lcd):
  global name_from_keyboard, keyboard_done, accepting_keyboard_input
  
  name_from_keyboard = ""
  keyboard_done = False
  accepting_keyboard_input = True
  
  #  prompt the user to enter their name with the keyboard
  lcd.display_list_of_strings(["enter your name", "on the keyboard", "press enter key", "when done"])
  lcd.clear()
  
  while not keyboard_done:
    lcd.display_string(name_from_keyboard, 1)
    time.sleep(0.25)
  
  accepting_keyboard_input = False
  
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
      if event.name in shift_chars.keys():
        name_from_keyboard += shift_chars[event.name]
      else:
        name_from_keyboard += event.name.upper()
    else:
      name_from_keyboard += event.name

def process_shift_release(event):
  global shift_pressed
  
  shift_pressed = False

# ---------- end keyboard handling stuff -----

if __name__ == "__main__":
  main()
