import sqlite3
import os
import hashlib

# 确保data目录存在
os.makedirs('data', exist_ok=True)

# 启用 WAL 模式以支持更好的并发(需在连接后执行)
_initialized = False

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('data/notes.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    """初始化数据库表"""
    global _initialized
    conn = get_db_connection()
    cursor = conn.cursor()

    # 启用外键约束
    cursor.execute('PRAGMA foreign_keys = ON')

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

    # 创建标签表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')

    # 创建笔记-标签关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (note_id, tag_id),
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')

    # 标签表索引
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_user_parent_name
        ON tags(user_id, parent_id, name)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tags_parent_id ON tags(parent_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id)
    ''')

    # 笔记标签关联表索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_note_tags_tag_id ON note_tags(tag_id)
    ''')

    conn.commit()
    conn.close()
    _initialized = True

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
    """根据ID获取笔记(验证用户权限)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
    note = cursor.fetchone()
    conn.close()
    return note

def update_note(note_id, user_id, title=None, content=None, keywords=None, summary=None):
    """更新笔记(验证用户权限)"""
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
    """删除笔记(验证用户权限)"""
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
    """搜索笔记(支持标题和内容搜索)"""
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

# 标签管理函数

def create_tag(user_id, name, parent_id=None):
    """创建新标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    try:
        cursor.execute(
            'INSERT INTO tags (user_id, name, parent_id) VALUES (?, ?, ?)',
            (user_id, name, parent_id)
        )
        conn.commit()
        tag_id = cursor.lastrowid
        conn.close()
        return tag_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_all_tags(user_id):
    """获取用户所有标签(平铺列表)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM tags WHERE user_id = ? ORDER BY name',
        (user_id,)
    )
    tags = cursor.fetchall()
    conn.close()
    return tags


def get_tag_by_id(tag_id, user_id):
    """根据ID获取标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM tags WHERE id = ? AND user_id = ?',
        (tag_id, user_id)
    )
    tag = cursor.fetchone()
    conn.close()
    return tag


def get_child_tags(user_id, parent_id=None):
    """获取指定节点的直接子标签"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if parent_id is None:
        cursor.execute(
            'SELECT * FROM tags WHERE user_id = ? AND parent_id IS NULL ORDER BY name',
            (user_id,)
        )
    else:
        cursor.execute(
            'SELECT * FROM tags WHERE user_id = ? AND parent_id = ? ORDER BY name',
            (user_id, parent_id)
        )
    children = cursor.fetchall()
    conn.close()
    return children


def _get_all_descendant_ids(cursor, tag_id, user_id):
    """递归获取标签的所有后代ID(内部辅助函数,用于环路检测)"""
    descendants = set()
    stack = [tag_id]
    while stack:
        current = stack.pop()
        cursor.execute(
            'SELECT id FROM tags WHERE parent_id = ? AND user_id = ?',
            (current, user_id)
        )
        children = cursor.fetchall()
        for child in children:
            child_id = child['id']
            if child_id not in descendants:
                descendants.add(child_id)
                stack.append(child_id)
    return descendants


def update_tag(tag_id, user_id, name=None, parent_id=None):
    """更新标签(验证所有权,含环路检测)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    # 验证所有权
    cursor.execute(
        'SELECT * FROM tags WHERE id = ? AND user_id = ?',
        (tag_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return False

    # 环路检测:如果要更新parent_id,新父节点不能是标签自身或其子孙
    if parent_id is not None and parent_id != -1:
        if parent_id == tag_id:
            conn.close()
            return False
        descendants = _get_all_descendant_ids(cursor, tag_id, user_id)
        if parent_id in descendants:
            conn.close()
            return False
        # 验证新父标签存在且属于同一用户
        cursor.execute(
            'SELECT id FROM tags WHERE id = ? AND user_id = ?',
            (parent_id, user_id)
        )
        if not cursor.fetchone():
            conn.close()
            return False

    # 构建动态更新
    update_fields = []
    params = []
    if name is not None:
        update_fields.append('name = ?')
        params.append(name)
    if parent_id is not None and parent_id != -1:
        update_fields.append('parent_id = ?')
        params.append(parent_id)

    if update_fields:
        params.append(tag_id)
        set_clause = ', '.join(update_fields)
        try:
            cursor.execute(
                'UPDATE tags SET ' + set_clause + ' WHERE id = ?',
                params
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return False

    conn.close()
    return True


def delete_tag(tag_id, user_id):
    """删除标签(CASCADE自动删除子标签和note_tags关联)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    # 验证所有权
    cursor.execute(
        'SELECT * FROM tags WHERE id = ? AND user_id = ?',
        (tag_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
    conn.commit()
    conn.close()
    return True

# 笔记-标签关联函数

def set_note_tags(note_id, user_id, tag_ids):
    """替换笔记的标签(事务内先删后插)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')

    # 验证笔记所有权
    cursor.execute(
        'SELECT id FROM notes WHERE id = ? AND user_id = ?',
        (note_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return False

    # 事务内:删除旧关联 + 插入新关联
    cursor.execute('DELETE FROM note_tags WHERE note_id = ?', (note_id,))
    for tag_id in tag_ids:
        # 只关联属于该用户的标签
        cursor.execute(
            'SELECT id FROM tags WHERE id = ? AND user_id = ?',
            (tag_id, user_id)
        )
        if cursor.fetchone():
            cursor.execute(
                'INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                (note_id, tag_id)
            )
    conn.commit()
    conn.close()
    return True


def get_note_tags(note_id, user_id):
    """获取笔记的标签列表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 先验证笔记属于该用户
    cursor.execute(
        'SELECT id FROM notes WHERE id = ? AND user_id = ?',
        (note_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute('''
        SELECT t.* FROM tags t
        INNER JOIN note_tags nt ON t.id = nt.tag_id
        WHERE nt.note_id = ?
        ORDER BY t.name
    ''', (note_id,))
    tags = cursor.fetchall()
    conn.close()
    return tags


def get_notes_by_tag(user_id, tag_id, include_children=True):
    """按标签筛选笔记"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if include_children:
        # 使用递归CTE获取标签及其所有后代
        cursor.execute('''
            WITH RECURSIVE tag_tree AS (
                SELECT id FROM tags WHERE id = ? AND user_id = ?
                UNION ALL
                SELECT t.id FROM tags t
                JOIN tag_tree tt ON t.parent_id = tt.id
                WHERE t.user_id = ?
            )
            SELECT DISTINCT n.* FROM notes n
            INNER JOIN note_tags nt ON n.id = nt.note_id
            INNER JOIN tag_tree ON nt.tag_id = tag_tree.id
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC
        ''', (tag_id, user_id, user_id, user_id))
    else:
        cursor.execute('''
            SELECT n.* FROM notes n
            INNER JOIN note_tags nt ON n.id = nt.note_id
            WHERE nt.tag_id = ? AND n.user_id = ?
            ORDER BY n.created_at DESC
        ''', (tag_id, user_id))

    notes = cursor.fetchall()
    conn.close()
    return notes


# 初始化表(模块加载时自动执行,确保表结构存在)
init_tables()  # pyright: ignore[reportUnusedCallResult]