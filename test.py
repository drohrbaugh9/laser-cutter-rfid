import setup_test_db
import db_interface

class test_db_interface(db_interface.db_interface):
  
  def test_get_row_from_uid(self):
    row = self.get_row_from_uid(86080826340)
    
    assert(row.get_uid() == 86080826340)
    assert(row.get_name() == 'Test User')
    assert(row.is_admin() == False)
    assert(row.has_duplicate() == False)

  def test_get_row_from_uid_duplicate(self):
    row = self.get_row_from_uid(151493474601)
    
    assert(row.get_uid() == 151493474601)
    assert(row.get_name() == 'David Rohrbaugh')
    assert(row.is_admin() == True)
    assert(row.has_duplicate() == True)
  
  def test_get_name(self):
    assert(self.get_name(151493474601) == "David Rohrbaugh")
    assert(self.get_name(86080826340) == "Test User")
  
  def test_check_uid(self):
    assert(self.check_uid(151493474601) == True) # admin, not expired
    assert(self.check_uid(86080826340) == True) # test user
    assert(self.check_uid(123456789012) == False) # expired user
    assert(self.check_uid(98765432109) == True) # expired admin
    assert(self.check_uid(5) == False) # no entry for uid '5' in db
    assert(self.check_uid(-1) == False) # no entry for uid '-1' in db
    assert(self.check_uid("151493474601") == False) # string version of a good uid
    assert(self.check_uid("a string") == False)
  
  def test_is_admin(self):
    assert(self.is_admin(151493474601) == True)
    assert(self.is_admin(86080826340) == False)

  def test_add_entry(self):
    self._add_entry(0x010203, "test_add_entry", 2)
    
    row = self.get_row_from_uid(0x010203)
    
    assert(row.get_uid() == 0x010203)
    assert(row.get_name() == "test_add_entry")
    assert(row.is_admin() == False)
    assert(row.has_duplicate() == False)
  
  def test_log_add_entry(self):
    res = self._db_cursor.execute("SELECT * FROM users_log WHERE action = ?", [self.USER_ADD_ACTION])
    
    row = res.fetchone()
    
    assert(row[1] == self.USER_ADD_ACTION)
    assert(row[2] == 0x010203)
    
    duplicate = res.fetchone()
    
    assert(not duplicate)
  
  def test_add_user_sql_injection_drop_table(self):
    self.add_user(0xBADDA7A1, "test_sql_injection; DROP TABLE users --")
    
    row = self.get_row_from_uid(0xBADDA7A1)
    
    assert(row.get_uid() == 0xBADDA7A1)
    assert(row.get_name() == "test_sql_injection; DROP TABLE users --")
    assert(row.is_admin() == False)
    assert(row.has_duplicate() == False)
  
  # --- NOT ACTIVE ---
  # TODO: add assert statements
  def test_add_user_sql_injection_comment(self):
    self.add_user(0xBADDA7A2, "test_sql_injection --")
  
  def test_update_entry(self):
    self._add_entry(0x010203, "test_update_entry", 3)
    
    row = self.get_row_from_uid(0x010203)
    
    assert(row.get_uid() == 0x010203)
    assert(row.get_name() == "test_update_entry")
    assert(row.is_admin() == False)
    assert(row.has_duplicate() == False)
  
  def test_log_update_entry(self):
    res = self._db_cursor.execute("SELECT * FROM users_log WHERE action = ?", [self.USER_UPDATE_ACTION])
    
    row = res.fetchone()
    
    assert(row[1] == self.USER_UPDATE_ACTION)
    assert(row[2] == 0x010203)
    
    duplicate = res.fetchone()
    
    assert(not duplicate)
  
  def test_delete_entry(self):
    self.delete_entry(0x010203)
    
    assert(self.check_uid(0x010203) == False)
  
  def test_log_delete_entry(self):
    res = self._db_cursor.execute("SELECT * FROM users_log WHERE action = ?", [self.USER_DELETE_ACTION])
    
    row = res.fetchone()
    
    assert(row[1] == self.USER_DELETE_ACTION)
    assert(row[2] == 0x010203)
    
    duplicate = res.fetchone()
    
    assert(not duplicate)
  
  def test_duplicate_check_after_manual_delete(self):
    self._db_cursor.execute("DELETE FROM users WHERE fullname = ?", ['Duplicate Admin'])
    self._db.commit()
    
    row = self.get_row_from_uid(151493474601)
    
    assert(row.get_uid() == 151493474601)
    assert(row.get_name() == "David Rohrbaugh")
    assert(row.is_admin() == True)
    assert(row.has_duplicate() == False)
  
  def test_remove_expired_users(self):
    self.remove_expired_users()
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired User'])
    assert(len(res.fetchall()) == 0)
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired Admin'])
    assert(len(res.fetchall()) != 0)
  
  def test_log_remove_expired_users(self):
    res = self._db_cursor.execute("SELECT * FROM users_log WHERE action = ?", [self.USER_REMOVEEXPIRED_ACTION])
    
    row = res.fetchone()
    
    assert(row[1] == self.USER_REMOVEEXPIRED_ACTION)
    assert(row[2] == 1)
    
    duplicate = res.fetchone()
    assert(not duplicate)
  
  def test_remove_expired_entries(self):
    self.remove_expired_entries()
    
    # if test_remove_expired_users is not run, check that this test removed the expired user
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired User'])
    assert(len(res.fetchall()) == 0)
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired Admin'])
    assert(len(res.fetchall()) == 0)
  
  def test_log_remove_expired_entries(self):
    res = self._db_cursor.execute("SELECT * FROM users_log WHERE action = ?", [self.USER_REMOVEEXPIRED_ACTION])
    
    row = res.fetchone()
    
    assert(row[1] == self.USER_REMOVEEXPIRED_ACTION)
    assert(row[2] == 1)
    
    row = res.fetchone() # TODO if test_remove_expired_users is not run, there won't be another entry and these asserts will fail
    
    assert(row[1] == self.USER_REMOVEEXPIRED_ACTION)
    assert(row[2] == 1)
    
    duplicate = res.fetchone()
    assert(not duplicate)

def main():
  setup_test_db.setup()
  db = test_db_interface("test.db")
  
  db.test_get_row_from_uid()
  
  db.test_get_row_from_uid_duplicate()
  
  db.test_get_name()
  
  db.test_check_uid()
  
  db.test_is_admin()
  
  db.test_add_entry()
  
  db.test_log_add_entry()
  
  db.test_add_user_sql_injection_drop_table()
  
  #db.test_add_user_sql_injection_comment()
  
  db.test_update_entry()
  
  db.test_log_update_entry()
  
  db.test_delete_entry()
  
  db.test_duplicate_check_after_manual_delete()
  
  db.test_log_delete_entry()
  
  db.test_remove_expired_users()
  
  db.test_log_remove_expired_users()
  
  db.test_remove_expired_entries()
  
  db.test_log_remove_expired_entries()

if __name__ == "__main__":
  main()
  
  print('all tests passed')