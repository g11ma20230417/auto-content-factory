# Auto Content Factory - SKILL.md

## 🎯 技能目标
自动化内容工厂：使用 VEOAIFree 免费生成 Google VEO AI 视频，上传到 YouTube 赚钱。

## ⚠️ 关键约束与注意事项
- **数据安全**：所有账户信息必须通过环境变量读取，严禁硬编码
- **模拟真人操作**：随机延迟，避免触发反自动化机制
- **可靠等待**：使用显式等待确保元素加载
- **异常处理**：完善的 try...except 逻辑，保存截图供分析
- **日志记录**：记录关键步骤执行状态

## 🚀 工作流程

### 阶段1：VEOAIFree 视频生成
1. 启动 Playwright 浏览器
2. 导航到 https://veoaifree.com/veo-video-generator/
3. 输入视频描述提示词
4. 选择 VEO 版本 (3.0 或 2.0)
5. 选择视频比例 (16:9/9:16/1:1)
6. 点击生成按钮
7. 等待视频生成完成
8. 下载生成的视频

### 阶段2：YouTube 上传
1. 登录 YouTube Studio
2. 上传视频文件
3. 填写标题、描述、标签
4. 发布视频

## 📂 模块结构

```
auto-content-factory/
├── skills/
│   └── SKILL.md              # 本文件
├── scripts/
│   ├── main.py               # 主入口
│   ├── veoaifree_generator.py # VEOAIFree 视频生成
│   └── youtube_uploader.py    # YouTube 上传
├── mcp/
│   └── playwright_server.py   # Playwright MCP Server
├── config/
│   └── .env.example          # 环境变量模板
└── logs/
    └── screenshots/          # 截图目录
```

## 🔧 环境变量配置

```bash
# YouTube 配置
YOUTUBE_EMAIL=your_email@gmail.com
YOUTUBE_PASSWORD=your_password

# 浏览器配置
HEADLESS=false
SLOW_MO=100

# 路径配置
SCREENSHOT_DIR=./logs/screenshots
VIDEO_OUTPUT_DIR=./output/videos
LOG_FILE=./logs/automation.log
```

## 🛠️ VEOAIFree 特性

- ✅ **完全免费** - 无需注册账号
- ✅ **无限使用** - 无次数限制
- ✅ **Google VEO AI** - 支持 VEO 2.0 和 3.0
- ✅ **无水印** - 视频无任何水印
- ✅ **快速生成** - AI 智能加速渲染

## 📖 使用方法

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp config/.env.example config/.env
vim config/.env

# 3. 生成视频
python scripts/veoaifree_generator.py "A sunset over mountains"

# 4. 指定版本和比例
python scripts/veoaifree_generator.py "Futuristic city" 3.0 16:9

# 5. 上传到 YouTube
python scripts/main.py --mode upload --video ./video.mp4 --title "My AI Video"

# 6. 完整流水线
python scripts/main.py --mode full
```

## 🎬 提示词示例

```
A majestic mountain landscape at sunrise with golden light
Futuristic city with flying cars and neon lights at night
Peaceful ocean waves crashing on a tropical beach
Northern lights dancing across the Arctic sky
Cherry blossoms falling in a traditional Japanese garden
Aerial view of a forest with misty morning fog
Wild horses running across a green meadow
A cozy coffee shop with rain outside the window
```

## 📊 支持的参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --mode | 运行模式 | full |
| --prompt | 视频提示词 | 随机选择 |
| --version | VEO 版本 (3.0/2.0) | 3.0 |
| --ratio | 视频比例 (16:9/9:16/1:1) | 16:9 |
| --video | 视频路径 (上传模式) | - |
| --title | YouTube 标题 | 默认 |
| --description | YouTube 描述 | 默认 |
| --tags | YouTube 标签 (逗号分隔) | 默认 |
