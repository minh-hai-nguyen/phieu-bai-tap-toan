#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt

# Seed database if it doesn't exist
if [ ! -f webapp.db ]; then
    python seed_exercises.py
fi

# Create default admin user
python -c "
from db import init_webapp_db, get_webapp_db
from auth import hash_password
init_webapp_db()
conn = get_webapp_db()
cur = conn.cursor()
cur.execute(\"SELECT id FROM users WHERE role='admin' LIMIT 1\")
if not cur.fetchone():
    cur.execute(
        'INSERT INTO users (username, password_hash, display_name, role) VALUES (?,?,?,?)',
        ('admin', hash_password('admin123'), 'Quản trị viên', 'admin')
    )
    conn.commit()
    print('Created default admin: admin / admin123')
cur.execute(\"SELECT id FROM users WHERE username='hocsinh'\")
if not cur.fetchone():
    cur.execute(
        'INSERT INTO users (username, password_hash, display_name, role, lop) VALUES (?,?,?,?,?)',
        ('hocsinh', hash_password('123456'), 'Học sinh Demo', 'student', 1)
    )
    conn.commit()
    print('Created demo student: hocsinh / 123456')
conn.close()
"
