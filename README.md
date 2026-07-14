# 🎵 BIU Music Player

轻量级 Bilibili 音乐播放器桌面版，基于 Python + Flask + pywebview 构建。登录后从收藏夹中提取音频播放，常驻系统托盘，支持播放控制。

## ✨ 特性

- **B站收藏夹音乐播放** — 登录后读取收藏夹，提取视频音频流（优先 FLAC 无损）
- **系统托盘常驻** — 关闭窗口隐藏到托盘，不占用任务栏空间，托盘菜单支持上一首/下一首/暂停
- **窗口吸附** — 推到屏幕顶部自动缩进隐藏，鼠标悬浮边缘滑出（QQ 式体验）
- **无边框窗口** — 简洁的现代深色 UI，支持拖拽移动
- **单文件分发** — PyInstaller 打包为单个 EXE，无需安装 Python 环境

## 📦 快速开始

### 环境要求

- Python 3.10+
- Windows 10+（依赖 Edge WebView2）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 打包为 EXE

```bash
pip install pyinstaller
pyinstaller BIU.spec --noconfirm
```

输出文件：`dist/BIU.exe`

## 🛠️ 技术栈

| 组件 | 用途 |
|------|------|
| Flask | 后端 API 路由 + 音频代理 |
| pywebview | 桌面窗口容器（Edge WebView2） |
| pystray | 系统托盘图标与菜单 |
| Pillow | 托盘图标处理 |
| requests | B站 API 请求 |

## 📁 项目结构

```
biu-python/
├── main.py          # 主入口：窗口管理、系统托盘、窗口吸附
├── bilibili.py      # B站 API 客户端（WBI 签名、收藏夹、播放地址）
├── routes.py        # Flask 路由注册 + JS API 桥接
├── template.py      # 前端 HTML/JS/CSS 模板
├── BIU.ico          # 应用图标
├── BIU.spec         # PyInstaller 打包配置
├── requirements.txt # Python 依赖
└── config.json      # 用户配置（本地生成，不上传）
```

## 🎮 使用说明

1. **登录** — 从 B站网页获取 `SESSDATA` Cookie，粘贴到登录框
2. **浏览收藏夹** — 登录后可查看所有收藏夹及内容
3. **播放** — 点击歌曲开始播放，支持播放列表、上一首/下一首
4. **托盘控制** — 关闭窗口自动隐藏到托盘，右键托盘图标控制播放或退出

## 📄 License

MIT
