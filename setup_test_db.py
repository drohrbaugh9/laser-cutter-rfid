import sqlite3
import datetime

def setup():
  testdb = sqlite3.connect("test.db")
  cur = testdb.cursor()
  
  # delete old tables
  cur.execute("DROP TABLE IF EXISTS users")
  cur.execute("DROP TABLE IF EXISTS users_log")
  cur.execute("DROP TABLE IF EXISTS laser_log")
  
  # create new table and fill in
  cur.execute("CREATE TABLE users(ramcard_uid, fullname, is_admin, expiration_date)")
  
  now = datetime.datetime.today()
  six_months = datetime.timedelta(days = 180)
  expiration_date = int((now + six_months).timestamp())
  date_in_the_past = int((now - six_months).timestamp())
  
  cur.execute("""
    INSERT INTO users VALUES
      (151493474601, 'David Rohrbaugh', 1, %d),
      (123456789012, 'Expired User', 0, %d),
      (98765432109, 'Expired Admin', 1, %d),
      (86080826340, 'Test User', 0, %d),
      (151493474601, 'Duplicate Admin', 1, %d)
  """ % (expiration_date, date_in_the_past, date_in_the_past, expiration_date, expiration_date))
  
  cur.execute("CREATE TABLE users_log(timestamp, action, data)")
  
  cur.execute("CREATE TABLE laser_log(timestamp, action, data)")
  
  testdb.commit()
  
  testdb.close()

if __name__ == "__main__":
  setup()