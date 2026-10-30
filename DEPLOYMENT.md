> **当前版本 6.0.0**：已部署用户请先读 **UPGRADE-6.0-长期运行与完整流程.md**。本轮包含后端、依赖、数据库增量表、前端与监控任务，请使用完整升级包。下方 5.0 各轮说明保留作历史参考。

> 新增：完整/部分退款与奖励冲回、年费续期与到期补换卡、保留历史的销卡、可选身份验证器二次验证和恢复码、偏好同步、展示模式、日历 ICS、反馈处理、版本记录、运行告警，以及带校验和回退保护的升级工具。提供独立测试数据的 Playwright 配置；真实浏览器和截图基线须按升级说明运行并审核。

> 已完成三批升级的网站，本轮界面更新请先读 **UPGRADE-界面与移动端优化.md**（更新 app.py 和整个 static/，保留数据库与配置）。

# JWB 云端模拟体验 · 5.0

**最新：三批综合功能升级**。已完成管理员后台部署的站点请按 **UPGRADE-三批综合升级.md** 更新。本轮新增月度账单与 PDF、权益中心、比较推荐、消费分析和年度 PDF、站内通知、受控管理操作、独立演示和表单草稿。新增 ReportLab 依赖、PDF 字体及每小时维护任务；不可仅覆盖上一轮的 9 个文件。现有账户、SMTP 和备份配置保持兼容。


**上一轮：管理员后台**，地址 `/bank/admin/`。已完成第一批部署的站点请按 **UPGRADE-管理员后台.md** 更新 9 个文件。提供用户/申请/业务/总账/邮件/系统/访问审计查询及总览；后台严格只读，新增记录不会被前台 500 条限制清除。历史缺失数据明确标记，保留现有账户和资产。

已部署的 jasa.hk/bank 升级请先看 **UPGRADE-第一批优化.md**：本轮加入账户安全中心、双邮箱换绑、设备会话管理、可校验的每日备份与恢复工具、异常提示和四步体验引导。该说明包含最少覆盖文件和直接适用的宝塔命令。

保留原有六张卡片扇形首页与中英文展示，加入可部署的账户服务器。此项目不提供真实银行、支付、充值、征信或授信服务。卡号、安全码、资金和印章均用于模拟。

## 已实现

- 访客浏览、比较六种卡片；资产、换汇、消费、申请、账单与证书需要登录。
- 邮箱密码登录、邮箱验证码登录、邮箱验证码注册、找回密码、退出当前或全部设备。
- 注册后六币种余额、卡片、积分全部为零。同一邮箱登录后读取同一份服务器数据；页面可见时每 15 秒同步，亦可手动刷新。
- 服务端即时模拟审批：默认模拟年收入最低 5,000 USD，或模拟资产至少 2,500 USD；额度模型还参考模拟账龄、既有授信与本账户资产。每卡种最多一张，卡种额度上限由服务器强制执行。
- **首年模拟年费在签发时计入账单**。升级收取已付最高年费与目标年费的差额，降级不退费；原始开卡奖励进度和已用权益保留。新卡超过授信的消费会拒绝，冻结后不能消费、仍能还款。
- 模拟入金、6 币种参考价兑换、消费积分、开卡达标奖励、报销权益、USD / JR 还款、卡片冻结、安全码轮换、额度调拨。每账户每自然月一次示意结息，按 4.85% 年有效收益换算月利率；不代表真实收益。
- 实际持卡满 61 天后，每卡一次最高 3 倍初始额度提升，受卡种上限限制。申请表中的“模拟账龄”不会让已签发卡片提前满足 61 天。
- 服务端报价有效 60 秒、仅当前账户可用、成功后失效；幂等键与数据库事务避免网络重试重复扣款。余额、欠款、额度和积分计算不采信浏览器传入的结果。
- 最近 500 条交易 / 总账、CSV 导出、只读账户快照；管理员通过命令行维护注册开关和最低收入规则，界面有简要只读管理概览。
- A4 授信演示证书 PDF，包含模拟签名图样、印章和本地 ECDSA / SHA-256 验证记录。**它不是受信任 CA 证书或真实银行电子签章**；本地演示密钥不具有银行身份认证能力。JSON 验证记录嵌入 PDF 元数据。
- 自托管字体、移动端布局、键盘可用对话框、扇形卡片动效、减少动态效果偏好支持。

## 你的实际地址： https://jasa.hk/bank/

此次部署保留 jasa.hk 原有网站。应用目录仍是 `/www/wwwroot/jwb-cloud`；无需创建新站点、修改主站根目录或重新解析域名。

`.env` 使用 `PUBLIC_ORIGIN=https://jasa.hk`（这里只填来源域名，不加 /bank），另设 `BASE_PATH=/bank`。将 `deploy/nginx-bank.conf` 的两个 location 块加入现有 jasa.hk 的 HTTPS server 块。保留主站已有的 location / 和静态资源设置。`location ^~ /bank/` 专门转发银行子系统；`proxy_pass http://127.0.0.1:8895` 末尾不加斜杠。如果 /bank 已存在旧页面或代理，先备份并替换它的对应 location，避免重复。

