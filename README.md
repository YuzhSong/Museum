# 中国工艺美术馆预约与导览服务平台

本项目根据《详细设计报告》实现课程作业 MVP，采用 Django + Vue 前后端分离思路，覆盖游客、管理员、志愿者/讲解员三类角色。

GitHub 仓库：[YuzhSong/Museum](https://github.com/YuzhSong/Museum)

## 功能范围

- 用户账号：游客注册、登录、退出、角色区分
- 展览与藏品：展览列表、展览详情、关联藏品、藏品详情接口
- 门票预约：场次查询、创建预约、查看个人预约、取消预约、管理员查看预约数据
- 活动报名：活动列表、活动报名、个人报名记录
- 志愿者/讲解员：浏览活动并提交参与申请，查看申请状态，管理已通过活动的报名名单
- 导览服务：推荐路线、展厅说明、文字导览
- 后台管理：管理员维护展览、藏品、活动、导览信息

## 官网参考说明

前端视觉与演示数据参考了中国工艺美术馆 中国非物质文化遗产馆官网的公开栏目，包括“服务”“展览”“活动”“典藏”“志愿者”等页面。演示数据中的展览名称、活动类型、志愿者公益讲解、典藏门类和图片素材尽量贴近官网公开信息；本项目仍为课程作业 MVP，不代表官方系统。

图片 URL 使用官网公开页面中的图片地址，便于课堂演示时呈现更贴合馆方内容的视觉效果。若离线演示或图片加载失败，系统仍可展示文字内容。

## 技术栈

- 后端：Python 3.9+、Django 4.2 LTS、Django REST Framework、SQLite
- 前端：Vue 3 CDN 单页应用、原生 CSS、Fetch API、`npm run dev` 静态服务
- 文档：README.md、编码实现报告.pdf

## 目录结构

```text
Museum/
  backend/                 Django 后端项目
    api/                   业务模型、接口、初始化数据命令
    museum_backend/        Django 配置
    requirements.txt       后端依赖清单
    manage.py
  frontend/
    index.html             Vue 单页前端
    package.json           前端本地静态服务脚本
  docs/
    coding_implementation_report.md
  编码实现报告.pdf
  README.md
```

## 环境配置

以下命令以 macOS / Linux 为准，项目根目录为：

```bash
/Users/rainy/Code/Museum/Museum
```

首次拉取后，建议先创建虚拟环境并安装后端依赖：

```bash
git clone https://github.com/YuzhSong/Museum.git
cd Museum
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py seed_demo
```

Windows PowerShell 激活虚拟环境命令：

```powershell
.venv\Scripts\Activate.ps1
```

前端当前不需要额外执行 `npm install`。`frontend/package.json` 只是封装了一个本地静态服务命令，实际页面依赖 Vue 3 CDN 运行。

## 启动方式

启动后端：

```bash
cd /Users/rainy/Code/Museum/Museum
source .venv/bin/activate
cd backend
python manage.py runserver 127.0.0.1:8000
```

可先访问健康检查接口确认后端已启动：

```text
http://127.0.0.1:8000/api/health/
```

启动前端：

```bash
cd /Users/rainy/Code/Museum/Museum/frontend
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

后端默认监听 `http://127.0.0.1:8000`，前端默认通过 `frontend/index.html` 中的 `API_BASE` 访问后端 API。如需修改后端地址，可在浏览器控制台设置：

```javascript
localStorage.setItem("museum_api_base", "http://127.0.0.1:8000/api")
```

## 演示账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | admin | admin123 |
| 游客 | visitor | visitor123 |
| 志愿者/讲解员 | volunteer | volunteer123 |

## API 说明

主要接口与详细设计报告保持一致：

- `POST /api/register/`
- `POST /api/login/`
- `GET /api/exhibitions/`
- `GET /api/exhibitions/{id}/`
- `GET /api/visit-slots/`
- `POST /api/reservations/`
- `GET /api/reservations/`
- `POST /api/reservations/{id}/cancel/`
- `GET /api/admin/reservations/`
- `GET /api/activities/`
- `POST /api/activities/{id}/register/`
- `GET /api/volunteer/activities/`
- `GET /api/volunteer/available-activities/`
- `POST /api/volunteer/activities/{id}/apply/`
- `GET /api/volunteer/my-applications/`
- `GET /api/admin/applications/`
- `POST /api/admin/applications/{id}/approve/`
- `POST /api/admin/applications/{id}/reject/`
- `GET /api/guides/`
- `POST /api/admin/exhibitions/`

登录成功后使用返回的 token：

```text
Authorization: Bearer <token>
```

## 测试

后端包含 3 个核心接口测试，覆盖游客预约/取消、管理员查看预约数据、志愿者查看报名名单。

```bash
cd /Users/rainy/Code/Museum/Museum
source .venv/bin/activate
cd backend
python manage.py test api
```

也可以执行 Django 系统检查：

```bash
python manage.py check
```

## Git 同步

当前建议主开发分支为 `codex/museum-mvp`。首次关联远程仓库：

```bash
cd /Users/rainy/Code/Museum/Museum
git remote add origin https://github.com/YuzhSong/Museum.git
git push -u origin codex/museum-mvp
```

日常提交与同步：

```bash
git status
git add .
git commit -m "Update museum platform"
git push
```

其他电脑同步最新代码：

```powershell
git pull
```

## 作业提交清单

- 源代码：`backend/`、`frontend/`
- 中间产物与文档：`docs/coding_implementation_report.md`
- 运行说明与已知问题：`README.md`
- 编码实现报告：`编码实现报告.pdf`
- 支撑材料：初始化数据命令、接口测试、演示账号

## 已知问题

- MVP 阶段未实现真实支付、实名认证、闸机核验、实时地图导航和消息通知。
- 活动报名暂不支持游客自行取消，符合详细设计报告中的 MVP 约束。
- 前端使用 Vue CDN，需要首次打开时能够访问 CDN；若离线演示，可下载 Vue 运行时后替换 `frontend/index.html` 中的 CDN 地址。
- 图片使用官网公开远程图片 URL，网络不可用时仍可展示文字信息，但图片可能无法加载。

## 初始化数据

`python manage.py seed_demo` 会创建演示账号、展览、藏品、参观场次、活动和导览数据。若需要重新初始化，可删除 `backend/db.sqlite3` 后重新执行迁移和初始化命令。
