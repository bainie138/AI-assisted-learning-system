import sqlite3
import os

# 确保data目录存在
os.makedirs('data', exist_ok=True)

# 连接SQLite数据库（不存在则创建）
conn = sqlite3.connect('data/notes.db')
cursor = conn.cursor()

# 创建notes表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        keywords TEXT,
        summary TEXT
    )
''')

# 创建索引以优化查询
cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)')

# 提交更改并关闭连接
conn.commit()
conn.close()

print("✅ SQLite数据库初始化完成！")
print("📋 已创建notes表，包含字段：id, title, content, created_at, keywords, summary")
