# 📝 AI辅助学习笔记系统

基于 Python + Streamlit + SQLite + DeepSeek API 构建的 AI 智能学习笔记系统,支持多用户、AI 辅助总结与知识管理。

## 🌟 功能特点

- 👤 **多用户系统**:支持用户注册、登录,笔记数据隔离,密码安全哈希存储
- ✨ **AI 智能总结**:一键调用 DeepSeek API 生成笔记关键词和总结
- 🔍 **搜索筛选**:支持标题搜索和日期范围筛选
- 📚 **学习资源推荐**:基于关键词自动推荐百度百科、简书、B 站等学习资源
- 📁 **本地存储**:使用 SQLite 数据库,数据安全可控
- 🎨 **精美界面**:现代化 UI 设计,操作便捷

## 📋 技术栈

- **前端框架**:Streamlit 1.57.0
- **数据库**:SQLite3(Python 内置)
- **AI 服务**:DeepSeek API
- **其他依赖**:requests、python-dotenv

## 🚀 安装步骤

### 1. 创建虚拟环境

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`,配置 API 密钥:

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

### 4. 初始化数据库

首次运行时系统会自动创建数据库和表结构,无需手动操作。

## 🔑 如何申请 DeepSeek API

### 申请步骤

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并完成实名认证
3. 进入 "API Keys" 页面
4. 点击 "Create new API key" 生成密钥
5. 将密钥复制到 `.env` 文件中

### 免费额度说明

- **deepseek-chat** 模型:每月有一定免费额度
- 详细价格请参考 [官方文档](https://platform.deepseek.com/api-docs/pricing)

## 🎯 运行项目

```bash
streamlit run app.py
```

运行后访问 `http://localhost:8501` 即可使用。

首次使用请先注册账号,然后登录进入主界面。

## 📁 项目结构

```
AI-assisted-learning-system/
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
├── requirements.txt        # 依赖列表
├── app.py                  # Streamlit 主应用
├── README.md               # 项目文档
├── data/                   # 数据存储目录
│   └── notes.db            # SQLite 数据库文件
└── utils/                  # 工具函数目录
    ├── __init__.py
    ├── ai_client.py        # AI 接口调用封装
    └── db_operations.py    # 数据库操作封装
```

## ❓ 常见问题

### Q: API 调用失败怎么办？

**可能原因及解决方案:**

1. **API Key 错误**:检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确,确保以 `sk-` 开头
2. **未实名认证**:DeepSeek 要求完成实名认证后才能正常调用 API
3. **网络问题**:确保网络可以访问 `https://api.deepseek.com`
4. **额度用尽**:登录 DeepSeek 平台查看 API 使用额度
5. **401 错误**:系统会给出详细的错误提示和解决建议

### Q: 数据库文件在哪里？

数据库文件位于 `data/notes.db`,包含 `users` 表和 `notes` 表。

### Q: 如何备份数据？

直接复制 `data/notes.db` 文件即可完成备份。

### Q: 忘记虚拟环境激活命令？

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 退出虚拟环境
deactivate
```

### Q: 页面显示异常？

尝试清除浏览器缓存或使用无痕模式访问。

## 📝 使用说明

1. **注册账号**:首次使用先注册用户名和密码
2. **登录系统**:使用注册的账号登录
3. **创建笔记**:点击侧边栏"新建笔记"按钮
4. **AI 总结**:查看笔记时点击"AI 生成关键词和总结"按钮
5. **搜索笔记**:使用搜索框输入标题关键词
6. **日期筛选**:选择日期范围筛选笔记
7. **学习资源**:查看基于关键词推荐的学习资源链接

## 📄 许可证

MIT License

---

**享受智能学习的乐趣!** 🎉
