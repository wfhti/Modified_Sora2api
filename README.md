# 本项目二次开发基于 [sora2api](https://github.com/TheSmallHanCat/sora2api)

##### 原作者: [TheSmallHanCat](https://github.com/TheSmallHanCat)

# 该项目是二开的项目请谨慎使用

---

## 项目介绍

Sora2API 是一个 OpenAI 兼容的 Sora API 服务，支持文生图、文生视频、图生视频、视频 Remix、角色创建等功能。

### 主要功能

- 文生图片 / 图生图片
- 文生视频 / 图生视频
- 视频 Remix（基于已有视频二次创作）
- 视频分镜（Storyboard）
- 角色卡创建与引用
- Token 池管理与自动轮询
- 代理配置（支持单代理和代理池轮询）
- 无水印模式
- WebDAV 上传
- 管理后台

---

## 快速开始

```bash
# Docker 部署
docker-compose up -d

# 本地部署
pip install -r requirements.txt
python main.py
```

**管理后台**: http://localhost:8000 (默认账号: admin/admin)

**默认 API Key**: `han1234`

---

## 项目结构

```
├── config/                 # 配置文件
│   ├── setting.toml       # 主配置文件
│   └── setting_warp.toml  # Warp 配置
├── data/                   # 数据目录
│   ├── hancat.db          # SQLite 数据库
│   └── proxy.txt          # 代理池配置（每行一个代理地址）
├── docs/                   # API 文档
│   ├── OPENAI_API.md      # OpenAI 标准格式 API 文档
│   └── SORA_API.md        # Sora API 文档
├── src/                    # 源代码
│   ├── api/               # API 路由
│   │   ├── admin.py       # 管理接口
│   │   ├── openai_compat.py # OpenAI 兼容接口
│   │   ├── public.py      # 公共接口
│   │   ├── routes.py      # 路由注册
│   │   └── sora_compat.py # Sora 兼容接口
│   ├── core/              # 核心模块
│   │   ├── auth.py        # 认证
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库
│   │   ├── logger.py      # 日志
│   │   └── models.py      # 数据模型
│   └── services/          # 业务服务
│       ├── generation_handler.py # 生成处理
│       ├── proxy_manager.py      # 代理管理
│       ├── sora_client.py        # Sora 客户端
│       ├── token_manager.py      # Token 管理
│       └── webdav_manager.py     # WebDAV 管理
├── static/                 # 静态文件
│   ├── login.html         # 登录页面
│   └── manage.html        # 管理后台
├── tests/                  # 测试脚本
├── docker-compose.yml      # Docker 配置
├── Dockerfile             # Docker 镜像
├── main.py                # 入口文件
└── requirements.txt       # 依赖
```

---

## API 文档

详细 API 文档请参考：
- [OpenAI 标准格式 API](docs/OPENAI_API.md)
- [Sora API](docs/SORA_API.md)

---

## 许可证

MIT License
