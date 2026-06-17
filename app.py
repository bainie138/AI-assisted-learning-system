import streamlit as st
from datetime import datetime

# 导入工具函数
from utils.db_operations import (
    create_note,
    get_all_notes,
    get_note_by_id,
    update_note,
    delete_note,
    register_user,
    authenticate_user,
    create_tag,
    get_all_tags,
    get_child_tags,
    update_tag,
    delete_tag,
    set_note_tags,
    get_note_tags,
    get_notes_by_tag
)

from utils.ai_client import generate_keywords_and_summary


# ========================
# 标签辅助函数
# ========================

def build_tag_tree(tags, parent_id=None):
    """从平铺标签列表构建树形结构,返回指定父节点的子标签列表"""
    children = [t for t in tags if (
        t['parent_id'] == parent_id or
        (parent_id is None and t['parent_id'] is None)
    )]
    children.sort(key=lambda t: t['name'])
    return children


def get_tag_full_path(tag, all_tags):
    """获取标签的完整路径(如 '编程/Python/机器学习')"""
    path_parts = [tag['name']]
    current = tag
    # 如果传入的是类似dict的对象且没有get方法(sqlite3.Row),需要适配
    while current['parent_id'] is not None:
        parent = next(
            (t for t in all_tags if t['id'] == current['parent_id']),
            None
        )
        if parent is None:
            break
        path_parts.insert(0, parent['name'])
        current = parent
    return ' / '.join(path_parts)


def get_tag_options(all_tags):
    """返回 {tag_id: '完整路径'} 的字典,用于 multiselect"""
    options = {}
    for tag in all_tags:
        options[tag['id']] = get_tag_full_path(tag, all_tags)
    return options


def render_tag_tree(tags, parent_id, indent_level, all_tags):
    """递归渲染标签树(紧凑版)"""
    children = build_tag_tree(tags, parent_id)
    for tag in children:
        tag_id = tag['id']
        tag_name = tag['name']
        has_children = any(t['parent_id'] == tag_id for t in tags)
        expanded = tag_id in st.session_state.expanded_tags
        is_active = st.session_state.tag_filter_id == tag_id

        # 箭头小图标
        arrow = '▾' if (expanded and has_children) else ('▸' if has_children else ' ')

        # 每行:箭头(极小) + 标签名按钮 + 添加子标签按钮
        col1, col2, col3 = st.columns([0.5, 7, 0.8])

        with col1:
            if has_children:
                if st.button(arrow, key=f"te-{tag_id}", help="展开/折叠"):
                    if expanded:
                        st.session_state.expanded_tags.discard(tag_id)
                    else:
                        st.session_state.expanded_tags.add(tag_id)
                    st.rerun()

        with col2:
            btn_label = f"● {tag_name}" if is_active else tag_name
            btn_type = "primary" if is_active else "tertiary"
            if st.button(btn_label, key=f"tf-{tag_id}", type=btn_type,
                         help=get_tag_full_path(tag, all_tags)):
                st.session_state.tag_filter_id = None if is_active else tag_id
                st.rerun()

        with col3:
            if st.button('+', key=f"ta-{tag_id}", help="添加子标签"):
                st.session_state.tag_editor_parent_id = tag_id
                st.session_state.tag_management_open = True
                st.rerun()

        # 递归子标签
        if expanded and has_children:
            st.markdown(
                f'<div style="margin-left:{16 * (indent_level + 1)}px;">',
                unsafe_allow_html=True
            )
            render_tag_tree(tags, tag_id, indent_level + 1, all_tags)
            st.markdown('</div>', unsafe_allow_html=True)

# 设置页面配置
st.set_page_config(
    page_title="AI学习笔记系统",
    page_icon="📝",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
/* 笔记卡片样式 */
.note-card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
    border: 1px solid #e9ecef;
    transition: all 0.2s ease;
}

