# 编码实现报告

## 1. 项目概述

本项目实现”中国工艺美术馆预约与导览服务平台”MVP（最简可实行版本），参考中国工艺美术馆·中国非物质文化遗产馆官网的公开栏目（包括展览、活动、典藏、志愿者等），面向三类用户角色：

- **游客**：浏览展览与藏品、按日期场次预约参观门票、报名博物馆活动、查看个人预约与报名记录、浏览馆内导览信息
- **管理员**：维护展览、藏品、活动及导览信息，查看各场次预约数据，审批志愿者身份申请与活动参与申请
- **志愿者/讲解员**：先由游客提交身份申请并经管理员审批升级，再浏览可申请活动、提交参与申请、查看负责活动的报名名单

系统覆盖两条关键业务闭环：①游客从浏览展览 → 查看藏品 → 预约门票 → 确认预约的端到端流程；②管理员新增展览 → 添加藏品 → 发布 → 查看预约数据的后台维护闭环。这两个闭环构成系统 MVP 的核心价值：让游客能完成参观前的信息获取与预约操作，让管理员能维护内容并掌握预约情况。

## 2. 技术选型

后端采用 Django 4.2 LTS + Django REST Framework，数据库使用 SQLite，适合课程作业的本地部署与演示。前端采用 Vue 3 单页应用（通过 CDN 引入，详见 `frontend/index.html`），使用 Fetch API 调用 RESTful 接口。认证采用后端生成的 Bearer Token，支持过期自动失效，降低跨域和 CSRF 配置复杂度。

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Django 4.2 LTS | Python Web 框架，ORM + 路由 + 中间件 |
| API 层 | Django REST Framework | 函数视图（`@api_view`），JSON 请求/响应 |
| 数据库 | SQLite | 课程作业场景本地部署，零配置 |
| 前端 | Vue 3（CDN） | 单页应用，无构建步骤，`npm run dev` 静态服务 |
| 认证 | Bearer Token | 自维护 AuthToken 表，默认 7 天过期 |

## 3. 主要实现内容

### 3.1 用户账号模块（US-01, US-02, US-03）

- **注册**：游客通过用户名 + 密码 + 手机号 + 邮箱注册。后端校验用户名/手机号/邮箱唯一性，密码经 Django `create_user` 哈希存储。注册成功后自动签发 Token 并登录。
- **登录**：使用 Django `authenticate` 进行凭据校验，成功后生成 64 位随机 Token 存入 `AuthToken` 表。登录失败统一返回”账号或密码错误”，不区分是账号不存在还是密码错误。
- **角色区分**：通过 `Profile.role` 字段区分 visitor / admin / volunteer。后端 `require_role` 装饰器在路由层拦截无权限访问，返回 403。
- **个人中心**：已登录用户可查看个人资料（用户名、邮箱、手机号、角色、真实姓名等），可通过 `GET /api/profile/` 获取。
- **志愿者身份申请**：游客可在个人中心提交志愿者身份申请，填写意向服务方向与申请说明。管理员审核通过后，系统自动将 `Profile.role` 从 `visitor` 升级为 `volunteer`；若被拒绝，游客可修改说明后重新提交。
- **个人预约与报名记录**：游客可查看自己的门票预约记录（含预约状态、是否可取消）和活动报名记录。

### 3.2 展览与藏品模块（US-04, US-05, US-06）

- **展览列表**：无需登录即可访问，仅展示 `status=published` 的展览，按开始日期排序。每条展示名称、时间范围、展厅位置、封面图片。
- **展览详情**：点击进入后可查看展览完整信息，下方列出该展览关联的藏品列表（含藏品名称、缩略图或占位图），藏品可点击跳转到详情页。
- **藏品详情**：展示名称、类别、年代、文字介绍和图片。缺失字段统一显示”信息暂不可用”而非报错。若藏品所属展览已下架，则返回 404 而非暴露数据。
- **典藏总览**：将所有已发布展览的藏品汇总为一个典藏列表页，方便游客按门类浏览（如陶瓷、织绣、漆器、金属工艺等）。

### 3.3 门票预约模块（US-07, US-08, US-09）

- **场次查询**：游客可查看所有开放预约的参观场次（VisitSlot），每条显示日期、时间段、总容量、已预约人数、剩余名额。名额已满的场次前端按钮置灰不可选。
- **创建预约**：使用 `select_for_update()` 行级锁 + `IntegrityError` 唯一约束双重保护，确保同一用户不会重复预约同一场次，同时名额计数正确。操作在单数据库事务中完成，预约成功后 `booked_count` 自增。
- **取消预约**：游客可在”我的预约”中对状态为”已预约”且参观日期未过的记录取消。取消在事务中完成，使用 `F(“booked_count”)` 表达式回滚名额计数，避免竞态条件。
- **管理员查看预约**：管理员可按日期筛选查看所有预约记录，包含游客名、日期、时间段、预约状态。

