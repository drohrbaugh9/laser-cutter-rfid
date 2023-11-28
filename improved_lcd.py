import RPi_I2C_driver as lcd_driver # https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

import time

class lcd(lcd_driver.lcd):
  
  NOT_RECOGNIZED = "not recognized"
  NOT_AUTHORIZED = "not authorized"
  AUTHORIZED =     "AUTHORIZED"
  
  def __init__(self):
    super().__init__() # call original class constructor, then do custom setup
    self.setup()
  
  def setup(self):
    self.clear()
    self.backlight(1)
  
  def clear(self):
    self.lcd_clear()
  
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
