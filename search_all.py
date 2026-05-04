import sqlite3

conn = sqlite3.connect('e_yoklama.db')
cursor = conn.cursor()

# Search all users
cursor.execute('SELECT id, username, email, department, class_name FROM users WHERE role=2')
students = cursor.fetchall()

print('All students:')
for student in students:
    print(f'ID: {student[0]}, Username: {student[1]}, Email: {student[2]}, Department: {student[3]}, Class: {student[4]}')

print('\nSearching for names containing "nisanur", "berfin", "kara":')
cursor.execute('SELECT id, username, email, department, class_name FROM users WHERE username LIKE "%nisanur%" OR username LIKE "%berfin%" OR username LIKE "%kara%" OR email LIKE "%nisanur%" OR email LIKE "%berfin%" OR email LIKE "%kara%"')
students = cursor.fetchall()

for student in students:
    print(f'ID: {student[0]}, Username: {student[1]}, Email: {student[2]}, Department: {student[3]}, Class: {student[4]}')

conn.close()
