import keyboard
import time
import RPi_I2C_driver as lcd_driver

def my_callback(event):
  global name, current_letter
  
  if event.name == 'up':
    current_letter -= 1
    if current_letter < ord('A'):
      current_letter = ord('Z')
    #print(chr(current_letter), end=' ')
  
  if event.name == 'down':
    current_letter += 1
    if current_letter > ord('Z'):
      current_letter = ord('A')
    #print(chr(current_letter), end=' ')
  
  if event.name == 'enter':
    name += chr(current_letter)
  
  if event.name == 'esc':
    print(name)

def main():
  global name, current_letter
  
  name = ""
  current_letter = 65
  
  lcd = my_lcd()
  lcd.setup()

  keyboard.on_press(my_callback)
  
  display_current = False

  while(True):
    name_to_display = name
    if display_current: name_to_display += chr(current_letter)
    display_current = not display_current
    
    lcd.display_string(name_to_display, 1)
    #lcd.display_string((len(name) * ' ') + '^', 2)
    
    time.sleep(0.25)

class my_lcd(lcd_driver.lcd):
  
  def setup(self):
    self.lcd_clear()
    self.backlight(1)
  
  def display_string(self, short_str, row):
    padded_str = short_str + (' ' * (16 - len(short_str)))
    self.lcd_display_string(padded_str, row)

if __name__ == "__main__":
  main()