.note-card:hover {
    background-color: #e9ecef;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

/* 主内容区域卡片 */
.content-card {
    background-color: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* 学习资源卡片 */
.resource-card {
    background-color: #f0f9ff;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}

/* 总结卡片 */
.summary-card {
    background-color: #fef3c7;
    padding: 12px;
    border-radius: 8px;
}

/* 标题样式 */
.main-title {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
}

/* 侧边栏美化 */
.sidebar-intro {
    padding: 10px 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    color: white;
    margin-bottom: 12px;
}

/* 按钮样式增强 */
.stButton>button {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}

.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 编辑模式高亮 */
.edit-mode {
    border-left: 4px solid #3b82f6;
    padding-left: 12px;
}

/* 登录卡片 */
.login-card {
    max-width: 400px;
    margin: 0 auto;
    padding: 32px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

/* 标签chip样式 */
.tag-chip {
    display: inline-block;
    background: #e0e7ff;
    color: #3730a3;
    border-radius: 4px;
    padding: 2px 8px;
    margin: 2px;
    font-size: 11px;
    font-weight: 500;
}

.tag-chip-active {
    background: #6366f1;
    color: white;
}

/* 标签树容器 */
.tag-tree-container {
    max-height: 240px;
    overflow-y: auto;
    padding: 2px 0;
    margin-bottom: 0;
}

/* 标签管理面板 */
.tag-management-panel {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 10px;
    margin-top: 6px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'  # login, register, main
if 'selected_note' not in st.session_state:
    st.session_state.selected_note = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'ai_processing' not in st.session_state:
    st.session_state.ai_processing = False
if 'refresh_key' not in st.session_state:
    st.session_state.refresh_key = 0
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'edit_title' not in st.session_state:
    st.session_state.edit_title = ""
if 'edit_content' not in st.session_state:
    st.session_state.edit_content = ""
if 'tag_filter_id' not in st.session_state:
    st.session_state.tag_filter_id = None
if 'tag_filter_include_children' not in st.session_state:
    st.session_state.tag_filter_include_children = True
if 'tag_management_open' not in st.session_state:
    st.session_state.tag_management_open = False
if 'expanded_tags' not in st.session_state:
    st.session_state.expanded_tags = set()
if 'tag_editor_parent_id' not in st.session_state:
    st.session_state.tag_editor_parent_id = None
if 'tag_editor_name' not in st.session_state:
    st.session_state.tag_editor_name = ''
if 'selected_note_tags' not in st.session_state:
    st.session_state.selected_note_tags = []

# 登录页面
def show_login_page():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="text-align:center;margin-bottom:8px;">📝 AI学习笔记</h1>', unsafe_allow_html=True)
    st.subheader("用户登录", divider='gray')

    username = st.text_input("用户名", placeholder="请输入用户名")
    password = st.text_input("密码", placeholder="请输入密码", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("登录", type="primary", use_container_width=True):
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = {'id': user['id'], 'username': user['username']}
                    st.session_state.page = 'main'
                    st.session_state.selected_note = None
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            else:
                st.warning("请输入用户名和密码")

    with col2:
        if st.button("注册", use_container_width=True):
            st.session_state.page = 'register'
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# 注册页面
def show_register_page():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="text-align:center;margin-bottom:8px;">📝 AI学习笔记</h1>', unsafe_allow_html=True)
    st.subheader("用户注册", divider='gray')

    username = st.text_input("用户名", placeholder="请输入用户名")
    password = st.text_input("密码", placeholder="请输入密码", type="password")
    confirm_password = st.text_input("确认密码", placeholder="请再次输入密码", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("注册", type="primary", use_container_width=True):
            if not username:
                st.warning("请输入用户名")
            elif not password:
                st.warning("请输入密码")
            elif password != confirm_password:
                st.error("两次输入的密码不一致")
            else:
                user_id = register_user(username, password)
                if user_id:
                    st.success("注册成功!请登录")
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error("用户名已存在")

    with col2:
        if st.button("返回登录", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# 主应用页面
def show_main_page():
    # 页面标题和用户信息
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<h1 class="main-title">📝 AI学习笔记系统</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align:right;padding-top:16px;">
            <span style="margin-right:12px;">👤 {st.session_state.user['username']}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("退出登录", key="logout-btn", type="secondary"):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.session_state.selected_note = None
            st.rerun()

    # 侧边栏
    with st.sidebar:
        # 系统简介
        st.markdown("""
        <div class="sidebar-intro">
            <strong>📝 AI学习笔记</strong>
            <span style="font-size:12px;opacity:0.85;display:block;">智能学习笔记系统</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ========================
        # 搜索与筛选
        # ========================
        st.caption("🔍 搜索与筛选")

        # 搜索框
        search_query = st.text_input(
            "按标题搜索",
            value=st.session_state.search_query,
            placeholder="输入标题关键词",
            label_visibility="collapsed",
            key="search_input"
        )

        # 日期筛选
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=st.session_state.start_date, key="start_date_input")
        with col2:
            end_date = st.date_input("结束日期", value=st.session_state.end_date, key="end_date_input")

        # 应用/重置
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("应用", type="primary", use_container_width=True):
                st.session_state.search_query = search_query
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date
                st.session_state.selected_note = None
                st.session_state.refresh_key += 1
        with col_btn2:
            if st.button("重置", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.start_date = None
                st.session_state.end_date = None
                st.session_state.selected_note = None
                st.session_state.refresh_key += 1
                st.rerun()

        st.divider()

        # 新建笔记 + 标签目录
        col_new, col_tag = st.columns([1, 1])
        with col_new:
            if st.button("＋ 新建笔记", use_container_width=True):
                st.session_state.selected_note = None
                st.session_state.edit_mode = False
                st.session_state.tag_filter_id = None
                st.session_state.refresh_key += 1
        with col_tag:
            tag_mgmt_label = "管理标签" if not st.session_state.tag_management_open else "关闭管理"
            if st.button(tag_mgmt_label, key="tag-mgmt-toggle", use_container_width=True):
                st.session_state.tag_management_open = not st.session_state.tag_management_open
                st.rerun()

        # ========================
        # 标签目录
        # ========================
        st.caption("🏷️ 标签目录")

        # 获取当前用户的所有标签
        all_tags = get_all_tags(st.session_state.user['id'])

        # 标签筛选指示器
        if st.session_state.tag_filter_id:
            active_tag = next(
                (t for t in all_tags if t['id'] == st.session_state.tag_filter_id),
                None
            )
            if active_tag:
                col_f1, col_f2, col_f3 = st.columns([3, 1, 1])
                with col_f1:
                    st.markdown(
                        f'<span style="font-size:12px;color:#6366f1;">'
                        f'筛选: {active_tag["name"]}</span>',
                        unsafe_allow_html=True
                    )
                with col_f2:
                    include_children = st.checkbox(
                        "含子", value=st.session_state.tag_filter_include_children,
                        key="tag_include_children_check"
                    )
                    st.session_state.tag_filter_include_children = include_children
                with col_f3:
                    if st.button("✕", key="clear-tag-filter", help="清除标签筛选"):
                        st.session_state.tag_filter_id = None
                        st.rerun()

        # 渲染标签树
        if all_tags:
            st.markdown('<div class="tag-tree-container">', unsafe_allow_html=True)
            render_tag_tree(all_tags, None, 0, all_tags)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.caption("  — 暂无标签")

        # 标签管理面板
        if st.session_state.tag_management_open:
            st.markdown('<div class="tag-management-panel">', unsafe_allow_html=True)

            # --- 创建新根标签 ---
            st.caption("创建根标签")
            new_tag_name = st.text_input(
                "标签名", key="new_root_tag_name",
                placeholder="输入标签名称", label_visibility="collapsed"
            )
            if st.button("创建", key="create-root-tag", use_container_width=True):
                if new_tag_name.strip():
                    result = create_tag(st.session_state.user['id'], new_tag_name.strip())
                    if result:
                        st.success(f"'{new_tag_name}' 已创建")
                        st.rerun()
                    else:
                        st.error("标签已存在")
                else:
                    st.warning("请输入标签名称")

            # --- 创建子标签 ---
            if st.session_state.tag_editor_parent_id is not None:
                parent_tag = next(
                    (t for t in all_tags if t['id'] == st.session_state.tag_editor_parent_id),
                    None
                )
                if parent_tag:
                    st.caption(f"在「{parent_tag['name']}」下创建子标签")
                    child_name = st.text_input(
                        "子标签名", key="new_child_tag_name",
                        placeholder="输入子标签名称", label_visibility="collapsed"
                    )
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button("创建", key="create-child-tag", use_container_width=True):
                            if child_name.strip():
                                result = create_tag(
                                    st.session_state.user['id'],
                                    child_name.strip(),
                                    parent_id=st.session_state.tag_editor_parent_id
                                )
                                if result:
                                    st.success("已创建")
                                    st.session_state.expanded_tags.add(st.session_state.tag_editor_parent_id)
                                    st.session_state.tag_editor_parent_id = None
                                    st.rerun()
                                else:
                                    st.error("标签已存在")
                            else:
                                st.warning("请输入标签名称")
                    with col_c2:
                        if st.button("取消", key="cancel-child-tag", use_container_width=True):
                            st.session_state.tag_editor_parent_id = None
                            st.rerun()

            #编辑标签
            if all_tags:
                st.caption("编辑 / 删除标签")
                tag_options = get_tag_options(all_tags)
                tag_to_edit_id = st.selectbox(
                    "选择", options=list(tag_options.keys()),
                    format_func=lambda tid: tag_options[tid],
                    key="tag_to_edit_select", label_visibility="collapsed"
                )

                rename_name = st.text_input(
                    "重命名", key="tag_rename_input",
                    placeholder="留空不修改", label_visibility="collapsed"
                )

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    move_options = {"__keep__": "不移动", "__none__": "→ 根级别"}
                    for tid, path in tag_options.items():
                        if tid != tag_to_edit_id:
                            move_options[str(tid)] = path
                    move_to = st.selectbox(
                        "移动到", options=list(move_options.keys()),
                        format_func=lambda k: move_options[k],
                        key="tag_move_select", label_visibility="collapsed"
                    )
                with col_e2:
                    confirm_delete = st.checkbox("确认删除", key="tag_delete_confirm")
                    if st.button("删除", key="tag-delete-btn", disabled=not confirm_delete,
                                 use_container_width=True):
                        delete_tag(tag_to_edit_id, st.session_state.user['id'])
                        if st.session_state.tag_filter_id == tag_to_edit_id:
                            st.session_state.tag_filter_id = None
                        st.session_state.expanded_tags.discard(tag_to_edit_id)
                        st.rerun()

                if st.button("保存修改", key="tag-save-edit", use_container_width=True):
                    changed = False
                    if rename_name and rename_name.strip():
                        if update_tag(tag_to_edit_id, st.session_state.user['id'],
                                      name=rename_name.strip()):
                            changed = True
                        else:
                            st.error("名称可能已存在")
                    if move_to != "__keep__":
                        new_parent = None if move_to == "__none__" else int(move_to)
                        if update_tag(tag_to_edit_id, st.session_state.user['id'],
                                      parent_id=new_parent):
                            changed = True
                        else:
                            st.error("移动失败(可能造成环路)")
                    if changed:
                        st.success("已保存")
                        st.rerun()
                    elif not rename_name or not rename_name.strip():
                        st.info("无修改")

            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # 当前筛选条件
        if st.session_state.search_query or st.session_state.start_date or st.session_state.end_date:
            st.caption("📊 当前筛选")
            if st.session_state.search_query:
                st.markdown(f"<small>标题: `{st.session_state.search_query}`</small>", unsafe_allow_html=True)
            if st.session_state.start_date:
                st.markdown(f"<small>起始: {st.session_state.start_date}</small>", unsafe_allow_html=True)
            if st.session_state.end_date:
                st.markdown(f"<small>截止: {st.session_state.end_date}</small>", unsafe_allow_html=True)

        st.divider()

        # 笔记列表
        st.caption("📋 笔记列表")

        # 获取用户所有笔记
        all_notes = get_all_notes(st.session_state.user['id'])

        # 应用筛选条件
        filtered_notes = all_notes

        # 标题关键词筛选
        if st.session_state.search_query:
            filtered_notes = [
                note for note in filtered_notes
                if st.session_state.search_query.lower() in note['title'].lower()
            ]

        # 日期范围筛选
        if st.session_state.start_date:
            filtered_notes = [
                note for note in filtered_notes
                if datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S').date() >= st.session_state.start_date
            ]

        if st.session_state.end_date:
            filtered_notes = [
                note for note in filtered_notes
                if datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S').date() <= st.session_state.end_date
            ]

        # 标签筛选(额外过滤层)
        if st.session_state.tag_filter_id:
            tag_notes = get_notes_by_tag(
                st.session_state.user['id'],
                st.session_state.tag_filter_id,
                include_children=st.session_state.tag_filter_include_children
            )
            tag_note_ids = {n['id'] for n in tag_notes}
            filtered_notes = [n for n in filtered_notes if n['id'] in tag_note_ids]

        # 显示筛选结果
        if filtered_notes:
            st.caption(f"共 {len(filtered_notes)} 条笔记")
        else:
            st.caption("没有匹配的笔记")

        # 显示笔记列表
        for note in filtered_notes:
            note_date = datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')

            # 获取笔记的标签
            note_tags = get_note_tags(note['id'], st.session_state.user['id'])
            tag_chips_html = ''
            if note_tags:
                tag_chips_html = '<div style="margin-top:6px;">' + ''.join(
                    f'<span class="tag-chip">{get_tag_full_path(t, all_tags)}</span>'
                    for t in note_tags[:3]
                )
                if len(note_tags) > 3:
                    tag_chips_html += (
                        f'<span class="tag-chip">+{len(note_tags) - 3}</span>'
                    )
                tag_chips_html += '</div>'

            st.markdown(f"""
            <div class="note-card">
                <span style="font-weight:600;color:#1f2937;">📄 {note['title'][:30]}{'...' if len(note['title']) > 30 else ''}</span>
                <span style="display:block;font-size:12px;color:#6b7280;margin-top:4px;">{note_date}</span>
                {tag_chips_html}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"note_{note['id']}", key=f"note-btn-{note['id']}", use_container_width=True):
                st.session_state.selected_note = note['id']
                st.session_state.edit_mode = False

    # 主内容区域
    if st.session_state.selected_note:
        # 显示笔记详情
        note = get_note_by_id(st.session_state.selected_note, st.session_state.user['id'])
        if note:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)

            # 编辑模式
            if st.session_state.edit_mode:
                st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
                st.subheader("✏️ 编辑笔记")

                # 初始化编辑内容
                if st.session_state.edit_title == "" or st.session_state.edit_content == "":
                    st.session_state.edit_title = note['title']
                    st.session_state.edit_content = note['content']

                # 编辑表单
                edit_title = st.text_input("标题", value=st.session_state.edit_title, key="edit_title_input")
                edit_content = st.text_area("内容", value=st.session_state.edit_content, height=300, key="edit_content_input")

                # 标签选择(编辑模式)
                st.markdown("**🏷️ 标签**")
                all_tags_for_edit = get_all_tags(st.session_state.user['id'])
                if all_tags_for_edit:
                    tag_options_edit = get_tag_options(all_tags_for_edit)
                    # 预填当前笔记的标签
                    current_note_tags = get_note_tags(
                        st.session_state.selected_note,
                        st.session_state.user['id']
                    )
                    current_tag_ids = [t['id'] for t in current_note_tags]
                    selected_edit_tags = st.multiselect(
                        "选择标签",
                        options=list(tag_options_edit.keys()),
                        format_func=lambda tid: tag_options_edit[tid],
                        default=current_tag_ids,
                        key="edit_note_tag_select",
                        help="可选择多个标签对笔记进行分类"
                    )
                else:
                    selected_edit_tags = []
                    st.caption("暂无标签")

                # 保存修改按钮
                col1, col2 = st.columns(2)
                with col1:
                    can_save = bool(edit_title and edit_content)
                    if st.button("💾 保存修改", type="primary", disabled=not can_save):
                        # 更新数据库
                        success = update_note(
                            st.session_state.selected_note,
                            st.session_state.user['id'],
                            title=edit_title,
                            content=edit_content
                        )
                        if success:
                            # 保存标签关联
                            if selected_edit_tags is not None:
                                set_note_tags(
                                    st.session_state.selected_note,
                                    st.session_state.user['id'],
                                    selected_edit_tags
                                )
                            st.success("✅ 修改保存成功!")
                            # 退出编辑模式并刷新
                            st.session_state.edit_mode = False
                            st.session_state.edit_title = ""
                            st.session_state.edit_content = ""
                            st.session_state.refresh_key += 1
                        else:
                            st.error("❌ 修改失败,权限不足")
                with col2:
                    if st.button("❌ 取消编辑"):
                        st.session_state.edit_mode = False
                        st.session_state.edit_title = ""
                        st.session_state.edit_content = ""

                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # 查看模式
                st.subheader(note['title'])
                st.caption(f"创建时间:{note['created_at']}")

                # 笔记内容
                st.divider()
                st.markdown(f"<div style='line-height:1.8;color:#374151;'>{note['content']}</div>", unsafe_allow_html=True)

                # 显示已分配的标签
                note_detail_tags = get_note_tags(note['id'], st.session_state.user['id'])
                if note_detail_tags:
                    st.divider()
                    st.markdown("### 🏷️ 标签")
                    all_tags_for_path = get_all_tags(st.session_state.user['id'])
                    tag_paths_html = ''.join(
                        f'<span class="tag-chip">{get_tag_full_path(t, all_tags_for_path)}</span>'
                        for t in note_detail_tags
                    )
                    st.markdown(
                        f'<div style="margin-top:8px;">{tag_paths_html}</div>',
                        unsafe_allow_html=True
                    )

                # 显示关键词和总结(如果已生成)
                st.divider()
                if note['keywords'] and note['summary']:
                    st.markdown("### 🎯 AI分析结果")
                    st.markdown(f"<div style='margin-bottom:8px;'><strong>关键词:</strong>{note['keywords']}</div>", unsafe_allow_html=True)
                    st.markdown('<div class="summary-card"><strong>总结:</strong>' + note['summary'] + '</div>', unsafe_allow_html=True)
                elif note['keywords']:
                    st.markdown(f"**关键词:** {note['keywords']}")
                elif note['summary']:
                    st.markdown(f"**总结:** {note['summary']}")

                # 学习资源推荐
                st.divider()
                st.subheader("📚 学习资源推荐")

                if note['keywords']:
                    # 解析关键词
                    keywords_list = [k.strip() for k in note['keywords'].split(',') if k.strip()]

                    # 限制为前3个关键词
                    keywords_list = keywords_list[:3]

                    for idx, keyword in enumerate(keywords_list, 1):
                        st.markdown(f"""
                        <div class="resource-card">
                            <strong>关键词 {idx}:{keyword}</strong>
                            <div style="margin-top:12px;">
                                <a href="https://baike.baidu.com/item/{keyword}" target="_blank" style="margin-right:16px;">📖 百度百科</a>
                                <a href="https://www.jianshu.com/search?q={keyword}" target="_blank" style="margin-right:16px;">✍️ 简书搜索</a>
                                <a href="https://search.bilibili.com/?keyword={keyword}" target="_blank">🎬 B站搜索</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("💡 请先点击AI生成关键词和总结")

                # AI生成关键词和总结按钮
                if not (note['keywords'] and note['summary']):
                    if st.button("✨ AI生成关键词和总结", type="primary", disabled=st.session_state.ai_processing):
                        st.session_state.ai_processing = True
                        with st.spinner("AI分析中..."):
                            try:
                                # 调用AI生成关键词和总结
                                result = generate_keywords_and_summary(note['content'])

                                # 更新数据库
                                success = update_note(
                                    st.session_state.selected_note,
                                    st.session_state.user['id'],
                                    keywords=result.get('keywords'),
                                    summary=result.get('summary')
                                )

                                if success:
                                    st.success("✅ AI分析完成!")
                                    st.session_state.refresh_key += 1
                                else:
                                    st.error("❌ 更新失败,权限不足")
                            except Exception as e:
                                st.error(f"⚠️ AI调用失败:{str(e)}")
                            finally:
                                st.session_state.ai_processing = False

            # 操作按钮(始终显示)
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                # 编辑按钮
                if not st.session_state.edit_mode:
                    if st.button("✏️ 编辑笔记", key=f"edit-btn-{st.session_state.selected_note}"):
                        st.session_state.edit_mode = True
                        st.session_state.edit_title = note['title']
                        st.session_state.edit_content = note['content']
            with col2:
                # 删除按钮
                if not st.session_state.edit_mode:
                    if st.button("🗑️ 删除笔记", key=f"delete-btn-{st.session_state.selected_note}"):
                        success = delete_note(st.session_state.selected_note, st.session_state.user['id'])
                        if success:
                            st.session_state.selected_note = None
                            st.session_state.edit_mode = False
                            st.session_state.refresh_key += 1
                        else:
                            st.error("❌ 删除失败,权限不足")
            with col3:
                if st.button("🔄 刷新", key=f"refresh_btn_{st.session_state.selected_note}"):
                    st.session_state.edit_mode = False
                    st.session_state.edit_title = ""
                    st.session_state.edit_content = ""
                    st.session_state.refresh_key += 1

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("笔记不存在或权限不足")
    else:
        # 新建笔记表单
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.subheader("📝 新建笔记")

        title = st.text_input("标题", placeholder="输入笔记标题")
        content = st.text_area("内容", placeholder="输入笔记内容", height=300)

        # 标签选择
        st.subheader("🏷️ 标签")
        all_tags_for_form = get_all_tags(st.session_state.user['id'])
        if all_tags_for_form:
            tag_options = get_tag_options(all_tags_for_form)
            selected_tags = st.multiselect(
                "选择标签(可选)",
                options=list(tag_options.keys()),
                format_func=lambda tid: tag_options[tid],
                key="new_note_tag_select",
                help="可选择多个标签对笔记进行分类"
            )
        else:
            selected_tags = []
            st.caption("暂无标签,可在侧边栏 ⚙️ 管理标签中创建")

        # 保存按钮
        can_save = bool(title and content)
        if st.button("💾 保存笔记", type="primary", disabled=not can_save):
            # 保存笔记(不自动调用AI)
            note_id = create_note(st.session_state.user['id'], title, content, keywords=None, summary=None)
            # 保存标签关联
            if selected_tags and note_id:
                set_note_tags(note_id, st.session_state.user['id'], selected_tags)
            st.success("🎉 笔记保存成功!")

            # 清空表单并刷新
            st.session_state.search_query = ""
            st.session_state.refresh_key += 1

        st.markdown('</div>', unsafe_allow_html=True)

    # 页脚
    st.divider()
    st.caption("💡 提示:使用侧边栏的搜索和筛选功能快速找到笔记,点击笔记下方的AI按钮生成关键词和总结")

# 主入口
if st.session_state.page == 'login':
    show_login_page()
elif st.session_state.page == 'register':
    show_register_page()
elif st.session_state.page == 'main' and st.session_state.user:
    show_main_page()
else:
    st.session_state.page = 'login'
    st.rerun()
