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
    authenticate_user
)

from utils.ai_client import generate_keywords_and_summary

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
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #e9ecef;
    transition: all 0.3s ease;
}

.note-card:hover {
    background-color: #e9ecef;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
    padding: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
    margin-bottom: 20px;
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
                    st.success("注册成功！请登录")
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
            <h3>🌟 系统简介</h3>
            <p style="font-size: 14px; opacity: 0.9;">基于AI的智能学习笔记系统，帮助您高效整理和学习知识。</p>
        </div>
        """, unsafe_allow_html=True)

        # 使用说明
        st.subheader("📖 使用说明")
        st.markdown("""
        1. **创建笔记**：点击"新建笔记"按钮添加新笔记
        2. **编辑笔记**：查看笔记时点击"编辑"按钮修改内容
        3. **AI总结**：点击"AI生成总结"按钮自动生成关键词和总结
        4. **搜索筛选**：使用搜索框和日期筛选快速查找笔记
        5. **学习资源**：基于关键词自动推荐学习资源
        """)

        st.divider()

        st.header("🔍 搜索与筛选")

        # 搜索框
        search_query = st.text_input(
            "📝 按标题搜索",
            value=st.session_state.search_query,
            placeholder="输入标题关键词",
            key="search_input"
        )

        st.divider()

        # 日期筛选
        st.subheader("📅 日期筛选")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=st.session_state.start_date, key="start_date_input")
        with col2:
            end_date = st.date_input("结束日期", value=st.session_state.end_date, key="end_date_input")

        # 应用筛选按钮
        if st.button("🔍 应用筛选", type="primary", use_container_width=True):
            st.session_state.search_query = search_query
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.selected_note = None
            st.session_state.refresh_key += 1

        # 重置筛选按钮
        if st.button("🔄 重置筛选", use_container_width=True):
            st.session_state.search_query = ""
            st.session_state.start_date = None
            st.session_state.end_date = None
            st.session_state.selected_note = None
            st.session_state.refresh_key += 1
            st.rerun()

        st.divider()

        # 添加新笔记按钮
        if st.button("➕ 新建笔记", use_container_width=True):
            st.session_state.selected_note = None
            st.session_state.edit_mode = False
            st.session_state.refresh_key += 1

        st.divider()

        # 显示当前筛选条件
        if st.session_state.search_query or st.session_state.start_date or st.session_state.end_date:
            st.subheader("📊 当前筛选条件")
            if st.session_state.search_query:
                st.markdown(f"- 标题关键词：`{st.session_state.search_query}`")
            if st.session_state.start_date:
                st.markdown(f"- 开始日期：{st.session_state.start_date}")
            if st.session_state.end_date:
                st.markdown(f"- 结束日期：{st.session_state.end_date}")

        st.divider()

        # 笔记列表
        st.subheader("📋 笔记列表")

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

        # 显示筛选结果
        if filtered_notes:
            st.success(f"找到 {len(filtered_notes)} 条笔记")
        else:
            st.info("没有找到匹配的笔记")

        # 显示笔记列表（带卡片样式）
        for note in filtered_notes:
            note_date = datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')
            st.markdown(f"""
            <div class="note-card">
                <span style="font-weight:600;color:#1f2937;">📄 {note['title'][:30]}{'...' if len(note['title']) > 30 else ''}</span>
                <span style="display:block;font-size:12px;color:#6b7280;margin-top:4px;">{note_date}</span>
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
                            st.success("✅ 修改保存成功！")
                            # 退出编辑模式并刷新
                            st.session_state.edit_mode = False
                            st.session_state.edit_title = ""
                            st.session_state.edit_content = ""
                            st.session_state.refresh_key += 1
                        else:
                            st.error("❌ 修改失败，权限不足")
                with col2:
                    if st.button("❌ 取消编辑"):
                        st.session_state.edit_mode = False
                        st.session_state.edit_title = ""
                        st.session_state.edit_content = ""

                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # 查看模式
                st.subheader(note['title'])
                st.caption(f"创建时间：{note['created_at']}")

                # 笔记内容
                st.divider()
                st.markdown(f"<div style='line-height:1.8;color:#374151;'>{note['content']}</div>", unsafe_allow_html=True)

                # 显示关键词和总结（如果已生成）
                st.divider()
                if note['keywords'] and note['summary']:
                    st.markdown("### 🎯 AI分析结果")
                    st.markdown(f"<div style='margin-bottom:8px;'><strong>关键词：</strong>{note['keywords']}</div>", unsafe_allow_html=True)
                    st.markdown('<div class="summary-card"><strong>总结：</strong>' + note['summary'] + '</div>', unsafe_allow_html=True)
                elif note['keywords']:
                    st.markdown(f"**关键词：** {note['keywords']}")
                elif note['summary']:
                    st.markdown(f"**总结：** {note['summary']}")

                # 学习资源推荐
                st.divider()
                st.subheader("📚 学习资源推荐")

                if note['keywords']:
                    # 解析关键词（假设用逗号分隔）
                    keywords_list = [k.strip() for k in note['keywords'].split(',') if k.strip()]

                    # 限制为前3个关键词
                    keywords_list = keywords_list[:3]

                    for idx, keyword in enumerate(keywords_list, 1):
                        st.markdown(f"""
                        <div class="resource-card">
                            <strong>关键词 {idx}：{keyword}</strong>
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
                                    st.success("✅ AI分析完成！")
                                    st.session_state.refresh_key += 1
                                else:
                                    st.error("❌ 更新失败，权限不足")
                            except Exception as e:
                                st.error(f"⚠️ AI调用失败：{str(e)}")
                            finally:
                                st.session_state.ai_processing = False

            # 操作按钮（始终显示）
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
                            st.error("❌ 删除失败，权限不足")
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

        # 保存按钮
        can_save = bool(title and content)
        if st.button("💾 保存笔记", type="primary", disabled=not can_save):
            # 保存笔记（不自动调用AI）
            create_note(st.session_state.user['id'], title, content, keywords=None, summary=None)
            st.success("🎉 笔记保存成功！")

            # 清空表单并刷新
            st.session_state.search_query = ""
            st.session_state.refresh_key += 1

        st.markdown('</div>', unsafe_allow_html=True)

    # 页脚
    st.divider()
    st.caption("💡 提示：使用侧边栏的搜索和筛选功能快速找到笔记，点击笔记下方的AI按钮生成关键词和总结")

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
