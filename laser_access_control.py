#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # https://pypi.org/project/mfrc522/
import db_interface
import improved_lcd
import time
import keyboard # https://pypi.org/project/keyboard/

# TODO move constants to laser_access_control class?

# timing constants
LASER_OFF_POLLING_RATE_SECONDS = 0.5
LASER_ON_POLLING_RATE_SECONDS  = 1
LASER_ON_GRACE_PERIOD_SECONDS  = 20
ADD_USER_TIMEOUT_SECONDS       = 30

# pin number constants
LASER_RELAY_PIN_NUMBER = 8
DONE_BUTTON_PIN_NUMBER = 10
RED_LED_PIN_NUMBER = 32
GREEN_LED_PIN_NUMBER = 33
BLUE_LED_PIN_NUMBER = 35

shift_chars = {'1':'!', '2':'@', '3':'#', '4':'$', '5':'%', '6':'^', '7':'&', '8':'*', '9':'(', '0':')', '-':'_', '=':'+', '\\':'|', '`':'~', '[':'{', ']':'}', ';':':', '\'':'"', ',':'<', '.':'>', '/':'?'}

# ---------- keyboard handling stuff ---------

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

# standardize checking done button
#  since the button is connected between the input pin and ground
#  when pressed it will pull the pin LOW
#  when not pressed, the pin is pulled high by a built-in pull-up resistor on the Pi
def is_done_button_pressed(self):
  return not GPIO.input(DONE_BUTTON_PIN_NUMBER)

