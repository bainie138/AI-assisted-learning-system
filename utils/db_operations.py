import sqlite3
import os

# 确保data目录存在
os.makedirs('data', exist_ok=True)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('data/notes.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_note(title, content, keywords=None, summary=None):
    """创建新笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (title, content, keywords, summary)
        VALUES (?, ?, ?, ?)
    ''', (title, content, keywords, summary))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def get_all_notes():
    """获取所有笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes ORDER BY created_at DESC')
    notes = cursor.fetchall()
    conn.close()
    return notes

def get_note_by_id(note_id):
    """根据ID获取笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    note = cursor.fetchone()
    conn.close()
    return note

def update_note(note_id, title=None, content=None, keywords=None, summary=None):
    """更新笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
        cursor.execute(f'''
            UPDATE notes SET {', '.join(update_fields)} WHERE id = ?
        ''', params)
        conn.commit()
    
    conn.close()

def delete_note(note_id):
    """删除笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

def search_notes(keyword):
    """搜索笔记（支持标题和内容搜索）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM notes 
        WHERE title LIKE ? OR content LIKE ? 
        ORDER BY created_at DESC
    ''', (f'%{keyword}%', f'%{keyword}%'))
    notes = cursor.fetchall()
    conn.close()
    return notes
