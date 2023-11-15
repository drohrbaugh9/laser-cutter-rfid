import keyboard
import time

DEV = False

shift_pressed = False
accepting_keyboard_input = False

def process_key_press(event):
  global name, name_done, shift_pressed, accepting_keyboard_input
  
  if event.name == 'shift':
    shift_pressed = True
  
  if not accepting_keyboard_input:
    return
  
  if event.name == 'enter':
    name_done = True
    return
  
  if event.name == 'backspace':
    name = name[:-1]
  
  elif event.name == 'delete':
    name = ''
  
  elif event.name == 'space':
    name += ' '
  
  elif len(event.name) == 1:
    if shift_pressed:
      name += event.name.upper()
    else:
      name += event.name

def process_shift_release(event):
  global shift_pressed
  
  shift_pressed = False

def main():
  global name, name_done, accepting_keyboard_input
  
  name = ""
  name_done = False
  
  lcd = -1
  if DEV:
    lcd = lcd_linux_terminal_emulator()
  else:
    import improved_lcd
    lcd = improved_lcd.lcd()
  
  lcd.setup()
  
  keyboard.on_press(process_key_press)
  keyboard.on_release_key('shift', process_shift_release)
  
  while(True):
    accepting_keyboard_input = True
    
    while not name_done:
      lcd.display_string(name, 1)
      time.sleep(0.25)
    
    # soft reset
    accepting_keyboard_input = False
    lcd.lcd_clear()
    name_done = False
    name = ""
    time.sleep(5)

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
