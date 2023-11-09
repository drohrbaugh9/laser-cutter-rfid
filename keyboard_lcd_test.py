import keyboard
import time

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', ' ']

def my_callback(event):
  global name, current_letter
  
  if event.name == 'up':
    current_letter -= 1
    if current_letter < 0:
      current_letter = len(letters) - 1
  
  if event.name == 'down':
    current_letter += 1
    if current_letter >= len(letters):
      current_letter = 0
  
  if event.name == 'enter':
    name += letters[current_letter]
  
  if event.name == 'esc':
    print(name)

def main():
  global name, current_letter
  
  name = ""
  current_letter = 0
  
  #lcd = my_lcd()
  lcd = lcd_linux_terminal_emulator()
  lcd.setup()

  keyboard.on_press(my_callback)
  
  display_current = False

  while(True):
    name_to_display = name
    if display_current: name_to_display += letters[current_letter]
    #display_current = not display_current
    
    lcd.display_string(name_to_display, 1)
    cursor_letter = letters[current_letter]
    if cursor_letter == ' ': cursor_letter = '_'
    lcd.display_string((len(name) * ' ') + cursor_letter, 2)
    
    time.sleep(0.25)

'''
import RPi_I2C_driver as lcd_driver

class my_lcd(lcd_driver.lcd):
  
  def setup(self):
    self.lcd_clear()
    self.backlight(1)
  
  def display_string(self, short_str, row):
    padded_str = short_str + (' ' * (16 - len(short_str)))
    self.lcd_display_string(padded_str, row)
'''

class lcd_linux_terminal_emulator:
  
  def setup(self):
    print("\x1b[0;0H\
 ________________  \n\
|                | \n\
|                | \n\
 ````````````````  ", flush=True)
  
  def display_string(self, short_str, row):
    padded_str = short_str + (' ' * (16 - len(short_str)))
    print("\x1b[%s;2H%s" % (row + 1, padded_str), flush=True)

if __name__ == "__main__":
  main()