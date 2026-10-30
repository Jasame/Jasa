# 显示与交互修复（2026-10-18）

适用于 https://jasa.hk/bank/ 已完成三批功能升级及界面优化的站点。本次不改变模拟资金、授信、审批、账单结算或权益规则，不迁移或清空数据库。

## 已确认并修复

1. **管理员后台桌面侧栏消失**：上版使用关闭状态的原生 details 包裹导航。display:contents 无法解除浏览器对关闭内容的隐藏。现改为普通容器和有 aria-expanded 状态的手机菜单按钮，桌面始终显示导航，手机按需展开。
2. **月度账单大片留白**：收起的设置和全部卡片欠款共享网格行，行高被整列欠款撑开。现按欠款汇总、卡片明细、还款/周期设置、历史账单独立排版。欠款卡片按设备宽度排列；不再把整个卡包塞进半屏长列。
3. **账单信息不清晰**：显示完整产品名与后四位；没有已出账待还时禁用相应还款按钮；首份账单尚未生成时展示说明与下一账单日，不显示一张空表。出账余额和当前未结清金额分列。
4. **折叠状态与重复增强**：周期设置、权益、卡片管理等折叠状态按账户/栏目/卡片保留在本页内存；增强重复执行不再嵌套卡片选择条或移动已经包裹的权益内容。退出登录清空状态。
5. **刷新和按钮状态**：手动刷新现在会重新加载当前栏目，即使账户修订号没有变化；自动刷新避免替换正在操作的内容。命令结束只恢复本次临时禁用的按钮，保留无报价、无已出账余额等条件下的禁用状态。
6. **异步结果**：离开换汇页、重新渲染或修改输入会使旧报价失效；旧会话请求不能在同一个用户重新登录后写回新会话。操作完成不会强行把已离开的栏目切回原栏目。下载检查账户与会话仍匹配。
7. **手机筛选抽屉**：主动关闭或提交前先将表单放回原栏目，避免异步 close 事件尚未触发时重开、提交或换语言丢失表单。原生取消关闭也会恢复表单。
8. **其他体验**：保留未提交的比较预算；通知分页在边界禁用；JPY 金额输入采用整数精度；资产汇率加载后更新首页参考估值；历史无效日期不再显示 Invalid Date。后台长编号、邮箱、金额、移动表格与侧栏滚动补充约束。
9. **独立演示**：增加超时和取消旧请求；网络失败状态在中英文切换后保留，避免变成一直加载；可正常重试。
10. **缓存**：相关入口资源版本更新为 20261018-3，避免继续加载上版脚本与样式。

## 部署：更新 app.py 和整个 static/

### 1. 备份

宝塔终端执行，确认 `Verified backup saved` 后继续。另存现有 app.py 和 static/ 副本便于回退。

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py backup "/www/backup/jwb-cloud/before-display-fix-$(date +%Y%m%d-%H%M%S).sqlite3"
```

### 2. 暂停服务

```bash
systemctl stop jwb-maintenance.timer jwb-backup.timer
systemctl stop jwb-cloud
```

### 3. 上传

将包内 jwb-cloud/app.py 覆盖到 `/www/wwwroot/jwb-cloud/app.py`，将 **static/ 内所有文件合并覆盖**到 `/www/wwwroot/jwb-cloud/static/`。

至少检查 index.html、cloud.js、suite.js、ui.js、ui.css、admin.html、admin.js、admin.css、demo.html、demo.js、fonts.css 已上传。不要只上传截图对应的两个样式文件，否则交互修复不会生效。

保留服务器现有 `.env`、`data/`、`.venv/`、fonts/、gunicorn.conf.py、deploy/。不修改 Nginx、域名、端口、邮箱或密钥。本轮没有新增 Python 依赖，不重新初始化用户或数据库。

如果尚未完成三批功能升级，请先按 `UPGRADE-三批综合升级.md` 安装 ReportLab、PDF 字库和维护任务，然后使用本轮最新界面文件。

### 4. 启动

```bash
cd /www/wwwroot/jwb-cloud
chown www:www app.py
chown -R www:www static
systemctl start jwb-cloud
systemctl status jwb-cloud --no-pager -l
```

确认 `active (running)` 后：

```bash
systemctl start jwb-maintenance.timer jwb-backup.timer
systemctl list-timers --all jwb-maintenance.timer jwb-backup.timer --no-pager
```

### 5. 验收

电脑 Ctrl+F5；手机关闭旧标签页重新进入。

- 后台：电脑左侧八个栏目可见；手机点击栏目菜单展开，切换栏目正常；搜索、筛选、分页、详情和管理密码错误反馈正常。
- 月度账单：顶部有总欠款/已出账/未出账，完整产品名正确；设置折叠时没有整列空白。展开设置后刷新、切换语言，状态与输入仍保留。无已出账待还的卡片按钮禁用。
- 业务：核对原有资产、卡片、积分；测试消费、换汇、还款和 PDF。第一份账单须到真实账单日才出现，不改服务器时间催出账。
- 手机：测试筛选抽屉输入、关闭重开、查询；卡片详情、表单、键盘、横屏及中文/英文切换。电脑和手机分别检查长金额和长商户名称。
- 退出登录后，工作台内容、表单草稿、折叠状态和筛选偏好清空；重新登录后从服务端加载账户。
- 独立演示网络失败后保留错误提示，换语言不会变成无限加载，重试可恢复。

出错时：

```bash
journalctl -u jwb-cloud -n 80 --no-pager -l
```

若页面仍旧，检查入口所请求的 ui.js、ui.css、admin.js、admin.css 是否带 `v=20261018-3` 且返回 200。回退仅恢复先前 app.py/static/ 并重启服务，不回退数据库。

## 验证范围

57 项 Python 回归测试通过。后台八个栏目中英文交互、权限错误、筛选、详情、管理操作、恶意文本转义通过 DOM 检查。用户界面以 320、375、390、768、1024、1440px 检查结构与原生事件，包括后台导航不能位于关闭的原生折叠元素中、账单分区、重复增强、草稿、筛选归位、折叠保留、按钮状态和旧报价失效。演示错误/换语言/重试及 CSS 语法检查通过。

提供 tests/frontend_fixtures.py、tests/frontend_regression.cjs、tests/admin_frontend_regression.cjs 便于复查。前端测试需要开发用 jsdom，不需要安装在生产服务器。

本环境未提供真实浏览器视觉预览；DOM 检查不能代替浏览器布局和真实设备验收。此次修复覆盖已确认缺陷，不承诺所有浏览器与未来数据场景绝无缺陷。
