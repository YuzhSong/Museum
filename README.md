# 中国工艺美术馆预约与导览服务平台

本项目根据《详细设计报告》实现课程作业 MVP，采用 Django + Vue 前后端分离思路，覆盖游客、管理员、志愿者/讲解员三类角色。

## 功能范围

- 用户账号：游客注册、登录、退出、角色区分
- 展览与藏品：展览列表、展览详情、关联藏品、藏品详情接口
- 门票预约：场次查询、创建预约、查看个人预约、取消预约、管理员查看预约数据
- 活动报名：活动列表、活动报名、个人报名记录
- 志愿者/讲解员：查看自己负责活动及报名名单
- 导览服务：推荐路线、展厅说明、文字导览
- 后台管理：管理员维护展览、藏品、活动、导览信息

## 技术栈

- 后端：Python 3.14、Django 6、Django REST Framework、SQLite
- 前端：Vue 3 CDN 单页应用、原生 CSS、Fetch API
- 文档：README.md、编码实现报告.pdf

## 目录结构

```text
Museum/
  backend/                 Django 后端项目
    api/                   业务模型、接口、初始化数据命令
    museum_backend/        Django 配置
    manage.py
  frontend/
    index.html             Vue 单页前端
    package.json           静态服务脚本
  docs/
    coding_implementation_report.md
  编码实现报告.pdf
  README.md
```

## 环境配置

建议在项目根目录 `D:\Code\Museum` 执行以下命令。

```powershell
python -m pip install Django djangorestframework django-cors-headers reportlab
cd backend
python manage.py migrate
python manage.py seed_demo
```

## 启动方式

启动后端：

```powershell
cd D:\Code\Museum\backend
python manage.py runserver 127.0.0.1:8000
```

启动前端：

```powershell
cd D:\Code\Museum\frontend
python -m http.server 5173
```

浏览器访问：

```text
http://127.0.0.1:5173
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
- `GET /api/guides/`
- `POST /api/admin/exhibitions/`

登录成功后使用返回的 token：

```text
Authorization: Bearer <token>
```

## 已知问题

- MVP 阶段未实现真实支付、实名认证、闸机核验、实时地图导航和消息通知。
- 活动报名暂不支持游客自行取消，符合详细设计报告中的 MVP 约束。
- 前端使用 Vue CDN，需要首次打开时能够访问 CDN；若离线演示，可下载 Vue 运行时后替换 `frontend/index.html` 中的 CDN 地址。
- 图片使用公开远程图片 URL，网络不可用时仍可展示文字信息，但图片可能无法加载。

## 初始化数据

`python manage.py seed_demo` 会创建演示账号、展览、藏品、参观场次、活动和导览数据。若需要重新初始化，可删除 `backend/db.sqlite3` 后重新执行迁移和初始化命令。
