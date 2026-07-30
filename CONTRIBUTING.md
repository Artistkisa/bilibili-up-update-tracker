# 参与贡献 / Contributing

感谢你愿意帮助改进 Bilibili UP Update Tracker。Bug 修复、通知渠道、部署方式、测试和文档改进都欢迎提交。

Thank you for helping improve Bilibili UP Update Tracker. Bug fixes, notification channels, deployment options, tests, and documentation improvements are welcome.

## 开始之前 / Before you start

- 搜索现有 Issues 和 Pull Requests，避免重复工作。
- 较大的功能或行为变更请先创建 Issue，说明使用场景和建议方案。
- 安全问题不要公开提交 Issue，请通过仓库所有者提供的私密联系方式报告。
- 不要提交真实的邮箱密码、授权码、Webhook Token、Gotify Token、`.env` 或 `config.yaml`。

- Search existing Issues and Pull Requests before starting.
- Open an Issue before large features or behavior changes.
- Do not report security vulnerabilities in a public Issue.
- Never commit real passwords, authorization codes, tokens, `.env`, or `config.yaml`.

## 本地开发 / Local development

要求 Python 3.11 或更高版本。

Python 3.11 or later is required.

```bash
git clone https://github.com/Artistkisa/bilibili-up-update-tracker.git
cd bilibili-up-update-tracker
python -m venv .venv
```

Linux/macOS：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

复制示例配置进行手动测试；真实配置不会被 Git 跟踪。

Copy the example configuration for manual testing; the real configuration is ignored by Git.

```bash
cp config.example.yaml config.yaml
```

## 提交修改 / Making changes

1. 从最新 `main` 创建简短、聚焦的分支。
2. 一个 Pull Request 只处理一个主题。
3. 修改行为时同步增加或更新测试。
4. 修改配置、CLI 或部署方式时同步更新中英文 README 和示例文件。
5. 保持敏感信息、运行状态、日志和缓存文件在提交之外。

1. Create a focused branch from the latest `main`.
2. Keep each Pull Request limited to one topic.
3. Add or update tests whenever behavior changes.
4. Update both READMEs and examples when configuration, CLI, or deployment behavior changes.
5. Keep secrets, runtime state, logs, and caches out of commits.

## 测试 / Tests

提交 Pull Request 前至少运行：

Run these checks before opening a Pull Request:

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

涉及 Docker 时还需运行：

For Docker-related changes, also run:

```bash
cp .env.example .env
docker compose config
docker compose build
```

不要使用示例凭据实际发送通知。需要端到端测试时，请使用自己的测试账号和私有端点。

Do not send real notifications with example credentials. Use private test accounts and endpoints for end-to-end testing.

## 提交与 PR / Commits and pull requests

建议使用清晰的 Conventional Commits 风格：

```text
feat: add a notification channel
fix: retry state after notification failure
docs: improve Docker setup guide
test: cover invalid webhook URLs
```

Pull Request 请说明：

- 解决的问题和实现方式
- 用户可见的行为变化
- 执行过的测试
- 配置或升级注意事项

A Pull Request should describe the problem, approach, user-visible behavior, tests performed, and any configuration or migration notes.

## 代码原则 / Project guidelines

- 首次运行只建立基线，不发送历史视频。
- 通知失败时不得提前提交视频状态。
- 新配置必须遵循 `CLI > 环境变量 > YAML > 旧配置 > 默认值`。
- 外部 URL、cron、JSON 和 YAML 输入必须在使用前验证。
- 新通知渠道必须返回独立的成功或错误结果，并添加失败测试。

- First runs establish a baseline without historical notifications.
- Failed notifications must not commit video state early.
- Configuration must preserve `CLI > environment > YAML > legacy > defaults` precedence.
- Validate external URLs, cron, JSON, and YAML before use.
- New notification channels must report independent outcomes and include failure tests.

## License

提交代码即表示你同意以本项目的 [MIT License](LICENSE) 发布贡献。

By contributing, you agree that your contribution is licensed under the project's [MIT License](LICENSE).
