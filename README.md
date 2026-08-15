# seedance-studio

个人 Claude Code / Agent Skill：把一句话创意、故事或小说改编为多集短剧剧本，拆分为分镜头脚本，编译成可直接粘贴到 Seedance（即梦）2.0 / 2.5 的视频提示词，并管理多集连载的集间衔接。

- 默认 Seedance 2.0（时间轴体），可切 2.5（Shot 体）
- 输出格式：8+1 区块分镜脚本（风格画质 / 时间 / 场景 / 人物 / 分镜时间轴+内联台词 / 光影 / 肤质 / 声音 / 限制）
- 附资产参考图（C/S/P）提示词、尾帧五要素、状态胶囊（跨会话续写）、`scripts/check_prompt.py` 自检器
- 设计决策与来源见 [DESIGN.md](DESIGN.md)

## 使用方式

安装后在对话中自然触发，例如：

- 「帮我把《XX》改编成 10 集短剧」→ 全流程（迷你方案 → 大纲确认 → 剧本 → 资产图提示词 → 分镜 → 提示词）
- 「来一条 15 秒的 XX 视频提示词」→ Fast Lane 直出
- 多集项目每集附「尾帧描述」与「状态胶囊」，新会话粘贴胶囊即可续写

## 安装

本仓库为私有仓库，克隆前需配置 GitHub 认证（`gh auth login` 或 SSH key）。以下 `<repo-url>` 指本仓库地址。

### Claude Code

```bash
# 全局安装（所有项目可用）
git clone <repo-url> ~/.claude/skills/seedance-studio

# 或仅当前项目
git clone <repo-url> .claude/skills/seedance-studio
```

重启会话后自动注册，说「视频提示词 / 分镜 / 短剧」等关键词即可触发，也可用 Skill 工具显式调用。

### OpenAI Codex CLI

```bash
git clone <repo-url> ~/.codex/skills/seedance-studio
```

对话中用 `$seedance-studio` 显式调用，或描述需求隐式触发。

### 跨运行时通用目录（Codex / GitHub Copilot CLI / Gemini CLI）

以上工具均识别 `~/.agents/skills/` 作为跨运行时 skill 目录：

```bash
git clone <repo-url> ~/.agents/skills/seedance-studio
```

### Cursor / Cline / TRAE / 其他 Agent

任何能读文件、按 Markdown 指令工作的 Agent 都可使用（本 skill 无宿主私有依赖，全部为相对路径 Markdown + 一个 Python 脚本）：

1. 克隆到任意目录，如 `git clone <repo-url> ~/skills/seedance-studio`
2. 在项目规则（如 Cursor 的 Project Rules、Cline 的 .clinerules）中加入一行：
   > 当用户要生成 Seedance/即梦视频提示词、改编剧本或拆分分镜时，先读取 ~/skills/seedance-studio/SKILL.md 并严格按其指引工作。
3. 或每次对话开头直接说：「读取 ~/skills/seedance-studio/SKILL.md 并按它帮我……」

### skills CLI（社区工具，可选）

公开仓库可用 `npx skills add <owner>/<repo>` 一键安装到多种 Agent；**私有仓库需先 `gh auth login`**，或直接用上面的 git clone 方式。

## 更新

```bash
cd <安装目录>/seedance-studio && git pull
```

## 目录结构

```
SKILL.md           路由 + 五阶段流程 + 硬约束（宿主加载的入口）
references/        01采访 02剧本 03资产 04分镜 05模板2.0 06模板2.5 07连载 08词库 09敏感词 10QA
templates/         剧本 / 素材清单 / 分镜脚本(8+1区块) / 状态胶囊
examples/          黄金范例：冷宫美食工坊(2.0) / 武松打虎(2.5)
scripts/           check_prompt.py 提示词自检器
DESIGN.md          设计文档（决策记录与借鉴来源）
```
