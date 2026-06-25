# 90 天路线图：把 restaurant-report-agent 从「演示骨架」做到「生产级」

> 这份 roadmap 是一个**职业训练计划**，伪装成一个**工程项目**。
>
> 你选的方向是 **系统 / 可靠性**（agent reliability / eval → 12–18 个月走向 MLOps / agent infra）。
> 抽象的 eval、observability、guardrails、CI/CD 光看是学不会的，需要一个真实的靶子。
> 这个仓库正好是一个**自洽的"演示骨架"**——它的每一个毛病，都精准对应你要练的一个能力点。
>
> **目标**：12 周后，这个 agent 是一个**真能跑、可观测、可评估、有护栏、有 CI、能自我改进**的系统；
> 同时你手里多了 3 个能写进简历、能在面试里讲 20 分钟的**作品**（eval harness / trace 看板 / 复盘文章）。
>
> **这个仓库是 dojo（道场），不是终点。** 这里练成的每一个 pattern，都能平移到你工作里那个真实的 agent 上。

---

## 它现在的真实状态（2026-06-25 核对过代码）

| 维度 | 现状 | 对应你要练的能力 |
|---|---|---|
| 能不能跑 | ❌ `api/main.py:44 USE_MOCK=True` → 图**从不执行**，返回罐头数据 | 让系统真实运行 |
| 工具调用 | ❌ `mcp_client/client.py` 全是写死 mock，高德/AntV 从不触网；`chart_bar/pie` 直接落到 error | 测试 seam / 依赖注入 |
| 可观测 | ❌ 没有 tracing，只有零星 `print`；partial error 算了但不返回给前端 | observability / OTel |
| 评估 | ❌ 0 个测试、0 个 eval、0 个 golden set | eval / LLM-as-judge ⭐ |
| 可靠性 | ⚠️ 有零散 try/except 和 `asyncio.gather(return_exceptions=True)`，但**无 retry / timeout / 熔断**，策略不统一 | resilience 原语 |
| 安全 | ❌ 真 key 进 `.env` + `快速测试.bat` 明文；CORS `allow_origins=["*"]`+`allow_credentials=True`（非法组合） | secrets / guardrails / authz |
| 工程地基 | ❌ **不是 git 仓库**，**没有 `requirements.txt`**（依赖无版本锁） | repo 卫生 / 可复现 |
| 前端 | ⚠️ `page.tsx:57` 硬编码 `localhost:8000`；`ReportContext` 内存单例，刷新即丢 | 配置管理 / 诚实 UX |

**节奏假设**：每周 = 几个专注的晚上 + 一个周末块（不是 40 小时）。慢了就顺延，别砸进度——这是马拉松。

**每周固定四件套**：🎯 目标（为什么） · ✅ 任务（锚定真实文件） · 🧠 学到的能力（简历/面试关键词） · 📐 验收（done = 什么）

---

## Week 0（Day 1–3）：止血 + 让地基能承重

🎯 在碰任何"高级"东西之前，先把会让你后面返工/出事的三件事清掉：泄露的 key、不可复现的依赖、不是仓库的仓库。这是可靠性工程师的本职，不是杂活。

✅ 任务
- [ ] **轮换泄露的 key**：`.env` 里的 `QWEN_API_KEY`、`AMAP_MAPS_API_KEY`，和 `快速测试.bat:13-20` 里硬编码的 `SILICONFLOW_API_KEY`/`AMAP_MAPS_API_KEY`——全部去对应平台**作废重发**。（它们已经在明文里躺过，必须当成已泄露。）
- [ ] 新建仓库根 `.gitignore`，至少含 `.env`、`__pycache__/`、`*.pyc`、`reports/`、`frontend/node_modules/`、`frontend/.next/`。
- [ ] 把 `快速测试.bat` 里的明文 key 删掉，改成从 `.env` 读。
- [ ] `pip freeze > requirements.txt`（或手写一份带版本的），锁住 langgraph / langchain / langchain-openai / fastapi / uvicorn / pydantic / httpx 等。
- [ ] `git init` → 确认 `git status` **看不到 `.env`** → 第一个干净 commit（`chore: initial clean commit, secrets rotated`）。
- [ ] 顺手修 CORS 非法组合：`api/main.py:18-19` 把 `allow_origins=["*"]` 改成显式 allowlist（开发期 `["http://localhost:3000"]`）。

