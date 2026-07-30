# Changelog

本项目的重要变更都会记录在这里。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- 支持 `config.yaml`、环境变量和命令行参数，并明确配置覆盖优先级。
- 新增通用 Webhook 和 Gotify 通知渠道。
- 新增 Docker Compose 部署、动态 `CHECK_CRON` 和 `TZ`。
- 新增 `config.example.yaml`、`.env.example` 和多部署方式文档。
- 新增 Email、Webhook、Gotify 通知效果展示。
- 新增配置、通知器、状态持久化和安全校验测试。

### Changed

- README 改为面向新用户的上手流程，并提供中英文版本。
- 只有所有启用的通知渠道发送成功后，才确认视频更新状态。
- 邮件增加新视频列表分隔区，并使用“万/亿”显示较大的播放量。
- Docker 在启动时动态生成 cron，并以非特权用户执行监控任务。

### Deprecated

- `src/config.py` 配置方式已弃用，计划在 v1.2 移除；v1.1 仍保留兼容回退。

### Security

- Webhook 和 Gotify URL 仅允许带有效主机名的 HTTP/HTTPS 地址。
- Docker cron 输入限制为安全字符，并阻止换行、百分号和 shell 注入。
- Docker 构建上下文排除 `.env`、`config.yaml`、数据目录和 Git 元数据。

## [1.0.1] - 2026-07-30

### Fixed

- GitHub Actions 邮箱环境变量现在会被正确读取。
- Docker 状态文件写入挂载的 `/app/data` 目录。
- 邮件发送失败时不再提前确认更新，下一次检查会重新通知。
- Actions 使用缓存保留监控状态。
- 数据文件改为原子写入并报告保存失败。

### Removed

- 删除未使用的代理配置。
- 删除 `src/1.txt`、`examples/1.txt` 和 `docx/` 占位文件。

### Tests

- 添加配置、通知提交和原子状态保存的基础测试。
