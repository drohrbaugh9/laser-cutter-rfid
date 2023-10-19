import sqlite3

NAME_COLUMN = "fullname"
ADMIN_COLUMN = "is_admin"

db = -1
db_cursor = -1
current_db = "not connected"

def connect_to_db(db_name: str):
  global db, db_cursor, current_db
  
  db = sqlite3.connect(db_name)
  db_cursor = db.cursor()
  
  current_db = db_name

def __add_entry(ramcard_uid: int, fullname: str, is_admin: int):
  global db, db_cursor
  
  db_cursor.execute("INSERT INTO users VALUES (?, ?, ?)", [ramcard_uid, fullname, is_admin])
  
  db.commit()

def add_user(ramcard_uid: int, fullname: str):
  __add_entry(ramcard_uid, fullname, 0)

def add_admin(ramcard_uid: int, fullname: str):
  __add_entry(ramcard_uid, fullname, 1)

def get_row_from_uid(uid: int):
  global db_cursor
  res = db_cursor.execute("SELECT * FROM users WHERE ramcard_uid = ?", [uid])
  
  row = res.fetchone()
  duplicate = res.fetchone()
  
  found_duplicate = False
  if duplicate: found_duplicate = True
  
  return row, found_duplicate

def get_name(uid: int):
  name, duplicate = get_items_from_uid(uid, NAME_COLUMN)
  
  return name

def check_uid(uid: int):
  if get_name(uid): return True
  
  return False

def is_admin(uid: int):
  admin, duplicate = get_items_from_uid(uid, ADMIN_COLUMN)
  
  if admin: return True
  
  return False

def close():
  db.close()