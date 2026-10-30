# 界面与移动端优化升级

适用于已经完成“三批综合升级”的 https://jasa.hk/bank/。本轮为界面重构，仅在 app.py 增加两份静态资源的允许项；账户、审批、资金、权益、邮件及定时任务业务规则保持不变。已有数据库和账户继续使用。

## 本轮改动

- 登录默认进入账户概览：模拟资产、待还、积分、四个常用操作和最近五笔交易。引导折叠，完整交易记录独立查看。
- 主导航收敛为首页、卡片、账户、我的。桌面工作台分组侧栏；手机和平板使用底部四栏及栏目内导航；通知从顶部铃铛进入。完整卡片目录从侧栏“探索全部卡片”或卡片栏目“探索”进入。
- 桌面保留六卡扇形；手机先短暂展开六卡，再收拢为原生横滑的大卡片。开启减少动态效果时直接显示可操作布局；点击卡片打开详情，申请按钮进入原申请流程。
- 卡片目录只保留卡面、介绍、年费和奖励摘要。完整礼遇在详情展开；卡包管理、额度调拨及安全设置按需展开。
- 手机账单、消费明细和后台表格转为带字段标签的记录列表；卡片比较仍保留独立横向滚动表格与固定项目列。
- 手机消费分析筛选放入底部抽屉；表单改为单列，输入字号 16px，按钮触控区域至少 44px。弹窗适配视口与底部安全区域，软键盘出现时按可用视口调整。
- 统一字体、色彩、间距、边框和金额层级；关闭持续脉冲、重复卡面扫光及大范围模糊动效，保留短暂页面切换和卡片首次展开。
- 后台导航改为手机可折叠菜单，筛选按需展开；独立演示改善手机字体、按钮、间距与安全区域。

## 部署步骤

### 1. 备份

宝塔终端执行：

```bash
cd /www/wwwroot/jwb-cloud
sudo -u www .venv/bin/python manage.py backup "/www/backup/jwb-cloud/before-ui-$(date +%Y%m%d-%H%M%S).sqlite3"
```

确认 `Verified backup saved`。另存现有 app.py 与 static/，用于回退。

### 2. 暂停服务

```bash
systemctl stop jwb-maintenance.timer jwb-backup.timer
systemctl stop jwb-cloud
```

### 3. 上传

从最新版包内 jwb-cloud/ 中，将 **app.py** 覆盖到 `/www/wwwroot/jwb-cloud/app.py`，将 **static/ 中所有文件合并覆盖**至服务器的 `/www/wwwroot/jwb-cloud/static/`。

必须包含新增 `ui.js` 和 `ui.css`，以及更新的 index.html、cloud.js、suite.js、suite.css、admin.html、admin.js、admin.css、fonts.css。app.py 不能漏：缺少它会导致新资源 404。

保留 `.env`、`data/`、`.venv/`、`gunicorn.conf.py`、fonts/ 和已有 deploy/ 配置；目录不要多套一层 jwb-cloud。

如果尚未完成“三批综合升级”，先按 `UPGRADE-三批综合升级.md` 安装依赖、字库和维护定时器，再覆盖本轮界面文件。新装请使用 README 的完整部署流程。

### 4. 恢复

```bash
cd /www/wwwroot/jwb-cloud
chown www:www app.py
chown -R www:www static
systemctl start jwb-cloud
systemctl status jwb-cloud --no-pager -l
```

确认 `active (running)`，然后执行：

```bash
systemctl start jwb-maintenance.timer jwb-backup.timer
systemctl list-timers --all jwb-maintenance.timer jwb-backup.timer --no-pager
```

本轮无需修改 `.env`、SMTP、Nginx、域名、端口或安装新的 Python 依赖。

### 5. 刷新与验收

电脑 Ctrl+F5，手机关闭旧标签页后重开 https://jasa.hk/bank/。

- 未登录：首页能浏览六卡，点击打开详情；进入账户、申请或我的时出现登录。
- 已登录：默认账户概览；底部四栏和栏目内导航可到达全部功能；铃铛显示未读数量。
- 手机：首次六卡展开后变为横滑卡片；竖向滚动和横滑互不阻塞；320px 小屏至平板无页面横向溢出。
- 比较最多三卡；长表格只在表格自身区域横滑。手机账单和明细显示字段标签。
- 测试消费分析抽屉输入、关闭、重开、提交和中英文切换；筛选结果与原数据一致。
- 测试申请、入金、换汇、消费、部分还款。草稿可在栏目切换后恢复；退出登录后清空。
- 输入键盘弹出时检查最后一项、错误提示、提交按钮和关闭按钮可以通过内部滚动到达。
- 检查月度和年度 PDF、授信证书下载，以及管理员查询和管理操作。
- iPhone Safari、Android Chrome、iPad/平板、电脑浏览器各检查一次；横屏、200% 缩放和减少动态效果偏好一并检查。

出错时查看：

```bash
journalctl -u jwb-cloud -n 100 --no-pager -l
```

新界面无样式：检查 app.py 和 static/ui.css、static/ui.js 是否均已覆盖，并强制刷新。程序回退只需恢复备份的 app.py 与 static/ 后重启服务，不回退数据库。

## 验证范围

57 项 Python 回归检查通过（本轮更新了子目录资源加载检查，包含新资源与缓存版本参数），中英文用户界面与后台 DOM 交互检查通过；额外检查 320、375、390、768、1024、1440px 的结构与导航、表单草稿、详情、访客门槛及筛选抽屉交互。结构测试不等同于真实浏览器排版测试。当前环境未提供真实浏览器视觉验收，实际设备效果请按上面的清单确认。
