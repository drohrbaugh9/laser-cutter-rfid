import setup_test_db
import db_interface

class test_db_interface(db_interface.db_interface):
  
  def test_get_row_from_uid(self):
    row, duplicate = self.get_row_from_uid(86080826340)
    
    assert(row[0] == 86080826340)
    assert(row[1] == 'Test User')
    assert(row[2] == 0)
    assert(duplicate == False)

  def test_get_row_from_uid_duplicate(self):
    row, duplicate = self.get_row_from_uid(151493474601)
    
    assert(row[0] == 151493474601)
    assert(row[1] == 'David Rohrbaugh')
    assert(row[2] == 1)
    assert(duplicate == True)
  
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
    
    row, duplicate = self.get_row_from_uid(0x010203)
    
    assert(row[0] == 0x010203)
    assert(row[1] == "test_add_entry")
    assert(row[2] == 2)
    assert(duplicate == False)
  
  def test_update_entry(self):
    self._add_entry(0x010203, "test_update_entry", 3)
    
    row, duplicate = self.get_row_from_uid(0x010203)
    
    assert(row[0] == 0x010203)
    assert(row[1] == "test_update_entry")
    assert(row[2] == 3)
    assert(duplicate == False)
  
  def test_delete_entry(self):
    self.delete_entry(0x010203)
    
    assert(self.check_uid(0x010203) == False)
  
  def test_duplicate_check_after_manual_delete(self):
    self._db_cursor.execute("DELETE FROM users WHERE fullname = ?", ['Duplicate Admin'])
    self._db.commit()
    
    row, duplicate = self.get_row_from_uid(151493474601)
    
    assert(row[0] == 151493474601)
    assert(row[1] == "David Rohrbaugh")
    assert(row[2] == 1)
    assert(duplicate == False)
  
  def test_remove_expired_users(self):
    self.remove_expired_users()
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired User'])
    assert(len(res.fetchall()) == 0)
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired Admin'])
    assert(len(res.fetchall()) != 0)
  
  def test_remove_expired_entries(self):
    self.remove_expired_entries()
    
    # if test_remove_expired_users is not run, check that this test removed the expired user
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired User'])
    assert(len(res.fetchall()) == 0)
    
    res = self._db_cursor.execute("SELECT * FROM users WHERE fullname = ?", ['Expired Admin'])
    assert(len(res.fetchall()) == 0)

def main():
  setup_test_db.setup()
  db = test_db_interface("test.db")
  
  db.test_get_row_from_uid()
  
  db.test_get_row_from_uid_duplicate()
  
  db.test_get_name()
  
  db.test_check_uid()
  
  db.test_is_admin()
  
  db.test_add_entry()
  
  db.test_update_entry()
  
  db.test_delete_entry()
  
  db.test_duplicate_check_after_manual_delete()
  
  db.test_remove_expired_users()
  
  db.test_remove_expired_entries()

if __name__ == "__main__":
  main()
  
  print('all tests passed')