🧠 能力：secrets management / 密钥轮换、repo 卫生、依赖锁定与可复现环境。
📐 验收：全新 clone 这个 repo + `pip install -r requirements.txt` 能装起来；`git log` 里**任何一次提交都搜不到真 key**；CORS 不再是 `*`+credentials。

---

# 月 1：先让它"真的在跑"，再让它"看得见、量得出"

> Month 1 的隐藏前提：你**不能评估/追踪一个返回罐头数据的东西**。所以前两周是"拆短路"，后两周才是 eval + observability 本体。

## Week 1：拆短路 ①——让图真的执行，让失败可见

🎯 把 `USE_MOCK` 关掉，让 `/api/analyze` 真正驱动 LangGraph 跑完 location → parallel_data →（competition_analysis?）→ report 四个节点。**先连着 mock MCP 跑**（数据确定、可复现），保证"图本身"是通的。

✅ 任务
- [ ] `api/main.py:44` 设 `USE_MOCK=False`，确认请求真的进了 `run_analysis()`（`main.py`）而不是返回罐头分支。
- [ ] 跑通一次端到端，对照 `graph/agent.py:107-128` 确认四个节点真实执行、`AgentState`（`nodes/state.py:65-92`）被逐步填上。
- [ ] **把 partial error 暴露出来**：现在各节点的失败只 merge 进 `final_state["errors"]`，但 `AnalyzeResponse` 不返回它。给响应加 `errors`/`degraded` 字段，让"哪个节点挂了"对调用方可见。
- [ ] 记录一次完整运行的耗时与大致 token，作为后面优化的 baseline（先手记也行）。

🧠 能力：读懂 agent 的真实执行路径；**让失败可观测**（partial failure surfacing）——可靠性的第一性原理。
📐 验收：`USE_MOCK=False` 下，调一次 `/api/analyze` 能拿到一份**由图真实生成**的报告；故意让某个节点抛错时，响应里能看到它降级了，而不是假装成功。

## Week 2：拆短路 ②——真实工具，但留一个干净的 seam

🎯 把 `mcp_client/client.py` 的写死 mock 换成真实 AMAP/AntV MCP（SSE）调用——**但保留 mock，做成可切换的两条路**。这个"seam"是整份 roadmap 里最重要的一个 pattern：prod 走真实，eval/test 走确定性 mock。

✅ 任务
- [ ] 把 `MCPClient` 拆成接口 + 两实现：`RealMCPClient`（真打 `AMAP_MCP_URL`/`CHART_MCP_URL` 的 SSE）和 `MockMCPClient`（现在那套 mock，保留）。用 env（如 `MCP_MODE=real|mock`）切换。
- [ ] 修 `chart_bar`/`chart_pie`：现在它们在 mock 里**没有分支 → 恒返回 `{"error": ...}`**（`client.py:105` 那条兜底）。让两条路都能真出图数据。
- [ ] 真实路径加最基础的超时（先硬编码一个值，Week 5 再系统化）。
- [ ] 决定 `chart_node`（`nodes/chart.py`，被 import+wrap 成 `_chart_node` 但**从没 `add_node`**）：要么接进图、要么明确删掉。别让死代码留着。

🧠 能力：**依赖注入 / 测试 seam**——可测性与可靠性的同一个根。这是把"demo"和"能写测试的系统"分开的那条线。
📐 验收：`MCP_MODE=mock` 完全确定可复现（给 eval 用）；`MCP_MODE=real` 能真拿到高德数据；`chart_*` 不再恒报错。

## Week 3：可观测——给每个节点装上 trace

🎯 现在它能跑了，但你"看不见"它怎么跑的。装 tracing：图、每个节点、两处 LLM 调用、每次工具调用，全部上 span。从此延迟、token 成本、工具错误能**按节点归因**。

