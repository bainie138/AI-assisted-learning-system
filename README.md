# 📝 AI学习笔记系统

基于Python + Streamlit + SQLite + 国内免费大模型API构建的智能学习笔记系统，帮助用户高效整理和学习知识。

## 🌟 功能特点

- ✨ **AI智能总结**：一键生成笔记关键词和总结
- 🔍 **搜索筛选**：支持标题搜索和日期范围筛选
- 📚 **学习资源推荐**：基于关键词自动推荐百度百科、简书、B站等学习资源
- 📁 **本地存储**：使用SQLite数据库，数据安全可控
- 🎨 **精美界面**：现代化UI设计，操作便捷

## 📋 技术栈

- **前端框架**：Streamlit 1.57.0
- **数据库**：SQLite3（Python内置）
- **AI服务**：DeepSeek API
- **其他依赖**：requests、python-dotenv

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

创建 `.env` 文件，配置API密钥：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

### 4. 初始化数据库

首次运行时系统会自动创建数据库，无需手动操作。

## 🔑 如何申请DeepSeek API

### 申请步骤

1. 访问 [DeepSeek平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入 "API Keys" 页面
4. 点击 "Create new API key" 生成密钥
5. 将密钥复制到 `.env` 文件中

### 免费额度说明

- **deepseek-chat** 模型：每月免费额度较高
- 详细价格请参考官方文档

## 🎯 运行项目

```bash
streamlit run app.py
```

运行后访问 `http://localhost:8501` 即可使用。

## 📁 项目结构

```
AI StudySystem/
├── .env                    # 环境变量配置
├── requirements.txt        # 依赖列表
├── app.py                  # Streamlit主应用
├── db_init.py              # 数据库初始化脚本
├── README.md               # 项目文档
├── data/                   # 数据存储目录
│   └── notes.db            # SQLite数据库文件
└── utils/                  # 工具函数目录
    ├── __init__.py
    ├── ai_client.py        # AI接口调用封装
    └── db_operations.py    # 数据库操作封装
```

## ❓ 常见问题

### Q: API调用失败怎么办？

**可能原因及解决方案：**

1. **API Key错误**：检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. **网络问题**：确保网络可以访问 `https://api.deepseek.com`
3. **额度用尽**：登录DeepSeek平台查看API使用额度
4. **请求超时**：检查网络连接稳定性

### Q: 数据库文件在哪里？

数据库文件位于 `data/notes.db`，SQLite是轻量级数据库，所有数据存储在此文件中。

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

1. **创建笔记**：点击侧边栏"新建笔记"按钮
2. **AI总结**：查看笔记时点击"AI生成关键词和总结"按钮
3. **搜索笔记**：使用搜索框输入标题关键词
4. **日期筛选**：选择日期范围筛选笔记
5. **学习资源**：查看基于关键词推荐的学习资源链接

## 📄 许可证

MIT License

---

**享受智能学习的乐趣！** 🎉