import RPi_I2C_driver as lcd_driver # https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

import time

class lcd(lcd_driver.lcd):
  
  def __init__(self):
    self.setup()
  
  def setup(self):
    self.lcd_clear()
    self.backlight(1)
  
  def display_string(self, string, row, display_last_16 = True, align_left = True):
    formatted_str = string
    if len(string) < 16:
      padding = (' ' * (16 - len(string)))
      if align_left:
        formatted_str = string + padding
      else:
        formatted_str = padding + string
    elif len(string) > 16 and display_last_16:
        formatted_str = string[-16:]
    self.lcd_display_string(formatted_str, row)
  
  def display_strings(self, string_with_newlines, sleep_time = 2, display_last_16 = True, align_left = True):
    list_of_strings = string_with_newlines.split('\n')
    self.display_list_of_strings(list_of_strings, sleep_time, display_last_16, align_left)
  
  def display_list_of_strings(self, strings, sleep_time = 2, display_last_16 = True, align_left = True):
    for i in range(1, len(strings)):
      self.display_string(strings[i -1], 1, display_last_16, align_left)
      self.display_string(strings[i], 2, display_last_16, align_left)
      time.sleep(sleep_time)
  
  def display_uid_not_recognized(self, clear = True, row = 2):
    if row == 2:
      self.display_string("card", 1)
      self.display_string("not recognized", 2)
    else:
      self.display_string("not recognized", 1)
    
    if clear:
      time.sleep(2)
      self.lcd_clear()
  
  def display_uid_not_authorized(self, clear = True, row = 2):
    self.display_string("not authorized", row)
    
    if clear:
      time.sleep(2)
      self.lcd_clear()
  
  def display_uid_authorized(self):
    self.display_string("AUTHORIZED", 2)