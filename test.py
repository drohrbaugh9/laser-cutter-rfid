import setup_test_db

import db_interface

errors = {}

def test_get_row_from_uid():
  errors['test_get_row_from_uid'] = []
  
  row, duplicate = db_interface.get_row_from_uid(86080826340)
  
  assert(row[0] == 86080826340)
  assert(row[1] == 'Test User')
  assert(row[2] == 0)
  assert(duplicate == False)

def test_get_row_from_uid_duplicate():
  row, duplicate = db_interface.get_row_from_uid(151493474601)
  
  assert(row[0] == 151493474601)
  assert(row[1] == 'David Rohrbaugh')
  assert(row[2] == 1)
  assert(duplicate == True)

def test__add_entry():
  db_interface.__add_entry(0x010203, "test__add_entry", 2)
  
  row, duplicate = db_interface.get_row_from_uid(0x010203)
  
  assert(row[0] == 0x010203)
  assert(row[1] == "test__add_entry")
  assert(row[2] == 2)
  assert(duplicate == False)

def main():
  setup_test_db.setup()
  db_interface.connect_to_db("test.db")
  
  test_get_row_from_uid()
  
  test_get_row_from_uid_duplicate()
  
  test__add_entry()

if __name__ == "__main__":
  main()
  
  print('all tests passed')