以下安装、密钥、权限、账户初始化和启动步骤保持适用；跳过新建网站、单独空根目录及根路径代理的步骤。根域部署模板 `deploy/nginx-location.conf` 仅供另一种部署方式，不要用于此次 jasa.hk/bank 部署。

## 宝塔部署（独立域名参考）

推荐 Linux、Python 3.11 或 3.12、Nginx、HTTPS；依赖仅 Flask、Werkzeug 和 Gunicorn。数据库使用本机 SQLite WAL，适合个人长期体验和小规模访客展示。保持单台服务器、本地磁盘，不把 SQLite 放在网络共享盘。若未来需要多台实例或高并发，需迁移数据库及任务 / 缓存设施后再扩容。

### 1. 上传与安装

将压缩包中的 `jwb-cloud` 目录内容放在 `/www/wwwroot/jwb-cloud`。域名先在宝塔创建网站并配置有效 HTTPS。应用目录不要作为 Nginx 静态文件根目录，另建空目录作为站点根目录。

通过宝塔终端，以具有相应权限的管理员执行。以下 `python3.12` 按你安装的 Python 路径调整：

```bash
cd /www/wwwroot/jwb-cloud
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

将生成的随机串填入 `.env` 的 `APP_SECRET`，将 `PUBLIC_ORIGIN` 改为实际域名，如 `https://demo.example.com`，**不加末尾斜杠**。独立根域部署将 `BASE_PATH` 留空；`/bank` 部署按上一节设置。确认 `DATABASE` 路径、`COOKIE_SECURE=true`、`TRUST_PROXY=true`。保留密钥；日后更换密钥会使现有会话及验证码失效。

```bash
mkdir -p data
chown -R www:www /www/wwwroot/jwb-cloud
chmod 600 .env
chmod 700 data
```

`www` 应为你宝塔 Nginx / Python 项目使用的实际非 root 用户。数据库目录与后续管理命令也使用同一用户。

### 2. 配置发信

你目前还没有发信服务。公开注册与验证码登录需要先准备一个可用的 SMTP 账号，配置：

```dotenv
MAIL_MODE=smtp
SMTP_HOST=smtp.your-provider.example
SMTP_PORT=587
SMTP_TLS=starttls
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password-or-authorization-code
MAIL_FROM=JWB Demo <noreply@your-domain.example>
```

使用服务商要求的发信地址和授权密码。465 隐式 TLS 对应 `SMTP_PORT=465`、`SMTP_TLS=ssl`；不要使用明文模式。按照服务商说明完成域名验证与 SPF / DKIM 等发信设置，然后在网页用自己的邮箱实际测试收信、垃圾箱与重试。未配置时，网页会明确提示尚未配置，不会伪装已发送。

在邮件准备好之前，可以用下一步的命令创建自己的密码账户体验，但访客仍无法完成验证码注册。**正式部署不能使用 `MAIL_MODE=console`，该模式会将验证码写入日志，仅供本地开发。**

### 3. 初始化及管理员账户

```bash
sudo -u www .venv/bin/python manage.py init-db
sudo -u www .venv/bin/python manage.py create-user owner@example.com --admin
```

命令会交互式输入并确认 10–128 位密码，不把密码写进命令历史。管理员账户同样零资产，不提供默认密码。此命令仅供服务器所有者初始化；公开访客通过邮箱验证码注册。

### 4. 启动生产进程

两种方式任选一种，避免重复占用端口：

- 宝塔 Python 项目管理器：选择项目虚拟环境，工作目录设为 `/www/wwwroot/jwb-cloud`，运行用户 `www`，启动命令如下；添加守护和开机启动。
- systemd：调整 `deploy/jwb-cloud.service` 中路径与用户，复制为 `/etc/systemd/system/jwb-cloud.service`，执行下面命令。

启动命令：

```bash
.venv/bin/gunicorn -c gunicorn.conf.py 'app:create_app()'
```

systemd 方式：

```bash
cp deploy/jwb-cloud.service /etc/systemd/system/jwb-cloud.service
systemctl daemon-reload
systemctl enable --now jwb-cloud
systemctl status jwb-cloud
```

应用仅绑定 `127.0.0.1:8895`。不要向公网开放该端口；公网通过 Nginx 的 HTTPS 访问。不要使用 `python app.py` 的开发服务器承载正式访问。

### 5. 宝塔反向代理

将 `deploy/nginx-location.conf` 的内容加入**实际 HTTPS 网站的 `server` 块**。不要替换宝塔已有的证书、ACME 校验或 HTTPS 配置。已有 `location /` 时删除旧代理冲突项。站点应将 HTTP 跳转至 HTTPS。

反向代理将所有请求转发给应用，包括 `/assets/` 和 `/api/`。**不要新增把整个项目目录静态公开的 location / alias**。应用只允许访问指定页面与两份前端资源，`.env`、数据库、源代码和备份不会作为静态文件提供。

