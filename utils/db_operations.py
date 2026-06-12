import sqlite3
import os
import hashlib

# 确保data目录存在
os.makedirs('data', exist_ok=True)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('data/notes.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建笔记表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keywords TEXT,
            summary TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """注册新用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
        ''', (username, hash_password(password)))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def authenticate_user(username, password):
    """验证用户登录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username FROM users 
        WHERE username = ? AND password = ?
    ''', (username, hash_password(password)))
    
    user = cursor.fetchone()
    conn.close()
    
    return user

def create_note(user_id, title, content, keywords=None, summary=None):
    """创建新笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (user_id, title, content, keywords, summary)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, content, keywords, summary))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def get_all_notes(user_id):
    """获取用户所有笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    notes = cursor.fetchall()
    conn.close()
    return notes

def get_note_by_id(note_id, user_id):
    """根据ID获取笔记（验证用户权限）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    note = cursor.fetchone()
    conn.close()
    return note

def update_note(note_id, user_id, title=None, content=None, keywords=None, summary=None):
    """更新笔记（验证用户权限）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先验证笔记是否属于该用户
    cursor.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False
    
    update_fields = []
    params = []
    
    if title is not None:
        update_fields.append('title = ?')
        params.append(title)
    if content is not None:
        update_fields.append('content = ?')
        params.append(content)
    if keywords is not None:
        update_fields.append('keywords = ?')
        params.append(keywords)
    if summary is not None:
        update_fields.append('summary = ?')
        params.append(summary)
    
    if update_fields:
        params.append(note_id)
        set_clause = ', '.join(update_fields)
        cursor.execute(
            'UPDATE notes SET ' + set_clause + ' WHERE id = ?',
            params
        )
        conn.commit()
    
    conn.close()
    return True

def delete_note(note_id, user_id):
    """删除笔记（验证用户权限）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先验证笔记是否属于该用户
    cursor.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return True

def search_notes(user_id, keyword):
    """搜索笔记（支持标题和内容搜索）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM notes 
        WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) 
        ORDER BY created_at DESC
    ''', (user_id, f'%{keyword}%', f'%{keyword}%'))
    notes = cursor.fetchall()
    conn.close()
    return notes

# 初始化表（模块加载时自动执行，确保表结构存在）
init_tables()  # pyright: ignore[reportUnusedCallResult]