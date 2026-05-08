# Auto Content Factory - SKILL.md

## 🎯 技能目标
自动化内容工厂：自动注册 Seedance 2.0 获取免费积分，制作视频并上传到 YouTube 赚钱。

## ⚠️ 关键约束与注意事项
- **数据安全**：所有账户信息必须通过环境变量读取，严禁硬编码
- **模拟真人操作**：随机延迟，避免触发反自动化机制
- **可靠等待**：使用显式等待确保元素加载
- **异常处理**：完善的 try...except 逻辑，保存截图供分析
- **日志记录**：记录关键步骤执行状态

## 🚀 工作流程

### 阶段1：Seedance 注册
1. 读取环境变量配置
2. 启动 Playwright 浏览器
3. 导航到注册页面
4. 填写注册表单（邮箱、密码）
5. 处理验证码（人工介入或自动）
6. 提交注册
7. 验证注册成功，获取积分

### 阶段2：视频制作
1. 使用 Seedance API 或网页自动化生成视频
2. 下载生成的视频到本地
3. 记录视频文件路径

### 阶段3：YouTube 上传
1. 登录 YouTube Studio
2. 上传视频文件
3. 填写标题、描述、标签
4. 设置发布时间
5. 发布视频

## 📂 模块结构

```
auto-content-factory/
├── skills/
│   └── SKILL.md           # 本文件
├── scripts/
│   ├── seedance_register.py    # Seedance 注册
│   ├── seedance_generator.py   # 视频生成
│   ├── youtube_uploader.py     # YouTube 上传
│   └── main.py                # 主入口
├── mcp/
│   └── playwright_server.py   # Playwright MCP Server
├── config/
│   └── .env.example           # 环境变量模板
└── logs/
    └── automation.log         # 日志文件
```

## 🔧 环境变量配置

```bash
# Seedance 配置
SEEDANCE_URL=https://www.seedance.tv
SEEDANCE_EMAIL=your_email@gmail.com
SEEDANCE_PASSWORD=your_password

# YouTube 配置
YOUTUBE_EMAIL=your_email@gmail.com
YOUTUBE_PASSWORD=your_password
YOUTUBE_CHANNEL_ID=your_channel_id

# 通用配置
HEADLESS=false
SCREENSHOT_DIR=./logs/screenshots
```

## 📋 页面对象模型 (POM) 规范

### RegisterPage
```python
class RegisterPage:
    def enter_email(self, email)
    def enter_password(self, password)
    def click_sign_up(self)
    def handle_captcha(self)
    def wait_for_success(self)
```

### YouTubeUploadPage
```python
class YouTubeUploadPage:
    def navigate_to_upload(self)
    def upload_video(self, file_path)
    def set_title(self, title)
    def set_description(self, description)
    def add_tags(self, tags)
    def publish(self)
```

## 🛠️ 依赖安装

```bash
pip install playwright
playwright install chromium
pip install python-dotenv google-api-python-client
```

## 📖 使用方法

```bash
# 1. 配置环境变量
cp config/.env.example config/.env
vim config/.env

# 2. 运行完整流程
python scripts/main.py --mode full

# 3. 仅注册 Seedance
python scripts/main.py --mode register

# 4. 仅上传 YouTube
python scripts/main.py --mode upload --video path/to/video.mp4
```