class laser_access_control:
  
  def __init__(self):
    self.setup()
  
  def setup(self):
    global shift_pressed, accepting_keyboard_input
    
    shift_pressed = False
    accepting_keyboard_input = False
    
    # -- keyboard setup --
    keyboard.on_press(process_key_press)
    keyboard.on_release_key('shift', process_shift_release)
    
    # -- GPIO setup --
    self.GPIO_setup()
    
    # -- rfid setup --
    self.reader = SimpleMFRC522()
    
    # connect to database
    #  use absolute path because when this script runs at boot (using /etc/rc.local),
    #  it is not launched from this folder that it is in
    self.db = db_interface.db_interface("/home/pi/senior_design_FA23/laser-cutter-rfid/prod.db")
    
    # -- LCD setup --
    self.lcd = improved_lcd.lcd()
  
  def GPIO_setup(self):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(LASER_RELAY_PIN_NUMBER, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(DONE_BUTTON_PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP) # enable Pi's built-in pull-up resistor for this pin
    
    GPIO.setup(RED_LED_PIN_NUMBER, GPIO.OUT);
    GPIO.setup(GREEN_LED_PIN_NUMBER, GPIO.OUT);
    GPIO.setup(BLUE_LED_PIN_NUMBER, GPIO.OUT);
    
    self.red = GPIO.PWM(RED_LED_PIN_NUMBER, 2);
    self.green = GPIO.PWM(GREEN_LED_PIN_NUMBER, 2);
    self.blue = GPIO.PWM(BLUE_LED_PIN_NUMBER, 2);
    
    self.green.start(0)
    self.red.start(0)
    self.blue.start(0)
  
  # params should range from 0 - 100, inclusive
  def set_LED(self, r, g, b):
    self.red.ChangeDutyCycle(r)
    self.green.ChangeDutyCycle(g)
    self.blue.ChangeDutyCycle(b)
  
  def add_user_mode(self):
    # TODO: enter a loop here so admin does not have to re-scan their card
    #  to add multiple users in one go?
    
    # indicate that the system is adding users
    self.set_LED(100, 0, 100) # purple
    self.lcd.display_list_of_strings(["adding a user!", "scan new RamCard"], sleep_time=5)
    
    while True:
      uid_to_add = self.reader.read_id_no_block()
      
      # if a card is not read within ADD_USER_TIMEOUT_SECONDS,
      #  exit add user mode
      timeout = ADD_USER_TIMEOUT_SECONDS
      while not uid_to_add:
        time.sleep(1)
        uid_to_add = self.reader.read_id_no_block()
        
        timeout -= 1
        if timeout == 0: return
      
      data = self.db.get_row_from_uid(uid_to_add)
      # check if there is an existing entry with this uid
      if (data):
        existing_name = data.get_name()[:15]
        self.lcd.display_list_of_strings(["update entry for", "%s?" % existing_name, "press and hold", "DONE to confirm"])
        
        self.lcd.display_string(existing_name, 1)
        if not is_done_button_pressed():
          self.lcd.display_string("entry unchanged", 2)
          time.sleep(2)
          return
        
        # only change the entry if the DONE button was pressed
        self.lcd.display_string("will be updated", 2)
        time.sleep(2)
      
      # user types in their name on the keyboard
      name_to_add = self.activate_keyboard_and_get_name()
      
      # add them to the database as a user
      self.db.add_user(uid_to_add, name_to_add)
      
      self.lcd.display_list_of_strings(["added user", name_to_add, "with uid", hex(uid_to_add)], display_last_16=False)
      
      self.lcd.display_list_of_strings(["scan next", "RamCard", "or wait", "%d seconds" % ADD_USER_TIMEOUT_SECONDS], "to exit add mode")
  
  def main(self):
    while True:
      
      # if a user just finished using the laser cutter ...
      if self.laser_just_finished_normally:
        
        # ... and then go back to the top of this while loop
        self.laser_just_finished_normally = False
        continue
      
      uid = self.reader.read_id_no_block()
      
      # if no card is detected ...
      if not uid:
        # ... display the idle message, wait,
        #  and then go back to the top of this while loop
        self.set_LED(0, 0, 100) # blue
        self.lcd.display_list_of_strings(["scan your", "RamCard to use"], sleep_time=LASER_OFF_POLLING_RATE_SECONDS)
        continue
      
      row = self.db.get_row_from_uid(uid)
      
      # if the DONE button is pressed
      if is_done_button_pressed():
        # ... and an admin has scanned their card ...
        if row and row.is_admin():
          
          # ... enter a mode where multiple users can be added in succession
          #  without an admin re-scanning their card ...
          self.add_user_mode()
          
          # ... then go back to the top of this while loop
          continue
        
        # if the card that was scanned is in the database,
        #  display the corresponding name
        elif row:
          self.lcd.display_string(row.get_name(), 1, display_last_16=False)
        
        # otherwise, display this generic text
        else:
          self.lcd.display_string("card uid:", 1)
        
        # and with the first LCD row set up,
        #  display the uid on the second row
        self.lcd.display_string(hex(uid), 2)
        time.sleep(2)
        continue
      
      # if the uid is not in the database ...
      if not row:
        # ... indicate that the card is not recognized
        #  and then go back to the top of this while loop
        self.set_LED(100, 0, 0) # red
        self.lcd.display_list_of_strings("card", self.lcd.NOT_RECOGNIZED)
        self.lcd.clear()
        continue
      
      # this uid is in the database,
      #  so get corresponding name from uid and display it
      name = row.get_name()
      self.lcd.display_string(name, 1)
      
      # if this user is not authorized to use the laser
      #  (i.e. if their acces has expired) ...
      if not self.db._check_uid(row):
        # ... indicate that this user is not authorized
        # and then go back to the top of this while loop
        self.set_LED(100, 0, 0) # red
        self.lcd.display_string(self.lcd.NOT_AUTHORIZED, 2)
        time.sleep(2)
        self.lcd.clear()
        continue
      
      # this user is authorized, so turn on the laser
      self.lcd.display_string(self.lcd.AUTHORIZED, 2)
      self.set_LED(0, 100, 0) # green
      GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.HIGH)
      
      times_card_missing = 0
      max_times_card_missing = LASER_ON_GRACE_PERIOD_SECONDS / LASER_ON_POLLING_RATE_SECONDS
      current_user_uid = uid
      
      while True:
        time.sleep(LASER_ON_POLLING_RATE_SECONDS)
        
        display_card_missing = True
        
        # if the user is pressing the DONE button ...
        if is_done_button_pressed():
          # ... turn off the laser ...
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW)
          self.lcd.display_list_of_strings([name, "DONE"], sleep_time=2)
          # ... wait for the user to remove their card ...
          self.lcd.display_list_of_strings(["please remove", "your RamCard"], sleep_time=5)
          # ... and break out of this inner while loop
          break
        
        # if the card is missing for too long, shut off the laser
        #  and break out of this inner while loop
        if times_card_missing >= max_times_card_missing:
          self.lcd.display_string("", 1)
          self.lcd.display_string("time up!", 2)
          GPIO.output(LASER_RELAY_PIN_NUMBER, GPIO.LOW) # laser and chiller OFF
          self.set_LED(100, 0, 0) # red
          time.sleep(2)
          self.lcd.clear()
          break
        
        # begin checking that a card is still present
        uid = self.reader.read_id_no_block()
        if not uid: uid = self.reader.read_id_no_block() # try again immediately if first read failed
        
        # if a card is present, check it against the database
        if uid:
          
          if uid == current_user_uid:
            times_card_missing = 0
            self.set_LED(0, 100, 0) # green
            self.lcd.display_string(name, 1)
            self.lcd.display_string(self.lcd.AUTHORIZED, 2)
            continue
          
          row = self.db.get_row_from_uid(uid)
          
          if row:
            name = row.get_name()
            self.lcd.display_string(name, 1)
            
            # if the new uid is authorized,
            #  update LED and LCD and go back to the top of this inner while loop
            if self.db._check_uid(row):
              current_user_uid = uid
              times_card_missing = 0
              self.set_LED(0, 100, 0) # green
              self.lcd.display_string(self.lcd.AUTHORIZED, 2)
              continue
            
            self.set_LED(100, 0, 0) # red
            display_card_missing = False
            self.lcd.display_string(self.lcd.NOT_AUTHORIZED, 1)
          
          else:
            self.set_LED(100, 0, 0) # red
            display_card_missing = False
            self.lcd.display_string(self.lcd.NOT_RECOGNIZED, 1)
        
        # a card is not present or the card is not valid,
        #  so increment the number of times a check has not detected a valid card
        times_card_missing += 1
        
        # alert the user that they need to return their card to the reader
        #  and update how much time they have left to do so
        if display_card_missing:
          self.lcd.display_string("card missing!", 1)
          self.set_LED(50, 0, 0) # blink red at 2 Hz
        time_str = "%d sec to return" % ((max_times_card_missing - times_card_missing) * LASER_ON_POLLING_RATE_SECONDS)
        self.lcd.display_string(time_str, 2)
  
  def cleanup(self):
    # if this program errors out,
    #  "turn off" the lcd and LED and close the connection to the database
    #  before exiting
    finally:
      self.lcd.clear()
      self.lcd.backlight(0)
      self.set_LED(0, 0, 0)
      self.db.close()
      # TODO print error for debugging purposes?
  
  # TODO move this method definition? seems logical to have cleanup() be the last definition
  def activate_keyboard_and_get_name(self):
    global name_from_keyboard, keyboard_done, accepting_keyboard_input
    
    name_from_keyboard = ""
    keyboard_done = False
    accepting_keyboard_input = True
    
    #  prompt the user to enter their name with the keyboard
    self.lcd.display_list_of_strings(["enter your name", "on the keyboard", "press enter key", "when done"])
    self.lcd.clear()
    
    while not keyboard_done:
      self.lcd.display_string(name_from_keyboard, 1)
      time.sleep(0.25)
    
    accepting_keyboard_input = False
    
    return name_from_keyboard
  
if __name__ == "__main__":
  access_controller = laser_access_control()
  
  try:
    access_controller.main()
  except:
    access_controller.cleanup()
