# seedance-studio

[![regression](https://github.com/MrYHM/seedance-studio/actions/workflows/regression.yml/badge.svg)](https://github.com/MrYHM/seedance-studio/actions/workflows/regression.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

个人 Claude Code / Agent Skill：把一句话创意、故事或小说改编为多集短剧剧本，拆分为分镜头脚本，编译成可直接粘贴到 Seedance（即梦）2.0 / 2.5 的视频提示词，并管理多集连载的集间衔接。

- 默认 Seedance 2.0（时间轴体），可切 2.5（Shot 体）
- 输出格式：8+1 区块分镜脚本（风格画质 / 时间 / 场景 / 人物 / 分镜时间轴+内联台词 / 光影 / 肤质 / 声音 / 参考 / 限制）；1 条提示词 = 1 次生成
- 单集超过单条上限时自动给出拆条/版本方案对比（2.0 N 条 / 2.5 M 条 / 2.5 超长一条）
- 附资产参考图（C/S/P）提示词、尾帧五要素、状态胶囊（跨会话续写）、`scripts/check_prompt.py` 自检器
- 设计决策与来源见 [DESIGN.md](DESIGN.md)

## 使用方式

安装后在对话中自然触发，例如：

- 「帮我把《XX》改编成 10 集短剧」→ 全流程（迷你方案 → 大纲确认 → 剧本 → 资产图提示词 → 分镜 → 提示词）
- 「来一条 15 秒的 XX 视频提示词」→ Fast Lane 直出
- 多集项目每集附「尾帧描述」与「状态胶囊」，新会话粘贴胶囊即可续写

## 安装

本 skill 为纯 Markdown + 一个 Python 脚本，无宿主私有依赖，可装到任意支持 Agent Skills 的工具中。

### Claude Code

```bash
# 全局安装（所有项目可用）
git clone https://github.com/MrYHM/seedance-studio.git ~/.claude/skills/seedance-studio

# 或仅当前项目
git clone https://github.com/MrYHM/seedance-studio.git .claude/skills/seedance-studio
```

重启会话后自动注册，说「视频提示词 / 分镜 / 短剧」等关键词即可触发，也可用 Skill 工具显式调用。

### OpenAI Codex（CLI 与 Mac 桌面应用）

```bash
git clone https://github.com/MrYHM/seedance-studio.git ~/.codex/skills/seedance-studio
```

Codex 桌面应用与 CLI 共用 `~/.codex/skills/`。对话中**优先用 `$seedance-studio` 显式调用**（比靠描述隐式触发可靠）。

### 跨运行时通用目录（GitHub Copilot CLI / Gemini CLI）

部分工具识别 `~/.agents/skills/` 作为跨运行时 skill 目录：

```bash
git clone https://github.com/MrYHM/seedance-studio.git ~/.agents/skills/seedance-studio
```

注意：有社区反馈新版 Codex 不再发现 `~/.agents/skills/` 下的本地 skill，Codex 请使用上面的 `~/.codex/skills/`。

### Cursor / Cline / TRAE / 其他 Agent

任何能读文件、按 Markdown 指令工作的 Agent 都可使用（本 skill 无宿主私有依赖，全部为相对路径 Markdown + 一个 Python 脚本）：

1. 克隆到任意目录，如 `git clone https://github.com/MrYHM/seedance-studio.git ~/skills/seedance-studio`
2. 在项目规则（如 Cursor 的 Project Rules、Cline 的 .clinerules）中加入一行：
   > 当用户要生成 Seedance/即梦视频提示词、改编剧本或拆分分镜时，先读取 ~/skills/seedance-studio/SKILL.md 并严格按其指引工作。
3. 或每次对话开头直接说：「读取 ~/skills/seedance-studio/SKILL.md 并按它帮我……」

### skills CLI（社区工具，可选）

```bash
npx skills add MrYHM/seedance-studio
```

一键安装到多种 Agent；也可直接用上面的 git clone 方式。

## 更新

```bash
cd <安装目录>/seedance-studio && git pull
```

## 目录结构

```
SKILL.md           路由 + 五阶段流程 + 硬约束（宿主加载的入口）
references/        01采访 02剧本 03资产 04分镜 05模板2.0 06模板2.5 07连载 08词库 09敏感词 10QA 11拆条 12调参
templates/         剧本 / 素材清单 / 分镜脚本(8+1区块) / 状态胶囊
examples/          黄金范例：冷宫美食工坊(2.0) / 武松打虎(2.5)
scripts/           check_prompt.py 提示词自检器
DESIGN.md          设计文档（决策记录与借鉴来源）
LICENSE            MIT
THIRD-PARTY-NOTICES.md  第三方参考项目署名与许可
```

## 许可证

[MIT](LICENSE) © 2026 MrYHM

本项目参考了若干社区项目的方法论，署名与许可信息见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

## 声明

Seedance、即梦为字节跳动的产品与商标，Claude Code 为 Anthropic 的产品，Codex 为 OpenAI 的产品。本项目是独立的第三方工具，与上述公司无隶属、赞助或背书关系，提及这些名称仅用于说明兼容性。

本 skill 只产出文本提示词，不调用任何视频生成 API，也不附带任何模型权重或平台凭证。使用时请遵守所用平台的服务条款与内容政策。

## 贡献

`main` 分支受保护，所有改动走 PR：fork → 建分支 → 提 PR。PR 会自动跑回归（校验器 12 项用例 + SKILL.md 结构自检），通过并经 review 后合并。

本地跑回归：

```bash
python3 tests/run_regression.py
```

改动 `SKILL.md` 的硬约束或新增 `references/` 文件时，请确认编号连续且交叉引用有效——CI 会检查这两项。

## 反馈

欢迎提 issue 讨论分镜方法论、提示词结构或平台参数的变化。