### 3.4 活动报名模块（US-10, US-11）

- **活动列表与详情**：无需登录即可浏览已发布的活动，展示活动名称、时间、地点、人数上限、剩余名额。
- **活动报名**：已登录游客点击”立即报名”。后端检查活动状态（是否为 published）、是否已截止（`activity_time > now`）、名额是否已满、是否重复报名。
- **个人报名记录**：游客可在”我的活动报名”区域查看自己的报名历史和状态。

### 3.5 志愿者模块（US-12）

- **身份申请入口**：游客在“我的”页面可直接提交志愿者身份申请，前端实时展示当前状态（待审批 / 已通过 / 已拒绝）。
- **身份审批闭环**：管理员在后台“申请审批”中先处理志愿者身份申请；通过后账号自动进入志愿者工作台，拒绝后允许再次提交。
- **可申请活动**：志愿者登录后可浏览所有已发布活动，选择感兴趣的活动提交参与申请。
- **活动申请记录**：志愿者可查看活动申请状态（待审批 / 已通过 / 已拒绝），被拒绝后可重新申请同一活动。
- **已分配活动**：活动申请通过后，可查看负责活动的完整报名名单（含报名人用户名、手机号、报名状态）。
- **管理员审批**：管理员在同一后台标签页中分别查看“志愿者身份申请”和“活动参与申请”，逐一通过或拒绝。
- **权限校验**：志愿者只能查看自己负责活动的报名数据，访问其他活动的报名列表返回 403。
- `VolunteerRoleApplication` 表负责游客到志愿者的身份申请流程，`ActivityVolunteer` 中间表负责志愿者参与具体活动的申请-审批流程。

### 3.6 导览模块（US-13）

- 游客可查看所有导览信息（`GuideInfo`），每条包含展厅名称、推荐参观路线、文字导览、地图图片 URL。
- 导览可关联展览（`exhibition` 外键），提供”当前展期内推荐路线”的上下文。
- 若地图图片 URL 为空或加载失败，仍可正常展示文字导览内容。

### 3.7 后台内容管理模块（US-14, US-15, US-16）

- **展览管理**：管理员可新增、修改展览，支持下架（`status → closed`，下架后游客端不可见但数据保留）。修改展览时保持原有创建时间不变。
- **藏品管理**：管理员可新增、修改、删除藏品。新增时选择所属展览。藏品删除为硬删除，区别于展览的软下架。
- **活动管理**：管理员可新增、修改、下架活动，新增时可指定志愿者关联。下架后游客端不可见。
- **导览管理**：管理员可新增、修改、删除导览信息。
- **审批管理**：管理员可审批游客的志愿者身份申请，也可审批志愿者对具体活动的参与申请，便于演示完整的角色流转与分工流程。
- **权限控制**：所有 `/api/admin/*` 接口均通过 `require_role(request, “admin”)` 校验，非管理员访问返回 403。

## 4. 数据库设计

核心数据表共 11 张，关系与详细设计报告保持一致，并补充了更贴近真实业务的志愿者身份申请表：

| 表名 | 用途 | 关键字段 | 关联 |
|------|------|---------|------|
| `Profile` | 用户扩展信息 | phone, role, real_name, department, service_area | User (1:1) |
| `AuthToken` | 登录令牌 | key (64位随机hex), expires_at | User (N:1) |
| `Exhibition` | 展览信息 | title, start_date, end_date, location, status | — |
| `CollectionItem` | 藏品信息 | name, category, dynasty, description, image_url | Exhibition (N:1) |
| `VisitSlot` | 参观场次 | visit_date, time_slot, capacity, booked_count | — |
| `Reservation` | 门票预约 | status, created_at | User (N:1), VisitSlot (N:1) |
| `MuseumActivity` | 博物馆活动 | title, activity_time, capacity, status | User (M:N, through ActivityVolunteer) |
| `ActivityRegistration` | 活动报名 | register_time, status | User (N:1), MuseumActivity (N:1) |
| `GuideInfo` | 导览信息 | hall_name, route_description, text_guide, map_image_url | Exhibition (N:1, nullable) |
| `ActivityVolunteer` | 活动-志愿者关联（含申请状态） | status, applied_at | MuseumActivity (N:1), User (N:1) |
| `VolunteerRoleApplication` | 志愿者身份申请 | service_area, motivation, status, applied_at, reviewed_at | User (1:1) |

预约与场次通过 `unique_together = (“user”, “slot”)` 确保同一用户不对同一场次重复预约。活动报名同理，`unique_together = (“user”, “activity”)` 防止重复报名。`booked_count` 和 `registered_count` 通过数据库事务 + `select_for_update()` 行级锁保证并发安全。

