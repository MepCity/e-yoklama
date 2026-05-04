import sqlite3

conn = sqlite3.connect('e_yoklama.db')
cursor = conn.cursor()

# Search for Nisanur and Berfin
cursor.execute('SELECT id, username, email, department, class_name FROM users WHERE username LIKE "%nisanur%" OR username LIKE "%berfin%" OR email LIKE "%nisanur%" OR email LIKE "%berfin%"')
students = cursor.fetchall()

print('Search results for Nisanur and Berfin:')
for student in students:
    print(f'ID: {student[0]}, Username: {student[1]}, Email: {student[2]}, Department: {student[3]}, Class: {student[4]}')

conn.close()
