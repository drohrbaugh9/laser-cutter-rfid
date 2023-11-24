import sqlite3
import datetime

# TODO extend dict instead of just having a dict?
#  could be useful when sqlite requires a dict or dict subclass
class user_entry:
  
  def __init__(self, uid: int, name: str, is_admin: int, expiration_date, duplicate: bool):
    self.data = {'ramcard_uid': uid, 'fullname': name, 'is_admin': is_admin, 'expiration_date': expiration_date, 'duplicate': duplicate}
  
  def get_uid(self):
    return self.data['ramcard_uid']
  
  def get_name(self):
    return self.data['fullname']
  
  def is_admin(self):
    if self.data['is_admin'] == 1:
      return True
    
    return False
  
  def is_expired(self):
    now = int(datetime.datetime.today().timestamp())
    expiration = self.data['expiration_date']
    
    if now > expiration: return True
    
    return False
  
  def has_duplicate(self):
    return self.data['duplicate']

class db_interface:

  USER_ADD_ACTION = "ADD"
  USER_UPDATE_ACTION = "UPDATE"
  USER_DELETE_ACTION = "DELETE"
  USER_REMOVEEXPIRED_ACTION = "REMOVE EXPIRED"
  
  def __init__(self, db_name: str):
    self.connect_to_db(db_name)

  def connect_to_db(self, db_name: str):
    self._db = sqlite3.connect(db_name)
    
    if not self._db:
      raise "could not connect to database %s" % db_name
    
    self._db_cursor = self._db.cursor()
    
    self.current_db = db_name
  
  def delete_entry(self, uid: int):
    self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [uid])
    
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_DELETE_ACTION, uid])
    
    self._db.commit()

  def _add_entry(self, ramcard_uid: int, fullname: str, is_admin: int):
    action = self.USER_ADD_ACTION
    
    res = self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [ramcard_uid])
    
    if res.rowcount > 0:
      action = self.USER_UPDATE_ACTION
    
    self._db_cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", [ramcard_uid, fullname, is_admin, calculate_expiration_date_timestamp()])
    
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), action, ramcard_uid])
    
    self._db.commit()

  def add_user(self, ramcard_uid: int, fullname: str):
    self._add_entry(ramcard_uid, fullname, 0)

  def add_admin(self, ramcard_uid: int, fullname: str):
    self._add_entry(ramcard_uid, fullname, 1)

  def get_row_from_uid(self, uid: int):
    res = self._db_cursor.execute("SELECT * FROM users WHERE ramcard_uid = ?", [uid])
    
    row = res.fetchone()
    
    if not row:
      return None
    
    duplicate = res.fetchone()
    found_duplicate = False
    if duplicate: found_duplicate = True
    
    return user_entry(row[0], row[1], row[2], row[3], found_duplicate)
  
  def check_uid(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return self._check_uid(data)
  
  def _check_uid(self, row):
    
    if not row:
      return False
    
    if row.is_admin() or not row.is_expired():
      self.log_unlock(row.get_uid())
      return True
    
    return False
  
  # only remove expired users, leave expired admins
  def remove_expired_users(self):
    res = self._db_cursor.execute("DELETE FROM users WHERE is_admin != 1 AND expiration_date < ?", [int(datetime.datetime.today().timestamp())])
    
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_REMOVEEXPIRED_ACTION, res.rowcount])
    
    self._db.commit()
  
  # remove all expired entries, admins included
  def remove_expired_entries(self):
    res = self._db_cursor.execute("DELETE FROM users WHERE expiration_date < ?", [int(datetime.datetime.today().timestamp())])
    
    self._db_cursor.execute("INSERT INTO users_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), self.USER_REMOVEEXPIRED_ACTION, res.rowcount])
    
    self._db.commit()
  
  def close(self):
    self._db.close()
  
  def log_unlock(self, uid):
    self._db_cursor.execute("INSERT INTO laser_log VALUES (?, ?, ?)", [int(datetime.datetime.today().timestamp()), "UNLOCK", uid])
    self._db.commit()
  
  ##### GET METHODS #####
  
  def get_name(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.get_name()
  
  ##### IS METHODS #####
  
  def is_admin(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.is_admin()
  
  def is_expired(self, uid: int):
    data = self.get_row_from_uid(uid)
    
    return data.is_expired()

# TODO change this to be something like
#  - end of the current semester
#  - end or current year
#  - one of the above or 3 months, whichever is longer
def calculate_expiration_date_timestamp():
  now = datetime.datetime.today()
  six_months = datetime.timedelta(days = 180)
  return int((now + six_months).timestamp())

def print_users_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM users")
  print(res.fetchall())
  db.close()

def print_users_log_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM users_log")
  print(res.fetchall())
  db.close()

def print_laser_log_table(db_name):
  db = sqlite3.connect(db_name)
  res = db.cursor().execute("SELECT * FROM laser_log")
  print(res.fetchall())
  db.close()