<h1 align="center">SlideForge</h1>

<p align="center">
  <b>丢进文档，出来幻灯片</b><br>
  Word / Markdown / txt → AI 全自动 → 一整套专业幻灯片
</p>
---

## 效果展示

以下是 SlideForge 生成的真实幻灯片，来自不同项目和风格——**全部由 AI 自动生成，零人工干预**：

<p align="center">
  <img src="assets/examples/example_02_chart_dark.png" width="48%" />
  <img src="assets/examples/example_04_diagram_purple.png" width="48%" />
</p>
<p align="center">
  <img src="assets/examples/example_01_cover_dark.png" width="48%" />
  <img src="assets/examples/example_06_chart_light.png" width="48%" />
</p>
<p align="center">
  <img src="assets/examples/example_07_cover_colorful.png" width="48%" />
  <img src="assets/examples/example_08_chart_minimal.png" width="48%" />
</p>

> 深色讲座风、紫色渐变风、浅色咨询报告风、彩色几何风、极简学术风……同一份文档，换个风格就是完全不同的视觉体验。图表、流程图、数据对比——AI 会根据内容自动选择最合适的可视化方式。

---

## 它干嘛的？

你有份报告要做成 PPT？丢给 SlideForge，选个风格，等几分钟，**30-40 页专业幻灯片**就出来了。

不是那种粗糙的 AI PPT——系统会先搭叙事框架，再逐页写内容，最后统一风格出图。页与页之间风格连贯，内容有逻辑，图表跟着内容走。

```
📄 你的文档（Word / Markdown / txt）
   ↓
🧠 Step 1: AI 拆解叙事大纲（SCQA 框架）
   ↓
📝 Step 2: 每页展开 200-600 字详细内容
   ↓
🎨 Step 3: 转成 500 字精细画图指令
   ↓
🖼️ Step 4: 并行出图，一套完整的幻灯片
```

---

## 凭什么比别的 AI 幻灯片好？

### 1. 整体叙事，不是逐页拼凑

大多数 AI PPT 工具是一页一页独立生成的，30 页之间没有关联。SlideForge 不同：它先用**咨询方法论（SCQA）**搭好整体故事线——情境、冲突、问题、答案，30 页讲的是一个**完整的、有说服力的故事**。

### 2. 页与页之间互相"看得见"

生成第 15 页时，AI 能看到前面所有页的内容和画风。这意味着：
- **视觉风格全程一致**——配色、字体、排版不会突然变风格
- **内容前后呼应**——前面埋的伏笔，后面能接住
- **不会重复啰嗦**——第 20 页不会再说第 5 页说过的话

### 3. 画图指令够"变态"地详细

不是一句"画个 SWOT 分析"就完了。每页的画图指令长达 **500 字**，包含：配色方案、排版布局、数据内容、图表类型、风格标签、参考图风格描述……给到画图模型的信息越多，出图质量越高。

### 4. 参考图风格迁移

扔几张你喜欢的幻灯片进去，AI 会分析它们的**配色、排版、字体风格、视觉语言**，然后把这些特征应用到每一页。你的品牌风格、你老板喜欢的审美，都能复刻。

### 5. 断点续跑，失败无痛

网断了？API 超时？某几页不满意？**只重跑那几页就行**，已经生成好的不受影响。40 页的项目跑到第 35 页断了，不用从头来。

### 6. 多模型协同，省钱又保质

大纲用强推理模型（Claude Opus），提示词用轻量模型（Gemini Flash），画图用图片生成模型——**每一步用最合适的模型**，既保证质量，又控制成本。一套 30 页幻灯片的 API 费用通常不到 $2。

---

## 快速开始