✅ 任务
- [ ] 选一个平台落地（**建议 Langfuse**，自托管友好、对 LangChain/LangGraph 集成好；备选 Arize Phoenix / LangSmith）。装 SDK、加进 `requirements.txt`、key 走 `.env`。
- [ ] 给 LangGraph 跑链路加 trace；两处 LLM 调用——`nodes/report.py:337` 和 `nodes/competition_analysis.py:118`——单独成 span（带 model、token、耗时）。
- [ ] 工具调用（`mcp_client`）每次一个 span，记 tool_name / 入参摘要 / 成功失败 / 耗时。
- [ ] 把散落的 `print` 换成结构化 logging（`logging` 带 JSON formatter，带 request_id）。
- [ ] 在看板上看一次真实运行：哪个节点最慢？哪步最烧 token？

🧠 能力：分布式 tracing、**OpenTelemetry GenAI 语义约定**、成本/延迟归因——MLOps 核心肌肉。
📐 验收：跑一次分析，能在 Langfuse 看板上看到完整 trace 树，并能一句话回答"这次最慢/最贵的是哪个节点"。

## Week 4：评估——golden set + LLM-as-judge ⭐

🎯 这是你这条职业路的**招牌技能**。建一个小而真的评测集，定义"什么叫一份好的选址报告"，用 LLM-as-judge 自动打分，拿到 baseline。从此你改 prompt / 换模型，**有数说话**。

✅ 任务
- [ ] 建 `evals/` 目录。写一个 golden set：~15–20 条真实选址 query（你所在城市的真实地址 + 店型），存成 JSONL。
- [ ] 定义 rubric（评分维度），比如：① 事实落地（有没有用上真实 POI/竞品/交通，而不是编数字）② 覆盖度（竞品/交通/POI/天气都谈到）③ 可执行建议 ④ 无幻觉数字 ⑤ 结构清晰。每维 1–5 分。
- [ ] 实现 LLM-as-judge scorer：喂 (query, 生成报告, rubric)，让裁判模型按维度打分 + 给理由。**跑在 `MCP_MODE=mock` 的确定性路径上**，保证可复现。
- [ ] 跑全集，得到 baseline 分数表（按维度）。记下最低的两维——那就是你 Month 2 改进的靶子。
- [ ] （进阶）加一条 trajectory 检查：图有没有真的调了该调的工具（用 Week 3 的 trace 验证），而不只看最终文本。

🧠 能力：**eval 设计、rubric、LLM-as-judge、golden dataset、trajectory eval**——「agent reliability / eval 那个人」的核心标识。
📐 验收：`python -m evals.run` 一键输出一张分维度评分表；同一份代码跑两次分数稳定（mock 路径确定性）。

---

# 月 2：可靠性 + 安全硬化

> 现在它能跑、看得见、量得出了。这个月把它从"能跑"变成"扛得住、攻不动"。每一步都用 Week 4 的 eval 分数验证没把质量改坏。

## Week 5：弹性原语——retry / timeout / 熔断 / 降级

🎯 现状是零散 try/except，没有 retry、没有 timeout、没有熔断。把它统一成一套**显式弹性策略**。

✅ 任务
- [ ] 引入 `tenacity`，给 MCP 工具调用和 LLM 调用加 retry（指数退避 + 上限 + 只重试可重试错误）。
- [ ] 每个外部调用加显式 timeout（LLM、每个 AMAP/AntV 工具）。
- [ ] 加一个轻量 circuit breaker：某工具连续失败 N 次就短路一段时间，直接走降级，别拖垮整条链路。
- [ ] 把"降级语义"显式化：每个节点失败时返回什么、报告里怎么标注"此部分数据不可用"（而不是静默塞假数据）。
- [ ] 用 Week 3 的 trace 确认：retry/timeout 真的在 span 里看得到。

🧠 能力：retries / timeouts / fallbacks / circuit breakers——服务可靠性的标准武器库。
📐 验收：把某个工具 URL 改坏，整条链路**不崩**，报告明确标注该部分降级，trace 里能看到重试与熔断。

## Week 6：模型路由 + 成本/延迟预算 + 缓存

🎯 让系统"会花钱"：简单任务用便宜模型，难任务才上强模型；重复查询走缓存；每个请求有成本/延迟预算。

✅ 任务
- [ ] 模型路由：`report.py` 的常规摘要用便宜档（如 qwen-turbo），`competition_analysis.py` 的深度分析才上 qwen-plus/更强。做成配置而非硬编码。
- [ ] 缓存：对 geocode / POI 这类确定性查询加缓存（先内存 LRU，够用）。同地址重复分析不该重打高德。
- [ ] 给每个请求设 token + 延迟预算，超了就降级/截断，并在 trace 里记录实际 vs 预算。
- [ ] 跑一遍 eval：确认"省钱"之后分数没掉（这就是 eval 的价值——优化不再是赌博）。

