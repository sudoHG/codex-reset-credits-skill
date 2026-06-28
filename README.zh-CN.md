# codex-reset-credits-skill

[English](README.md)

`codex-reset-credits-skill` 打包了一个名为 `codex-reset-credits` 的 Codex Skill。

它可以让 Codex 从本机 Codex Desktop 登录态中只读查询 banked Codex reset credits，并返回当前可用次数和到期时间。查询逻辑是本地优先、只读的：读取 `${CODEX_HOME:-~/.codex}/auth.json`，请求 ChatGPT 后端 reset-credit 端点，并且只输出脱敏结果。

本项目是非官方项目，不隶属于 OpenAI。

## 直接给 Codex 使用

把这个文件发给 Codex：

```text
https://github.com/sudoHG/codex-reset-credits-skill/blob/main/USE_WITH_CODEX.md
```

然后说：

```text
帮我查询 Codex 重置次数和到期时间
```

Codex 会读取 runbook，在本机运行查询脚本，并返回一个干净的摘要表格。

## 安装为 Codex Skill

把 Skill 目录复制到你的 Codex skills 目录：

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R codex-reset-credits "${CODEX_HOME:-$HOME/.codex}/skills/codex-reset-credits"
```

重启 Codex 或打开一个新的 Codex 会话。然后直接问：

```text
帮我查一下 Codex 重置机会还有几个，什么时候过期
```

## 直接作为 CLI 使用

```sh
python3 codex-reset-credits/scripts/query_reset_credits.py --human
python3 codex-reset-credits/scripts/query_reset_credits.py --json
```

`--human` 输出示例：

```markdown
Codex reset credits

| Summary | Value |
| --- | --- |
| Available reset credits | `3` |
| Earliest expiration | `2026-07-16 15:51:44 CST` |

| # | Status | Type | Expires local | Expires UTC | ID suffix |
| --- | --- | --- | --- | --- | --- |
| 1 | `available` | `codex_rate_limits` | 2026-07-16 15:51:44 CST | 2026-07-16 07:51:44 UTC | `c60e4307` |
```

## 安全边界

- 不要把 token 粘贴给 Codex。
- 脚本读取的是本机 Codex Desktop 登录态。
- 脚本不得打印 access token、完整 `auth.json`、完整 account id、完整 credit id 或后端原始响应。
- 脚本不会 redeem reset credits。
- 脚本不会调用 mutation 或 control 端点。
- 后端端点不是公开稳定 API；鉴权方式或响应结构可能变化。

## 验证

```sh
python3 -m unittest discover -s tests -v
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-reset-credits
```

## 许可证

MIT。