**需要先装好**：Python 3.10+、[uv](https://docs.astral.sh/uv/)、一个兼容 OpenAI 格式的 API 密钥

```bash
# 装依赖
uv pip install -r requirements.txt

# 配置 API（复制模板，填入密钥和模型名）
cp .env.example .env

# 启动
uv run scripts/run.py
```

启动后有交互菜单，跟着走就行，不用记命令。

### 第一次用？

1. 选「新建项目」→ 起个名字
2. 给它你的文档（可以直接把文件拖进终端）
3. 选幻灯片数量和风格
4. 等它跑完，每步都能审核和调整

---

## AI Agent 一键安装

把下面这段话复制给你的 AI Agent（Claude Code / Codex / OpenCode / OpenClaw 等），它会自动帮你完成安装和配置：

> 请帮我安装 SlideForge 项目。步骤如下：
>
> 1. 克隆仓库：`git clone https://github.com/zhutyler21/SlideForge.git && cd PPT-Slide-Generator`
> 2. 安装依赖：`uv pip install -r requirements.txt`
> 3. 创建配置文件：`cp .env.example .env`
> 4. 编辑 `.env`，填入以下内容（请替换为你的实际密钥和 API 地址）：
>    ```
>    BASE_URL=你的API地址（兼容 OpenAI 格式）
>    OPENAI_API_KEY=你的API密钥
>    OUTLINE_GEN_MODEL=claude-opus-4-6
>    PROMPT_GEN_MODEL=gemini-3.1-flash-lite-preview
>    IMAGE_GEN_MODEL=gemini-3.1-flash-image-preview
>    VISION_MODEL=gemini-3.1-flash-lite-preview
>    ```
> 5. 安装完成后，帮我打开一个终端窗口，定位到项目目录。**不要代我执行启动命令。**
>
> 注意：需要 Python 3.10+ 和 [uv](https://docs.astral.sh/uv/)。如果没有 uv，先运行 `curl -LsSf https://astral.sh/uv/install.sh | sh`。

安装完成后，在终端中自己运行启动命令：

```bash
uv run scripts/run.py
```

---

## 四步流程

| 步骤 | 做什么 | 你能干预什么 |
|:---|:---|:---|
| **1. 大纲** | AI 分析文档，搭叙事框架 | 审核、修改、带反馈重来 |
| **2. 内容** | 每页展开 200-600 字 | 审核内容质量 |
| **3. 提示词** | 转成详细画图指令 | 可指定页码范围 |
| **4. 出图** | 并行生成 PNG 幻灯片 | 调并发数、只跑失败页 |

每步独立，可以单独重跑。

---

## 5 种内置风格

| 风格 | 场景 | 长什么样 |
|:---|:---|:---|
| **咨询报告** | 商业汇报、客户提案 | McKinsey 风，白底深色，专业图表 |
| **讲座** | 演讲、培训 | 深色底，大字，视觉冲击 |
| **学术汇报** | 答辩、学术会议 | 严谨排版，数据密集 |
| **漫画** | 创意、轻松场合 | 插画风，活泼配色 |
| **小学生科普** | 儿童教育 | 彩色，可爱，简单 |

想加新风格？在 `styles/` 里加个 YAML 文件就行。还可以用**参考图风格迁移**，让 AI 学习你喜欢的任何视觉风格。

---

## 环境变量

`.env` 里要配这些：

| 变量 | 干嘛的 | 例子 |
|:---|:---|:---|
| `BASE_URL` | API 地址 | `https://api.psylabs.top/v1` |
| `OPENAI_API_KEY` | API 密钥 | `sk-xxx` |
| `OUTLINE_GEN_MODEL` | 大纲模型（要聪明的） | `claude-opus-4-6` |
| `PROMPT_GEN_MODEL` | 提示词模型（轻量就行） | `gemini-3.1-flash-lite-preview` |
| `IMAGE_GEN_MODEL` | 画图模型 | `gemini-3.1-flash-image-preview` |
| `VISION_MODEL` | 看图模型 | `gemini-3.1-flash-lite-preview` |

不同步骤用不同模型，省钱又保质。

---

## 命令行用法

不想用菜单的话，也可以直接敲命令：

```bash
uv run scripts/step1_outline.py <项目名>
uv run scripts/step2_content.py <项目名>
uv run scripts/step3_prompts.py <项目名> --pages 1-10
uv run scripts/step4_images.py <项目名> --workers 4
```

---

## 项目文件

```
projects/我的项目/
├── project.json    ← 所有状态都在这
├── source/         ← 原始文档
├── references/     ← 参考图（可选）
└── output/         ← 生成的幻灯片
    ├── page_01.png
    ├── page_02.png
    └── ...
```

---

## FAQ

**能编辑生成的幻灯片吗？** — 目前生成的是 PNG 图片，暂不支持直接编辑图中的文字和元素（此功能待开发）。可以拖进 PPT / Keynote 当背景，再叠加可编辑内容。

**支持 PDF 输入吗？** — PDF 和图片作为输入文档的功能正在开发中。目前请先将 PDF 转为 Word(.docx) 或 Markdown(.md) 使用。

**支持英文吗？** — 支持中文、英文、混合。

**某几页不好看？** — 只重跑那几页：`--pages 5,12,18`，或在菜单里选「重新生成失败页面」。

**能用自己的 API 吗？** — 能。只要兼容 OpenAI 格式就行，改 `.env` 里的 `BASE_URL` 和密钥。

**一套幻灯片大概多少钱？** — 取决于页数和模型选择。30 页幻灯片通常不到 $2 的 API 费用。

---

<details>
<summary>开发者：代码结构</summary>

```
scripts/              入口脚本（run.py 主菜单，step1-4 各步骤）
src/core/             核心逻辑（解析、大纲、提示词、画图、风格）
src/tui/              交互界面（菜单、向导、各步骤 UI）
src/utils/            工具（API 客户端、终端组件、JSON 读写）
styles/               风格模板（YAML）
projects/             项目数据
```

</details>

---

## 联系作者

**GitHub**: [zhutyler21](https://github.com/zhutyler21)

欢迎扫码加微信好友交流，或打赏支持项目开发。也非常欢迎提 PR！

<p align="center">
  <img src="assets/wechat_friend.jpg" width="280" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/wechat_pay.jpg" width="280" />
</p>
<p align="center">
  <b>加个朋友，做同路人</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>请up及背后的claude喝杯咖啡</b>
</p>