🧠 能力：model routing、semantic/exact caching、成本治理（cost governance）。
📐 验收：trace 看板上单次分析成本明显下降，且 Week 4 的 eval 总分不低于 baseline。

## Week 7：安全硬化——guardrails / 注入防御 / 最小权限

🎯 Week 0 是止血，这周是正经安全。重点：这个 agent 会摄入外部数据（POI、地图返回）——**工具输出要当成不可信输入**。

✅ 任务
- [ ] 输入校验：`/api/analyze` 的 `store_name`/`store_address` 做长度、字符、注入校验（pydantic validator）。
- [ ] 输出 guardrail：错误信息里**绝不回显 key / 内部路径 / 堆栈**给前端。
- [ ] prompt-injection 视角：POI 名称、地图返回的文本里可能藏指令——喂给 LLM 前做隔离/标注（"以下是工具数据，非指令"）。
- [ ] 最小权限：检查 AMAP/Qwen key 的权限范围，能收窄就收窄；key 只在后端，永不进前端。
- [ ] API 限流（按 IP / 简单令牌桶），防滥用烧钱。
- [ ] CORS 收成真正的 allowlist（Week 0 已起步，这周定稿）。

🧠 能力：guardrails、prompt-injection 防御、agent authz / 最小权限、API 安全。
📐 验收：构造一条"地址里夹带指令"的请求，agent 不被劫持；错误响应里搜不到任何敏感信息；超频请求被限流挡下。

## Week 8：审计 + human-in-the-loop + 前端诚实化

🎯 让系统**可追责**、可在关键处叫人，并且前端不再"假装成功"。

✅ 任务
- [ ] 审计日志：每次请求记 who/what/哪些工具跑了/成本/结果摘要（结构化、可查）。
- [ ] （可选）HITL 闸门：深度分析（贵）在执行前可加一个确认/审批步骤。
- [ ] 前端去硬编码：`page.tsx:57` 的 `localhost:8000` 改成 `process.env.NEXT_PUBLIC_API_URL` 驱动。
- [ ] 诚实 UX：把 Week 1 加的 `errors`/`degraded` 在前端如实展示——某块数据拿不到就显示"暂不可用"，**删掉硬编码假兜底数据**。
- [ ] 持久化 `ReportContext`（localStorage 或后端存一份），刷新不丢报告。

🧠 能力：auditability、human-in-the-loop、配置管理、失败的诚实 UX。
📐 验收：能从审计日志还原任意一次分析"发生了什么、花了多少"；前端断网时显示真实降级态而非假数据；刷新页面报告还在。

---

# 月 3：CI/CD + 监控 + 数据飞轮

> 把前两个月的成果固化成"不会退化"的系统，并让它**自己越变越好**。这是从"我做了个可靠的 agent"到"我建了让 agent 持续可靠的流程"的跃迁——也是 MLOps 的本体。

## Week 9：测试 + eval-gated CI

🎯 让"质量"变成**合并的硬门槛**。改了东西，CI 自动验证没把测试和 eval 跑坏。

✅ 任务
- [ ] 写 pytest 单测：覆盖各节点（跑在 `MCP_MODE=mock` seam 上，确定可复现）、关键工具封装、API 契约。
- [ ] 把 Week 4 的 eval 接进 CI：每次提交跑 golden set，输出分数。
- [ ] **gate**：测试挂 = 不能合；eval 总分相对 baseline 跌超过阈值 = 不能合。用 GitHub Actions（顺带这也是你 Week 0 git 化的回报）。
- [ ] 加个 `make check` / 脚本，本地一键跑全套。

🧠 能力：**eval-gated CI/CD**——把"我改了个 prompt"升级成"我证明了它没退化"。这是面试里最值钱的一句话。
📐 验收：开一个故意改坏 prompt 的 PR，CI **红**并指出 eval 掉分；正常 PR 绿灯通过。

## Week 10：prompt / agent 版本化 + 安全发布

🎯 让每次"改 prompt / 改图"都可版本化、可 A/B、可回滚。