## 5. 接口实现

接口路径基本沿用详细设计报告中的 RESTful API 设计，所有接口位于 `backend/api/urls.py`，当前共 40 条路由。核心接口清单：

**公开接口（无需登录）**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health/` | 健康检查 |
| POST | `/api/register/` | 游客注册 |
| POST | `/api/login/` | 用户登录 |
| GET | `/api/exhibitions/` | 已发布展览列表 |
| GET | `/api/exhibitions/{id}/` | 展览详情（含关联藏品） |
| GET | `/api/exhibitions/{id}/collections/` | 展览关联藏品列表 |
| GET | `/api/collections/{id}/` | 藏品详情 |
| GET | `/api/visit-slots/` | 可预约场次 |
| GET | `/api/activities/` | 活动列表 |
| GET | `/api/activities/{id}/` | 活动详情 |
| GET | `/api/guides/` | 导览列表 |
| GET | `/api/guides/{id}/` | 导览详情 |

**需登录接口**

| 方法 | 路径 | 说明 | 角色要求 |
|------|------|------|---------|
| POST | `/api/logout/` | 退出登录 | 登录用户 |
| GET | `/api/profile/` | 查看个人资料 | 登录用户 |
| GET/POST | `/api/my/volunteer-role-application/` | 查看/提交志愿者身份申请 | visitor |
| GET/POST | `/api/reservations/` | 查看个人预约 / 创建预约 | 登录用户 |
| POST | `/api/reservations/{id}/cancel/` | 取消预约 | 预约所属用户 |
| POST | `/api/activities/{id}/register/` | 报名活动 | 登录用户 |
| GET | `/api/my/activity-registrations/` | 我的活动报名 | 登录用户 |
| GET/POST | `/api/admin/exhibitions/` | 管理展览列表 / 新增 | admin |
| PUT/DELETE | `/api/admin/exhibitions/{id}/` | 修改 / 下架展览 | admin |
| GET/POST | `/api/admin/collections/` | 管理藏品列表 / 新增 | admin |
| PUT/DELETE | `/api/admin/collections/{id}/` | 修改 / 删除藏品 | admin |
| GET | `/api/admin/reservations/` | 查看预约数据 | admin |
| GET | `/api/admin/volunteers/` | 志愿者账号列表 | admin |
| GET | `/api/admin/volunteer-role-applications/` | 待审批志愿者身份申请 | admin |
| POST | `/api/admin/volunteer-role-applications/{id}/approve/` | 通过身份申请并升级角色 | admin |
| POST | `/api/admin/volunteer-role-applications/{id}/reject/` | 拒绝身份申请 | admin |
| GET/POST | `/api/admin/activities/` | 管理活动列表 / 新增 | admin |
| PUT/DELETE | `/api/admin/activities/{id}/` | 修改 / 下架活动 | admin |
| GET/POST | `/api/admin/guides/` | 管理导览列表 / 新增 | admin |
| PUT/DELETE | `/api/admin/guides/{id}/` | 修改 / 删除导览 | admin |
| GET | `/api/volunteer/activities/` | 志愿者负责活动列表 | volunteer |
| GET | `/api/volunteer/activities/{id}/registrations/` | 查看活动报名名单 | volunteer（需关联） |
| GET | `/api/volunteer/available-activities/` | 可申请活动列表 | volunteer |
| POST | `/api/volunteer/activities/{id}/apply/` | 申请参与活动 | volunteer |
| GET | `/api/volunteer/my-applications/` | 我的申请记录 | volunteer |
| GET | `/api/admin/applications/` | 待审批申请列表 | admin |
| POST | `/api/admin/applications/{id}/approve/` | 通过申请 | admin |
| POST | `/api/admin/applications/{id}/reject/` | 拒绝申请 | admin |

## 6. 前端实现

前端位于 `frontend/index.html`（当前约 3069 行），采用 Vue 3 单页应用（通过 CDN 引入 `vue.global.prod.js`），无需构建步骤即可运行。

**页面布局**：
- **Hero 区域**：品牌标识 + 系统名称 + 简介，使用馆方官网公开图片作为背景，配色参考官网的红色（品牌色 #8f1f24）、金色（#b38a3d）体系
- **信息条**：展示开馆/闭馆/入馆时间
- **顶部导航**：展览 / 典藏 / 预约 / 活动 / 导览 / 账号 / 后台 / 志愿者 八个 Tab，通过 `view` 变量切换渲染区域
- 不同角色登录后，后台 Tab 和志愿者 Tab 仅在对应角色下展示有效内容
- **活动页增强**：活动页增加“非遗体验 / 讲解活动”分类切换，活动图片与文案改为与演示数据逐条对应，详情按钮与报名人数布局同步优化
- **预约页增强**：默认展示当天日期与当天可预约时段，切换日期后再动态刷新该日期的 4 个标准时段（9-11、11-13、13-15、15-17），周一自动闭馆
- **身份申请交互**：游客账号在个人中心可以直接提交志愿者身份申请，管理员后台可即时审批并看到待办数量变化

**技术要点**：
- Token 与用户信息通过 `localStorage` 持久化，刷新页面不丢失登录状态
- 所有 API 请求统一通过 `api(path, options)` 方法发送，自动携带 `Authorization: Bearer <token>` 请求头
- 响应式布局：使用 CSS Grid + `min()` 函数，移动端（≤820px）自动切换为单列布局
- 错误提示通过 `toast()` 方法在顶部短暂显示，3.2 秒后自动消失
- `package.json` 仅封装 `npm run dev` 静态服务命令，前端不依赖 npm 依赖包

## 7. 测试与验证

后端使用 Django 自带测试框架 + DRF `APIClient`，测试文件位于 `backend/api/tests.py`，当前共 19 个测试用例，覆盖以下场景：

| 测试用例 | 验证内容 | 状态 |
|---------|---------|------|
| `test_visitor_can_reserve_and_cancel_ticket` | 游客预约 → `booked_count` 自增 → 取消 → `booked_count` 回滚 | 通过 |
| `test_admin_can_view_reservations` | 管理员查看预约数据（游客预约后管理员可查到） | 通过 |
| `test_expired_token_cannot_access_protected_endpoint` | 过期 Token（手动设置 `expires_at` 为过去时间）访问需登录接口返回 401 | 通过 |
| `test_same_user_cannot_reserve_same_slot_twice` | 同一用户重复预约同一场次返回 400 + 数据库只保留一条 | 通过 |
| `test_non_admin_cannot_access_admin_reservations` | 游客访问 `/api/admin/reservations/` 返回 403 | 通过 |
| `test_volunteer_only_sees_assigned_activity_registrations` | 志愿者只能看到被分配活动的报名名单 | 通过 |
| `test_admin_can_filter_reservations_by_time_slot` | 管理员按时间段筛选预约记录 | 通过 |
| `test_rejected_volunteer_can_reapply_for_activity` | 志愿者活动申请被拒后可再次申请 | 通过 |
| `test_visitor_can_apply_for_volunteer_role_and_admin_can_approve` | 游客提交身份申请，管理员审批后账号升级为志愿者 | 通过 |
| `test_rejected_volunteer_role_application_can_be_resubmitted` | 游客身份申请被拒后可重新提交 | 通过 |

运行方式：`python manage.py test api`，本次实现同步验证结果为 `Ran 19 tests ... OK`。测试覆盖了核心业务流程（预约→取消、身份申请→审批、活动申请→审批）、权限边界（过期 Token / 越权访问）和并发安全（重复预约防重）。

手动验证也已覆盖：展览列表浏览、游客登录、场次查询、创建预约、个人预约查看、管理员查看预约、游客提交志愿者申请、管理员审批身份申请、志愿者查看负责活动等流程。

## 8. 已知问题与后续扩展

### 8.1 MVP 阶段未实现

- 真实支付、实名认证、线下闸机核验
- 实时地图导航、消息通知
- 活动报名暂不支持游客自行取消（详细设计报告中已标注为 MVP 约束）
- 管理员审批通过后会直接升级为志愿者角色，当前尚未扩展到“多级审批 / 部门负责人会签 / 批量分配岗位”等更细粒度组织流程

### 8.2 前端局限性

- 使用 CDN 引入 Vue 3，首次打开需联网；离线演示时需下载 Vue 运行时后替换 CDN 地址
- 活动演示图片虽已切换为本地静态资源，但展览与部分导览图片仍依赖公开素材链接，完全离线演示时需继续补齐本地化资源

### 8.3 后续可扩展

- 扫码入馆核验、语音导览、用户收藏与评论
- 数据统计看板（访问量、预约趋势、热门展览分析）
- MySQL / PostgreSQL 部署替代 SQLite，适应生产环境
- 活动退报功能、志愿者岗位分配与更细的组织管理流程

## 9. AI 使用说明

### 9.1 使用工具

编码实现阶段主要使用 ChatGPT 和 GitHub Copilot（基于 OpenAI Codex）辅助完成以下工作：

- 项目目录结构设计与 Django 项目初始化
- 数据模型定义（models.py）
- 后端接口逻辑（views.py）
- 前端单页应用实现（index.html）
- 测试用例编写（tests.py）
- README.md 与编码实现报告整理

### 9.2 AI 参与度标注（按模块）

| 模块 | 文件 | AI 参与度 | 说明 |
|------|------|---------|------|
| 数据模型 | `backend/api/models.py` | 高 | AI 生成基础模型定义和关系，人工调整 `default=secrets.token_hex`、`select_for_update` 逻辑注释 |
| 后端接口 | `backend/api/views.py` | 高 | AI 生成 CRUD 框架和业务逻辑骨架，人工调整并发安全（事务+行级锁）、时区处理、错误消息中文化 |
| 测试 | `backend/api/tests.py` | 高 | AI 生成测试框架，人工调整用例边界和断言条件 |
| 路由 | `backend/api/urls.py` | 中 | AI 生成基本 URL 模式，人工逐条核对与接口函数对应 |
| 前端 | `frontend/index.html` | 高 | AI 生成页面布局和 Vue 组件逻辑，人工调整样式体系（官网配色）、响应式断点、错误处理交互 |
| 初始化数据 | `backend/api/management/commands/seed_demo.py` | 中 | AI 生成种子数据结构，人工填充具体展览、藏品、活动演示数据 |
| 文档 | `README.md`, `docs/coding_implementation_report.md` | 高 | AI 生成草稿，人工审阅修正技术表述并补充细节 |

### 9.3 AI 生成后的主要人工修改

以下列出 AI 生成代码后进行的代表性修改（非完整列表）：

1. **并发安全加固**：AI 初始生成的预约创建逻辑未使用 `select_for_update()` 行级锁。人工在 `reservations` 视图中为 `VisitSlot` 查询添加了 `select_for_update()`，并用 `transaction.atomic()` 包裹整个预约流程，配合 `IntegrityError` 捕获构成双重保护，确保在高并发预约时名额计数正确且不会重复预约。

2. **Token 过期机制**：AI 初始生成的登录方案未处理 Token 过期。人工在 `AuthToken` 模型中添加 `expires_at` 字段（默认创建后 7 天过期），并在 `current_user()` 函数中添加过期自动删除逻辑，同时在测试中加入 `test_expired_token_cannot_access_protected_endpoint` 用例验证。

3. **取消预约名额回滚**：AI 初始版本直接对 `booked_count` 做 Python 层面减法再 `save()`，存在竞态条件。人工改用 Django `F(“booked_count”) - 1` 表达式，将减法运算在数据库层面原子执行，避免多个取消操作同时发生时的计数错误。

4. **时区处理**：AI 初始版本使用了 `datetime.now()` 而非 `timezone.now()`，在非 UTC 时区下会出现场次过期判断偏差。人工将全部时间比较统一为 `timezone.now()` 和 `timezone.localdate()`，并在设置中配置了 `USE_TZ = True`。

5. **前端状态管理**：AI 初始版本将 Token 和用户信息仅保存在 Vue 组件 data 中，刷新页面即丢失。人工添加了 `localStorage` 持久化，在 `mounted` 钩子中恢复登录状态，在 `login()`/`register()`/`logout()` 中同步更新。

6. **错误消息中文化**：AI 初始生成的错误提示为英文。人工将所有面向用户的错误消息改为中文（如”该时间段名额已满或不可预约””你已预约过该场次”），并在权限拒绝（403）时给出明确说明而非通用报错。

7. **藏品缺失字段处理**：AI 初始版本对 `description` 为空时返回 `None`。人工修改为返回 `”藏品信息暂不可用。”`，确保前端不会因空值显示异常。

8. **删除策略差异化**：AI 初始版本对展览和藏品的删除操作行为一致。人工区分：展览删除采用软删除（`status → closed`，数据保留），藏品删除采用硬删除（物理删除），导览删除也为硬删除。这一差异基于业务语义——展览可能有历史预约数据需要追溯，而藏品和导览是纯内容数据。

9. **身份升级工作流补充**：AI 初始版本默认通过演示账号直接区分游客和志愿者，缺少更符合真实业务的角色流转。人工补充 `VolunteerRoleApplication` 模型、审批接口、管理员后台审批区和前端申请表单，实现“游客申请 -> 管理员审批 -> 账号升级为志愿者”的闭环。

### 9.4 Vibe Coding 过程概述

本项目采用 Vibe Coding 方式，以详细设计报告为需求基线，通过 ChatGPT 和 GitHub Copilot 与 AI 协作完成编码实现。整体工作流如下：

**第一阶段：项目初始化与环境搭建**

将详细设计报告中的技术选型部分提供给 ChatGPT，要求生成 Django 项目脚手架。包括创建项目目录结构、配置 `settings.py`（数据库、时区、INSTALLED_APPS）、生成 `requirements.txt`。AI 一次性输出了项目骨架，人工仅调整了时区设置（`USE_TZ = True`、`TIME_ZONE = 'Asia/Shanghai'`）和 ALLOWED_HOSTS 配置。

**第二阶段：数据模型设计**

将设计报告的 ER 图和 6 张核心表的字段清单逐表输入给 ChatGPT，要求生成 Django Model 定义。这一阶段是”先粗后细”的迭代过程：第一轮 AI 生成了基础模型，但缺少 `select_for_update` 注释、`unique_together` 约束、`AuthToken` 的过期机制和 `MuseumActivity` 的 M:N 志愿者关联。经过 3 轮补充提示，逐步完善了并发安全约束、Token 过期字段和活动-志愿者中间表设计。最终人工对比设计报告逐一核对字段名和关系，确认与设计一致。

**第三阶段：后端接口编写**

接口编写是迭代轮次最多的阶段。以设计报告的 API 设计章节为输入，对每个模块的接口逐批提交给 ChatGPT：
- 先提交认证模块（注册/登录/Token 校验），验证通过后再提交下一个模块
- 每个接口要求 AI 同时生成对应的权限校验逻辑
- 预约模块是最复杂的（涉及事务、行级锁、名额计数），AI 初版未考虑并发场景，经过 2 轮修改补充了 `select_for_update()` 和 `IntegrityError` 捕获
- 每批接口生成后立即在本地运行测试，发现问题即时反馈给 AI 修正

这一阶段的一个关键教训是：AI 生成的代码通常能跑通”正常路径”，但对异常路径（重复预约、过期 Token、越权访问、空字段处理）往往考虑不足。因此每批接口生成后，人工逐一构造边界条件进行测试，发现问题后再让 AI 修正。

**第四阶段：前端单页应用实现**

前端采用”需求描述 + 参考页面”的方式与 AI 协作：
1. 先向 AI 描述整体布局需求（顶部导航、Hero 区域、Tab 切换、响应式布局）
2. 要求参考中国工艺美术馆官网的配色和设计风格
3. 逐个 Tab 功能模块提交接口对接需求（如”展览 Tab 需要调用 `/api/exhibitions/` 展示卡片列表”）

AI 初版布局基本可用，但存在以下需要人工调整的问题：①CSS 配色体系不够统一（不同区域使用了不同的红色色值）；②登录状态未做 localStorage 持久化（刷新页面丢失登录）；③错误提示交互不够友好（未区分成功/错误样式）。这些问题在前述 §9.3 中均有对应修改。

**第五阶段：测试与文档**

测试用例向 AI 描述覆盖目标后生成框架，人工调整了边界断言和 `setUp` 数据。文档部分，README 和编码实现报告均由 AI 生成初稿，人工逐章修正技术细节和表述。

**总体评价**

Vibe Coding 在本项目中的效果总体良好。项目结构清晰的设计报告是关键前提——AI 在有明确输入（ER 图、API 路由表、功能列表）时输出质量高，反之则容易产生偏离需求的代码。最耗时的不是”让 AI 写代码”，而是”发现 AI 代码在边界条件下的问题并让 AI 修正”。建议后续类似项目在 Prompt 中明确列出异常场景要求（”请同时处理以下异常情况：重复预约、Token 过期、权限不足”），可以显著减少迭代轮次。

---

## 10. Prompt 示例

以下列出开发过程中各阶段使用的代表性 Prompt，每条附上使用场景和 AI 输出评价。

---

### Prompt 1 — 项目初始化

**场景**：开始编码，需要创建 Django 项目骨架。

**Prompt**：
> 我需要创建一个博物馆预约与导览服务平台的 Django 项目。技术栈：Django 4.2 LTS + Django REST Framework + SQLite。请帮我生成：
> 1. 项目目录结构
> 2. `backend/requirements.txt`（包含 django、djangorestframework、django-cors-headers）
> 3. `museum_backend/settings.py` 核心配置（数据库用 SQLite、USE_TZ=True、TIME_ZONE='Asia/Shanghai'、INSTALLED_APPS 包含 rest_framework 和 corsheaders）
> 4. `manage.py`
>
> 不需要生成任何模型或视图文件，这是第一步。

**AI 输出评价**：一次通过，生成的项目结构可直接使用。仅 `ALLOWED_HOSTS` 和 `CORS_ALLOWED_ORIGINS` 需人工根据实际前端地址调整。

---

### Prompt 2 — 数据模型设计

**场景**：根据设计报告 ER 图生成核心数据模型。

**Prompt**：
> 请帮我为博物馆预约系统生成 Django models.py。以下是核心数据表需求（字段名用 snake_case，关联关系要明确）：
>
> 1. **Profile** — 用户扩展信息：phone(unique, nullable)、role(choices: visitor/admin/volunteer)、real_name、department、service_area。与 User 一对一。
> 2. **AuthToken** — 登录令牌：key(64位随机hex, unique)、expires_at。与 User 多对一。需要自动生成 key 和过期时间（默认 7 天后）。
> 3. **Exhibition** — 展览：title、description、start_date、end_date、location、status(choices: draft/published/closed, default=published)、cover_image_url(blank=True)。
> 4. **CollectionItem** — 藏品：exhibition(FK)、name、category、dynasty、description(blank=True)、image_url(blank=True)。与 Exhibition 多对一，related_name='collections'。
> 5. **VisitSlot** — 参观场次：visit_date、time_slot、capacity(default=50)、booked_count(default=0)、status(choices: open/closed)。unique_together=(visit_date, time_slot)。
> 6. **Reservation** — 预约：user(FK)、slot(FK, PROTECT)、status(choices: active/cancelled/expired)。unique_together=(user, slot)。需要 can_cancel() 方法。
> 7. **MuseumActivity** — 活动：title、description、activity_time(DateTime)、location、capacity(default=30)、status(choices: published/closed/draft)、cover_image_url。需要 is_registerable() 方法和 registered_count/available_count 属性。与 User 的志愿者 M:N 通过 ActivityVolunteer 中间表。
> 8. **ActivityRegistration** — 活动报名：user(FK)、activity(FK)、status(choices: active/cancelled)。unique_together=(user, activity)。
> 9. **GuideInfo** — 导览：exhibition(FK, SET_NULL, nullable)、hall_name、route_description、text_guide、map_image_url。
> 10. **ActivityVolunteer** — 中间表：activity(FK)、volunteer(FK to User)。unique_together。
>
> 使用 `timezone.now()` 而非 `datetime.now()`。给所有模型添加 `__str__` 方法。

**AI 输出评价**：基础结构一次通过，但缺少以下细节，后续通过追加 Prompt 修正：
- `AuthToken.key` 未用 `secrets.token_hex` 作为 default
- `Reservation.can_cancel()` 函数体为空
- `MuseumActivity.is_registerable()` 未检查 `activity_time > timezone.now()`
- 未处理 `timezone.make_aware` 的情况

---

### Prompt 3 — 预约接口实现

**场景**：实现核心预约业务逻辑，需要并发安全。

**Prompt**：
> 帮我实现 Django REST Framework 的预约创建接口（`POST /api/reservations/`）。要求：
>
> 1. 仅登录用户可访问（从 Authorization: Bearer <token> 请求头获取当前用户）
> 2. 请求体：`{ “slot_id”: 1 }`
> 3. 需要处理以下异常情况：
>    - 用户未登录 → 返回 401 “请先登录。”
>    - slot_id 为空 → 返回 400 “请选择参观场次。”
>    - 同一用户重复预约同一场次 → 返回 400 “你已预约过该场次。”
>    - 场次名额已满或日期已过 → 返回 400 “该时间段名额已满或不可预约。”
> 4. 使用 `transaction.atomic()` 包裹整个创建流程
> 5. 在事务内使用 `select_for_update()` 锁定 VisitSlot 行，防止并发超约
> 6. 预约成功后用 `F(“booked_count”) + 1` 更新名额计数
> 7. 返回创建的预约记录 JSON（包含用户信息、场次信息、预约状态和 created_at）
>
> 同时实现 `GET /api/reservations/` 返回当前用户的预约列表（按创建时间倒序）。

**AI 输出评价**：AI 初版生成了基本的 CRUD，但缺少 `select_for_update()` 行级锁。追加提示”请添加 select_for_update 防止并发问题”后补充。`IntegrityError` 捕获是人工检查后追加的（AI 只加了 `unique_together` 约束但未捕获异常）。

---

### Prompt 4 — 前端页面实现

**场景**：生成 Vue 3 单页前端，对接已完成的 API。

**Prompt**：
> 帮我生成一个博物馆预约平台的 Vue 3 单页应用（通过 CDN 引入 Vue 3，不需构建工具）。页面需要：
>
> 1. **顶部导航栏**（sticky）：左侧品牌 logo + “预约与导览”文字，右侧 8 个 Tab 按钮（展览/典藏/预约/活动/导览/账号/后台/志愿者），最右侧显示当前登录用户名和退出按钮
> 2. **Hero 区域**：大图背景 + 系统名称”中国工艺美术馆预约与导览服务平台” + 一句话介绍
> 3. **信息条**：展示开馆时间（9:00-17:00，周一闭馆）
> 4. **展览 Tab**：调用 GET /api/exhibitions/ 获取列表，卡片网格布局展示（封面图、名称、地点、时间范围、简介）。首张卡片为 Hero 样式（大图 + 详情）
> 5. **预约 Tab**：左侧展示可预约场次（调用 /api/visit-slots/），右侧展示当前用户的预约记录（调用 /api/reservations/）
> 6. **登录/注册表单**：在账号 Tab 中
> 7. **管理员后台 Tab**：仅 admin 角色可见，包含展览管理、藏品管理、活动管理、预约数据 4 个子标签
> 8. 响应式布局：移动端（≤820px）切换为单列
> 9. 页面底色用米色（#f7f3ec），品牌色用暗红（#8f1f24），参考中国工艺美术馆官网风格
> 10. 所有 API 请求统一通过一个 `api(path, options)` 方法发送，自动携带 Authorization 头

**AI 输出评价**：初版布局框架可用，但存在以下问题需要多轮修正：
- 第 1 轮：CSS 配色不统一，Hero 区域和卡片区域使用了不同的红色
- 第 2 轮：登录状态仅存 Vue data，刷新丢失 → 要求 AI 改用 localStorage
- 第 3 轮：管理员后台子标签切换逻辑有 bug（编辑表单未正确回填数据）
- 第 4 轮：错误提示交互不佳 → 要求 AI 添加 toast 组件（3 秒自动消失，区分 success/error 样式）

最终版本约 710 行，是一次典型的”AI 出框架 → 人工发现问题 → 多轮迭代修正”的协作过程。

---

### Prompt 5 — 测试用例编写

**场景**：为核心流程编写集成测试。

**Prompt**：
> 请为 Django 博物馆预约系统编写 `backend/api/tests.py`，使用 `django.test.TestCase` 和 `rest_framework.test.APIClient`。需要覆盖以下场景（每个场景一个 test 方法）：
>
> 1. 游客预约并取消门票 — 预约后 booked_count +1，取消后 booked_count -1
> 2. 管理员查看预约数据 — 游客预约后，管理员 GET /api/admin/reservations/ 可看到该记录
> 3. 过期 Token 访问受保护接口 — 手动设置 expires_at 为过去时间后，GET /api/reservations/ 返回 401
> 4. 重复预约防重 — 同一用户对同一场次 POST 两次，第二次返回 400 且数据库只保留一条
> 5. 越权访问 — 游客 GET /api/admin/reservations/ 返回 403
> 6. 志愿者权限隔离 — 志愿者只能看到自己被分配活动的报名名单
>
> 在 setUp 中创建 visitor、admin、volunteer 三个用户和一个 VisitSlot、一个 MuseumActivity，并将 volunteer 关联到该活动。login_client 方法需封装登录逻辑（调 /api/login/ 获取 token 并设置 Authorization 头）。

**AI 输出评价**：AI 初版测试框架完整可用，但断言对 `booked_count` 的预期值未考虑并发情况下的原子性。人工在 `setUp` 中设置 `capacity=1` 以简化边界测试。此外 AI 未在 `test_expired_token` 中验证返回的具体错误消息，人工补充了 `self.assertEqual(response.json()[“detail”], “请先登录。”)` 断言。

---

### Prompt 6 — 文档整理

**场景**：生成 README 和编码实现报告初稿。

**Prompt**：
> 请为我的博物馆预约系统项目（Django 4.2 LTS + Vue 3 CDN + SQLite）生成完整的 README.md。需要包含：
> 1. 项目名称和一句话介绍
> 2. 功能范围（用户账号、展览藏品、门票预约、活动报名、志愿者、导览、后台管理 7 个模块）
> 3. 技术栈说明
> 4. 目录结构树
> 5. macOS/Linux 和 Windows 的环境配置与启动步骤（python -m venv .venv → pip install → migrate → seed_demo → runserver）
> 6. 3 个演示账号（admin/admin123、visitor/visitor123、volunteer/volunteer123）
> 7. 主要 API 路由表
> 8. 测试运行命令（manage.py test api）
> 9. 已知问题与局限性
>
> 语言用中文，格式用 Markdown。

**AI 输出评价**：AI 生成的 README 初版基本完整，但”启动方式”中未区分 macOS/Linux 和 Windows 的虚拟环境激活命令差异，人工补充了 PowerShell 的 `.venv\Scripts\Activate.ps1` 命令。此外 AI 将 Django 版本误写为”Django 6”，人工修正为”Django 4.2 LTS”。

---

## 11. 功能截图

> **【待补充：宋雨铮】** 请在此处插入各功能模块的运行截图，建议覆盖以下页面：
> - 首页展览列表（未登录状态）
> - 展览详情页（含关联藏品）
> - 藏品详情页
> - 注册/登录页面
> - 预约场次选择与预约成功
> - 我的预约记录（含取消操作）
> - 活动列表与报名
> - 管理员后台（展览管理、藏品管理、预约数据查看）
> - 志愿者活动报名查看
> - 导览信息页
>
> 每张截图下方建议标注对应的 User Story 编号（如”来源：US-04 浏览展览列表”），以便满足课程要求”说明各项功能分别来源于哪条 Feature / User Story”。
