import sqlite3

testdb = sqlite3.connect("test.db")
cur = testdb.cursor()

# delete old table
try:
  cur.execute("DROP TABLE users")
except sqlite3.OperationalError:
  pass

# create new table and fill in 
cur.execute("CREATE TABLE users(ramcard_uid, fullname, is_admin)")
cur.execute("""
  INSERT INTO users VALUES
    (86080826340, 'Test User', 0),
    (151493474601, 'David Rohrbaugh', 1),
    (151493474601, 'Duplicate Admin', 1)
""")
testdb.commit()

# more stuff here?

testdb.close()