✅ 任务
- [ ] 把 prompt 和图配置从代码里抽出来做版本化（Langfuse Prompt Management 或自建版本表）。
- [ ] 实现 shadow / canary 概念：新版本先在影子模式下对真实请求跑，和旧版本比 eval 分，不影响线上。
- [ ] 明确回滚路径：一条命令/一个配置切回上一个好版本。
- [ ] 记一次"版本 A vs B"的对比结论（用数据，不用感觉）。

🧠 能力：prompt/agent versioning、canary/shadow deploy、rollback。
📐 验收：能指着两个版本号说"B 比 A 在'事实落地'维度高 0.4 分，所以上 B"；能一键回滚。

## Week 11：在线监控 + 漂移检测

🎯 离线 eval 只看测试集；线上要持续盯**真实流量**的质量、成本、延迟、错误。

✅ 任务
- [ ] 在线打分：抽样线上真实报告，用 Week 4 的 judge 打分，写回看板。
- [ ] 看板/告警：延迟、成本、错误率、质量分随时间的曲线；越过阈值告警。
- [ ] 漂移检测：质量分或输入分布明显偏移时报警（比如某城市的报告突然质量掉）。
- [ ] 定义几条 SLO（如 p95 延迟 < X、质量分 > Y、错误率 < Z%）。

🧠 能力：online eval、drift detection、SLO/可观测性闭环。
📐 验收：有一张能持续看的健康看板；人为注入一批劣质输入，漂移/质量告警能响。

## Week 12：数据飞轮 + 复盘文章（把工作变成职业资本）

🎯 闭环：让**线上失败自动变成新的评测样本**，系统自我改进；然后把这 12 周变成别人看得见的资产。

✅ 任务
- [ ] 数据飞轮：线上低分/失败的真实 trace → 人工筛 → 加进 golden set。下次 eval 自动覆盖这些坑。
- [ ] 跑通一轮完整飞轮：发现一个线上 bad case → 进 eval 集 → 改 prompt/逻辑 → eval 验证修好 → 合并。
- [ ] **写复盘**：一篇《把一个 agent 从 demo 做到生产级》——架构图、before/after 的 eval 分、trace 截图、踩的坑。发博客 / 内部分享。
- [ ] （职业动作）给团队写一页提案：把这套 eval + observability 流程用到公司真实 agent 上。

🧠 能力：data flywheel / 持续学习闭环 + **把工程成果转化为可见的职业资本**。
📐 验收：有一篇带数据的公开/内部文章；有一份能在团队里推动的提案；golden set 里至少有 1 条来自"线上发现的真实失败"。

---

## 12 周后你手里有什么

**一个系统**：一个真能跑、可观测（Langfuse trace）、可评估（golden set + judge）、有弹性（retry/熔断/降级）、有护栏（注入防御/最小权限/限流）、有 eval-gated CI、有在线监控和数据飞轮的 agent。

**三个作品**（面试/简历的硬通货）：
1. **Eval harness** —— 你能讲清楚"如何定义和度量一个 agent 的好坏"，这是多数人答不上来的。
2. **Trace 看板 + 可靠性架构** —— 你能讲"如何让 agent 扛住真实世界的故障"。
3. **复盘文章 + 数据飞轮** —— 你能讲"如何让 agent 持续不退化、并自我改进"。

**一句话定位**：你不再是"会调 LLM API 的人"，而是"**能把一个 agent 从 demo 带到生产、并让它持续可靠的人**"——这正是 agent-reliability / MLOps 岗位在找的人。

---

## 给你自己的提醒

- **每周先动手做到"验收"，再往下走。** 别堆积，别完美主义。一周一个能 demo 的小成果。
- **每一次优化都用 eval 分说话。** 这个习惯本身就是你和大多数人的分水岭。
- **RL / 后训练**：当旁修，每周读一点就行，别现在跳。等你把"系统层"这条路走扎实，再决定要不要往"模型层"下沉。
- **AI 漫剧**：严格限时的周末实验，不准侵蚀这条主线。
- **这个 repo 是道场。** 真正的目标是把这里练成的肌肉，用到你工作里那个真实 agent 上。

> 卡住了、或者想把某一周再拆细到"今晚做什么"，随时来找我。
