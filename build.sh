#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt

# Always seed database (creates tables + exercises if not exist)
python seed_exercises.py

# Ensure admin user exists with current SECRET_KEY hash
python -c "
from db import init_webapp_db, get_webapp_db
from auth import hash_password
init_webapp_db()
conn = get_webapp_db()
cur = conn.cursor()

# Update or create admin user (ensure password hash matches current SECRET_KEY)
cur.execute(\"SELECT id FROM users WHERE username='admin'\")
row = cur.fetchone()
if row:
    cur.execute('UPDATE users SET password_hash=? WHERE username=?',
        (hash_password('admin123'), 'admin'))
    print('Updated admin password hash')
else:
    cur.execute(
        'INSERT INTO users (username, password_hash, display_name, role) VALUES (?,?,?,?)',
        ('admin', hash_password('admin123'), 'Quản trị viên', 'admin')
    )
    print('Created default admin: admin / admin123')

# Update or create demo student
cur.execute(\"SELECT id FROM users WHERE username='hocsinh'\")
row = cur.fetchone()
if row:
    cur.execute('UPDATE users SET password_hash=? WHERE username=?',
        (hash_password('123456'), 'hocsinh'))
else:
    cur.execute(
        'INSERT INTO users (username, password_hash, display_name, role, lop) VALUES (?,?,?,?,?)',
        ('hocsinh', hash_password('123456'), 'Học sinh Demo', 'student', 1)
    )
    print('Created demo student: hocsinh / 123456')

conn.commit()
conn.close()
print('Users ready')
"
