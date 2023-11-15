import RPi_I2C_driver as lcd_driver # https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

import time

class lcd(lcd_driver.lcd):
  
  def setup(self):
    self.lcd_clear()
    self.backlight(1)
  
  def display_string(self, string, row):
    formatted_str = string
    if len(string) < 16:
      formatted_str = string + (' ' * (16 - len(string)))
    elif len(string) > 16:
      formatted_str = string[-16:]
    self.lcd_display_string(formatted_str, row)
  
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