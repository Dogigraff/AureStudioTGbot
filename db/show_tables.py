import sqlite3

conn = sqlite3.connect('../ai_vision_studio.db')
c = conn.cursor()

print('Таблицы в базе:')
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in c.fetchall():
    print(row[0])

print('\nСтруктура таблицы leads:')
c.execute("PRAGMA table_info(leads);")
for row in c.fetchall():
    print(row)

conn.close()
