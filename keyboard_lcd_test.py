import keyboard
import time

DEV = False

def do_nothing(event):
  pass

def my_callback(event):
  global name, name_done
  
  if event.name == 'enter':
    name_done = True
    return
  
  elif event.name == 'backspace':
    name = name[:-1]
  
  elif event.name == 'delete':
    name = ''
  
  elif event.name == 'space':
    name += ' '
  
  elif len(event.name) == 1:
    name += event.name

def main():
  global name, name_done
  
  name = ""
  name_done = False
  
  lcd = -1
  if DEV:
    lcd = lcd_linux_terminal_emulator()
  else:
    lcd = my_lcd()
  
  lcd.setup()

  keyboard.on_press(my_callback)
  
  display_current = False

  while not name_done:
    lcd.display_string(name, 1)
    time.sleep(0.25)
  
  keyboard.on_press(do_nothing)

#'''
import RPi_I2C_driver as lcd_driver

class my_lcd(lcd_driver.lcd):
  
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
#'''

class lcd_linux_terminal_emulator:
  
  def setup(self):
    print("\x1b[0;0H\
 ________________  \n\
|                | \n\
|                | \n\
 ````````````````  ", flush=True)
  
  def display_string(self, string, row):
    formatted_str = string
    if len(string) < 16:
      formatted_str = string + (' ' * (16 - len(string)))
    elif len(string) > 16:
      formatted_str = string[-16:]
    print("\x1b[%s;2H%s" % (row + 1, formatted_str), flush=True)

if __name__ == "__main__":
  main()