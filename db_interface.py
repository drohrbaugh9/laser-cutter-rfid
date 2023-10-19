import sqlite3
import datetime

class db_interface:
  
  def __init__(self, db_name: str):
    self.connect_to_db(db_name)

  def connect_to_db(self, db_name: str):
    self._db = sqlite3.connect(db_name)
    
    if not self._db:
      raise "could not connect to database %s" % db_name
    
    self._db_cursor = self._db.cursor()
    
    self.current_db = db_name
  
  def _delete_entry(self, uid: int):
    self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [uid])
  
  def delete_entry(self, uid: int):
    self._delete_entry(uid)
    self._db.commit()

  def _add_entry(self, ramcard_uid: int, fullname: str, is_admin: int):
    self._db_cursor.execute("DELETE FROM users WHERE ramcard_uid = ?", [ramcard_uid])
    self._db_cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", [ramcard_uid, fullname, is_admin, calculate_expiration_date_timestamp()])
    
    self._db.commit()

  def add_user(self, ramcard_uid: int, fullname: str):
    self._add_entry(ramcard_uid, fullname, 0)

  def add_admin(self, ramcard_uid: int, fullname: str):
    self._add_entry(ramcard_uid, fullname, 1)

  def get_row_from_uid(self, uid: int):
    res = self._db_cursor.execute("SELECT * FROM users WHERE ramcard_uid = ?", [uid])
    
    row = res.fetchone()
    duplicate = res.fetchone()
    
    found_duplicate = False
    if duplicate: found_duplicate = True
    
    return row, found_duplicate
  
  def check_uid(self, uid: int):
    data, duplicate = self.get_row_from_uid(uid)
    
    return self._check_uid(data)
  
  def _check_uid(self, row: tuple):
    
    if not row:
      #print('uid %d not found' % uid)
      return False
    
    if self._is_admin(row):
      #print('uid %d is admin, check passed' % uid)
      return True
    
    if not self._is_expired(row):
      #print('expiration date for uid %d is in the future, check passed' % uid)
      return True
    
    return False
  
  # only remove expired users, leave expired admins
  def remove_expired_users(self):
    self._db_cursor.execute("DELETE FROM users WHERE is_admin = 0 AND expiration_date < ?", [int(datetime.datetime.today().timestamp())])
  
  # remove all expired entries, admins included
  def remove_expired_entries(self):
    self._db_cursor.execute("DELETE FROM users WHERE expiration_date < ?", [int(datetime.datetime.today().timestamp())])
  
  def close(self):
    self._db.close()
  
  ##### GET METHODS #####
  
  def get_name(self, uid: int):
    data, duplicate = self.get_row_from_uid(uid)
    
    return self._get_name(data)
  
  def _get_name(self, row: tuple):
    return row[1]
  
  def _get_uid(self, row: tuple):
    return row[0]
  
  ##### IS METHODS #####
  
  def is_admin(self, uid: int):
    data, duplicate = self.get_row_from_uid(uid)
    
    return self._is_admin(data)
  
  def is_expired(self, uid: int):
    data, duplicate = self.get_row_from_uid(uid)
    
    return self._is_expired(data)
  
  def _is_admin(self, row: tuple):
    if row[2] == 1: return True
    
    return False
  
  def _is_expired(self, row: tuple):
    now = int(datetime.datetime.today().timestamp())
    expiration = row[3]
    
    if now > expiration: return True
    
    return False

def calculate_expiration_date_timestamp():
  now = datetime.datetime.today()
  six_months = datetime.timedelta(days = 180)
  return int((now + six_months).timestamp())