在宝塔检查 Nginx 配置语法后重载。`PUBLIC_ORIGIN` 必须与浏览器访问的协议、域名、端口完全一致。经过多层 CDN / 代理时，先复核转发链与信任设置，不要直接增加信任层数。

## 汇率配置与准确含义

默认服务端从 ExchangeRate-API Open 获取 USD 基准参考数据，失败时尝试 Frankfurter / ECB 数据，每小时检查一次并缓存。主源通常每日更新；界面显示数据来源及其实际更新时间。参考数据超过 7 天不接纳，抓取失败时最多使用 24 小时内缓存并提示备用；没有有效数据时停用换汇和外币消费，USD 操作仍可用。

如需更高频率的数据，在服务端配置已购买方案的 Open Exchange Rates App ID：

```dotenv
OXR_APP_ID=your-server-side-app-id
FX_REFRESH_SECONDS=60
```

订阅源优先，失败回退公共参考源；最短允许检查间隔 15 秒，但**调用频率不等于供应商数据更新频率**。请按订阅额度设置，公开默认保持 3,600 秒。App ID 不会发送到浏览器。可在供应商后台核对实际更新时间与额度。项目没有赠送或预置付费接口。

本系统的“0 汇损”仅指模拟计算不增加平台点差和手续费，兑换按目标币种的最小单位四舍五入；并非真实市场可成交报价、实时国际中间价保证或真实资金零损失承诺。需要真实交易时必须另行接入获授权的金融服务，本项目不包含该能力。

数据源官方说明：

- https://www.exchangerate-api.com/docs/free
- https://frankfurter.dev/
- https://docs.openexchangerates.org/

## 运维与备份

定期以应用用户生成一致性备份，备份路径不要在任何公开网站根目录下：

```bash
sudo -u www .venv/bin/python manage.py backup /secure-backups/jwb-2026-10-17.sqlite3
```

目标目录必须存在且应用用户可写；文件名每次不同。将数据库备份和 `.env` 分别安全保管，限制访问，不在网页中上传这些文件。网页快照包含模拟卡号与账户信息，请自行保管；不支持导入修改账户数据。

恢复请使用 `UPGRADE-第一批优化.md` 的 `verify-backup` / `restore` 流程：先验证，停止应用，再保留当前数据副本并恢复；恢复后撤销所有会话与验证码。不要手工覆盖运行中的数据库或混用旧 WAL 文件。

管理规则：

```bash
sudo -u www .venv/bin/python manage.py settings --registration closed
sudo -u www .venv/bin/python manage.py settings --registration open --min-income 5000
```

运行日志通过宝塔项目管理器或 `journalctl -u jwb-cloud` 查看。邮件密码和 APP_SECRET 不应写进前端、日志或公开仓库。SQLite 的幂等请求记录和管理员事件随使用增长；页面只展示最近记录，数据库维护需保留幂等语义，不建议直接清空生产表。

## 本地验证

```bash
.venv/bin/python -m unittest discover -s tests -v
```

自动化测试使用临时数据库与测试收件箱，不会发送真实邮件，也不会调用真实汇率网络。覆盖零账户、登录与验证码、重设密码撤销会话、账户隔离、并发幂等、审批、年费、积分、消费、冻结、还款、报价归属与单次使用等。

本地手工体验需单独 `.env`：`PUBLIC_ORIGIN=http://127.0.0.1:8895`、`COOKIE_SECURE=false`、`TRUST_PROXY=false`、`MAIL_MODE=console`，并设置自己的随机 APP_SECRET 和本地 DATABASE，然后运行 `.venv/bin/python app.py`。开发模式的验证码仅显示在终端。不要将这些开发设置带到公网部署。

已执行浏览器主流程：访客限制、密码登录、空卡包、模拟入金、规则审批签发、消费、中英文切换、390 / 768 / 1440 像素布局与 PDF 下载。真实 SMTP 发信及你服务器上的域名、HTTPS、反向代理、磁盘权限和重启恢复需要部署后验收；压缩包本身不代表已部署上线。


## 历史邮件限流修复说明

服务端统一校验发送限制后才增加计数，被冷却或额度限制拒绝的重复请求不会消耗其他发送额度。默认同一邮箱间隔 60 秒、每小时最多 6 次；同一来源 IP 每小时最多 60 次。接口返回 Retry-After 和剩余秒数，页面显示倒计时；切换登录/注册选项不会绕过同一邮箱的倒计时。

可用环境变量 `MAIL_RESEND_SECONDS`（最小 30）、`MAIL_EMAIL_HOURLY_LIMIT`、`MAIL_IP_HOURLY_LIMIT` 调整。该限制属于本网站，不代表 SMTP 服务商额度。旧版本留下的 IP 请求计数沿用原到期时间，但按新的 60 次上限判断；不需要反复清空限流表。

此前单独邮件补丁仅覆盖两份文件。当前完整第一批优化涉及更多文件，必须按 `UPGRADE-第一批优化.md` 操作；仍需保留服务器现有 `.env`、`data/`、虚拟环境与 `gunicorn.conf.py`。无需重新初始化数据库或更换密钥。
