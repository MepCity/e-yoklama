import sqlite3

conn = sqlite3.connect('e_yoklama.db')
cursor = conn.cursor()

# Check tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])

# Check users table if exists
if any('users' in t for t in tables):
    cursor.execute('SELECT id, username, email, role FROM users WHERE role IN (0, 1)')
    users = cursor.fetchall()
    print('Admin and Teacher users:')
    for user in users:
        role = 'Admin' if user[3] == 0 else 'Teacher'
        print(f'ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {role}')
else:
    print('No users table found')

conn.close()
