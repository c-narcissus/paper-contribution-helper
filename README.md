# 论文贡献助手

`paper-contribution-helper skill`（中文名：论文贡献助手）是给 **A+B+C 式组合创新**、增量创新、工程创新、轻改迁移和旧方法新场景适配类论文准备的 Codex 投稿辅助 skill 工厂。很多研究生和早期科研作者并不是“没有做东西”，而是论文贡献容易被写成“把 A、B、C 拼在一起”，导致审稿人质疑 novelty 不够、只是 incremental、机制证据不足、baseline 不公平或 scope 过大。这个 skill 就是为了解决“工作做了，但贡献讲不清、审稿防不住”的痛点：把已有方法、实验和约束重新组织成更清楚、更强、更可防守的投稿叙事。感谢 University of Bristol 的刘欣阳同学提供 SemiDFL 素材支持。

![paper-contribution-helper skill architecture, Chinese](paper-contribution-helper-skill-architecture-zh.png)

它有两种核心用法：一种是直接利用主包内置的贡献包装知识库分析当前论文，快速得到 contribution framing、novelty defense、reviewer attack preplay 和 revision plan；另一种是在 **Codex 中**把目标论文作为 seed，自动收集同领域论文、reviews、author replies 和 meta-reviews，生成一个可反复复用的领域专用 helper skill，后续同方向论文可以继续用这个 child skill 做贡献包装和审稿防守。注意：**ChatGPT 网页版不能生成领域专用 helper skill**，只能直接使用主包内置知识库分析论文，或使用已经在 Codex 中生成好的 child skill。

注意：如果 Codex 过程中断，并显示类似“还没有生成最终 skill zip。原因是当前环境没有 OPENAI_API_KEY、acpx 或本地 LLM 后端”的信息，请回复：

```text
不对啊。我这里说了使用 Codex 来编排进行深度阅读。
```

SemiDFL 样例里，最关键的改写不是继续强调“我们组合了几个模块”，而是把论文从 **component-combination paper** 改写成 **interface-closure paper**。

| 容易被读成 | 更强的贡献叙事 |
| --- | --- |
| 把 NPL、diffusion MixUp、AdaGen 拼在一起 | semi-supervised DFL 缺少三个 consensus interfaces，SemiDFL 分别闭合 label-space、data-space、model-space 三个接口 |
| 实验只是报告 accuracy 更高 | 实验围绕 reviewer 会追问的失败模式组织：label scarcity、non-IID robustness、pseudo-supervision quality、data-space consensus、model-space consensus |

这样写的好处是：不需要编造新实验，也不把已有工作降格成“简单组合”，而是把论文真实解决的问题、已有证据和审稿防守点对齐起来。

核心原则是 **强而诚实**：不编造、不夸大、不脱离论文内容，而是最大化挖掘论文中真实存在但没有讲透的亮点，让“看起来只是组合、增量或工程优化”的工作，尽可能变成清楚、有边界、可防守的投稿叙事。

## 为什么需要它

这类论文往往不是不能投，而是比较难中。审稿人很容易把它们读成“已有方法 A+B+C 的组合”“只是在旧方法上做小改动”“工程系统堆得完整但科学问题不清楚”。一旦论文没有提前把贡献边界、必要性和机制证据讲清楚，reviewer 就会集中攻击：

- novelty 不够，像是 incremental tweak；
- 方法只是已有组件的直接拼接；
- contribution 写成了“我们加了 A、B、C 三个模块”；
- related work 没有划清和已有工作的关键边界；
- ablation 做了，但没有说明每个模块对应解决什么失败模式；
- baseline fairness、scope、cost、reproducibility 没有提前防守；
- rebuttal 只能写成空泛的 “we clarify” 或 “we will add discussion”。

这个 skill 的目标就是把这些风险提前暴露出来，并把论文已有材料重新组织成更清楚、更可防守的投稿叙事。

## 它能帮你做什么

### 1. 直接分析目标论文

适合你已经有一篇论文 PDF，想知道它应该怎么讲得更强。

输出重点包括：

- 当前论文最容易被攻击成哪种增量风险；
- 真正可防守的贡献层级是什么；
- 哪些亮点已经在论文里存在，但作者没有讲透；
- abstract、introduction、contribution bullets、related work、method overview 应该怎么改；
- reviewer 可能如何攻击 novelty、A+B/C、baseline、mechanism、experiment、reproducibility；
- 不增加实验时怎么修改，必须增加实验时优先补什么；
- rebuttal 里哪些话可以说，哪些危险话术要避免。

### 2. 自动生成领域专用 helper skill

适合你后续还要写同方向论文，或者希望为一个研究方向沉淀可复用经验。

它可以根据目标论文自动推断领域/子领域，再从参考论文、reviews、author replies 和 meta-reviews 中提取匿名案例，生成一个领域专用 skill。这个生成出的 skill 可以继续辅助同类论文：

- 复用该领域常见的强包装方式；
- 复用 reviewer 常见攻击模式；
- 复用有效 rebuttal 模式；
- 复用匿名案例中的 story route 和防守逻辑。

## 架构图介绍

上方中文架构图是 `paper-contribution-helper` 这个 skill / skill factory 的整体架构图，不是 SemiDFL 领域专用 helper skill 的架构图。

图里的核心逻辑是：左边输入目标论文和已有材料，中间的 `paper-contribution-helper` 负责诊断贡献风险、挖掘已有亮点、预演审稿攻击、给出分层修改方案，并把经验沉淀成领域专用 helper skill；右边的生成 skill 则把该领域的匿名案例、常见审稿问题、rebuttal 模式和 story routes 固化下来，方便后续同类论文复用。

模块贡献很直接：贡献诊断告诉你论文会被怎样质疑，亮点挖掘帮你找回已经存在但没讲透的价值，审稿预演提前暴露 novelty、A+B/C、baseline 和 mechanism 风险，分层修改给出从“完全不补实验”到“新增证据”的不同方案，领域生成则把这次经验变成可复用的方向级助手。

内部资源的作用也保持简单：`SKILL.md` 管入口、规则和输出格式；`references/` 放贡献包装方法、匿名案例、审稿攻击和 rebuttal 模式；`scripts/` 用于整理材料、抽取案例和打包校验；`assets/` 提供生成领域 skill 的模板与结构。打包资源中，`paper-contribution-helper-v1.0.2.zip` 是 `paper-contribution-helper skill` 的 v1.0.2 打包文件。

## SemiDFL 样例测试结果

`example_semiDFL/` 是一个端到端样例，重点展示两件事：先如何用主包生成 SemiDFL 领域专用 helper skill，再如何在 Codex 和 ChatGPT 网页版中使用这个生成出的 helper skill 分析论文。

**完整优化报告看这里：[`example_semiDFL/semidfl-reframing-report.md`](example_semiDFL/semidfl-reframing-report.md)。**

本次样例中，领域语料刻意选用 2023、2024 年的论文，是因为 SemiDFL 本身是 2025 年论文。为了模拟真实投稿前只能参考既有公开工作的设定，避免把目标论文之后或同期的材料反向泄漏进领域 helper skill，所以样例只使用目标论文发表前的领域文章。领域文章数量有限不是因为该方向文献很少，而是因为本次演示 token 额度不够；实际使用时可以根据预算扩大年份范围、会议来源和每年论文数量。

样例流程按顺序是：

1. 以 `semidfl.pdf` 作为目标论文输入；
2. 使用 `paper-contribution-helper skill` 分析 SemiDFL 的 contribution、novelty 风险和审稿防守点；

   注意：如果 Codex 过程中断，并显示类似“还没有生成最终 skill zip。原因是当前环境没有 OPENAI_API_KEY、acpx 或本地 LLM 后端”的信息，请回复：

   ```text
   不对啊。我这里说了使用 Codex 来编排进行深度阅读。
   ```

3. 生成 SemiDFL 领域专用 helper skill：`semidfl-contribution-helper.zip`；
4. 在 Codex 中使用生成出的 `semidfl-contribution-helper.zip` 继续分析 SemiDFL；
5. 在 ChatGPT 网页版中分别测试主包直接分析和使用已生成 helper skill 分析两种方式。

样例产物包括：

- `semidfl.pdf`：样例中用来分析的目标论文；
- `semidfl-reframing-report.md`：最终生成的论文优化报告；
- `semidfl-contribution-helper.zip`：根据 SemiDFL 生成的领域专用 helper skill；
- `codex-child-skill-generation-and-analysis.mp4`：在 Codex 中生成并使用领域专用 helper skill 的完整记录；
- `chatgpt-web-main-skill-direct-analysis.mhtml`：在 ChatGPT 网页版中使用 `paper-contribution-helper skill` 内置知识库直接分析论文的过程；
- `chatgpt-web-semidfl-helper-analysis.mhtml`：在 ChatGPT 网页版中使用 `semidfl-contribution-helper.zip` 分析论文的过程；
- `example-file-manifest.txt`：样例目录文件说明。

报告中对 SemiDFL 的关键改写来自 `semidfl-reframing-report.md`：

```text
SemiDFL identifies the missing consensus interfaces that make SSL hard in DFL, and builds a three-level consensus mechanism: label consensus for noisy pseudo supervision, data-space consensus for non-shareable heterogeneous data, and model-space consensus for aggregation without shared validation data.
```

简单说就是：

```text
这篇论文真正强的地方，是把 semi-supervised DFL 里的三个缺口拆清楚：没有可靠伪标签、没有可共享数据空间、没有共享验证集来决定谁的模型更可信。然后分别用 NPL、consensus diffusion MixUp、AdaGen 把这三个缺口接上。
```

## 如何使用

### 在 Codex 中使用主包

把这个 skill 的 zip 文件 `paper-contribution-helper-v1.0.2.zip` 放到 Codex 项目中，然后告诉 Codex 你要做哪一类任务：

```text
我选择 A：直接分析 target-paper.pdf，帮我做贡献包装、审稿攻击预演和修改建议。
```

或者：

```text
我选择 B：请根据 target-paper.pdf 自动推断领域，并生成一个该方向可复用的领域专用 helper skill。参考年份 2023、2024，每年最多 10 篇；来源 iclr-openreview。
```

### 在 ChatGPT 网页版中使用

主包的完整工厂能力需要在 Codex 中运行，尤其是自动生成领域专用 helper skill。ChatGPT 网页版不能生成领域专用 helper skill；它只适合两种方式：直接用主包内置知识库分析论文，或使用已经在 Codex 中生成好的领域专用 helper skill。建议使用 Thinking Standard 模式。

方式一：直接用主包内置知识库分析论文，不生成领域专用 skill。

1. 建立一个 ChatGPT 项目；
2. 把这个 skill 的 zip 文件 `paper-contribution-helper-v1.0.2.zip` 放进 Sources；
3. 第一轮输入：

```text
启动 paper-contribution-helper skill
```

4. 第二轮上传 PDF 后输入：

```text
方案A，直接分析semiDFL
```

方式二：使用已经生成好的领域专用 skill。

1. 建立一个 ChatGPT 项目；
2. 把 `semidfl-contribution-helper.zip` 放进 Sources；
3. 第一轮输入：

```text
启动semidfl-contribution-helper.zip 里面的skill
```

4. 第二轮上传 PDF 后输入：

```text
使用这个skill分析这篇文章
```

## English README

`paper-contribution-helper skill` is a Codex skill factory for **A+B+C-style component-combination papers**, incremental papers, engineering-optimization papers, light method-transfer papers, and old-method-new-setting adaptation papers. Many graduate students and early-career researchers have real methods and experiments, but their papers are written as “we combine A, B, and C,” which makes reviewers attack novelty, incrementalism, mechanism evidence, baseline fairness, or scope. This skill is built for that pain point: it helps turn existing methods, experiments, and constraints into a clearer, stronger, evidence-grounded contribution narrative. Thanks to Xinyang Liu from the University of Bristol for providing the SemiDFL materials.

![paper-contribution-helper skill architecture, English](paper-contribution-helper-skill-architecture-en.png)

There are two core ways to use it. First, you can directly use the main package’s built-in contribution-framing knowledge base to analyze a target paper and quickly obtain contribution framing, novelty defense, reviewer attack preplay, and revision plans. Second, **in Codex**, you can use the target paper as a seed, collect related papers, reviews, author replies, and meta-reviews, then generate a reusable domain-specific helper skill for future papers in the same area. **ChatGPT web cannot generate a domain-specific helper skill**; it can only directly use the main package’s built-in knowledge base, or use a child skill already generated in Codex.

Note: If the Codex run stops with a message like “The final skill zip has not been generated. The reason is that the current environment does not have OPENAI_API_KEY, acpx, or a local LLM backend,” reply:

```text
No, that is not right. I said to use Codex to orchestrate the deep-reading process.
```

In the SemiDFL example, the key rewrite is not to keep emphasizing “we combine several modules,” but to move the paper from a **component-combination paper** to an **interface-closure paper**.

| Easy to Read As | Stronger Contribution Narrative |
| --- | --- |
| Combining NPL, diffusion MixUp, and AdaGen | Semi-supervised DFL lacks three consensus interfaces; SemiDFL closes the label-space, data-space, and model-space interfaces |
| Experiments only show higher accuracy | Experiments are organized around reviewer-facing failure modes: label scarcity, non-IID robustness, pseudo-supervision quality, data-space consensus, and model-space consensus |

The point is not to invent new experiments or overclaim. The point is to align the real problem solved by the paper, the evidence already present in the paper, and the defenses reviewers will expect.

The core principle is **strong but honest**: do not fabricate, exaggerate, or claim beyond the paper. Instead, recover the real value already present in the work and turn a paper that looks like a combination, incremental improvement, or engineering optimization into a clearer, bounded, and more defensible submission narrative.

### Why This Is Needed

These papers are not necessarily unpublishable, but they are difficult to get accepted. Reviewers can easily read them as “a combination of existing methods A+B+C,” “a small tweak on an old method,” or “a complete engineering system without a clear scientific question.” Once the paper fails to explain contribution boundaries, necessity, and mechanism evidence, reviewers often attack:

- weak novelty or incremental tweak risk;
- direct composition of existing components;
- contribution bullets that only say “we add A, B, and C”;
- unclear boundaries with related work;
- ablations that do not explain which failure mode each module solves;
- missing defenses for baseline fairness, scope, cost, or reproducibility;
- rebuttals that collapse into vague “we clarify” or “we will add discussion” responses.

The skill exposes these risks early and reorganizes the paper’s existing material into a clearer, more defensible submission story.

### What It Can Do

#### 1. Directly Analyze a Target Paper

Use this when you already have a paper PDF and want to know how to frame it more strongly.

Main outputs include:

- which incremental-risk category the paper is most likely to be attacked as;
- what the defensible contribution level actually is;
- which real strengths already exist in the paper but are under-explained;
- how to revise the abstract, introduction, contribution bullets, related work, and method overview;
- how reviewers may attack novelty, A+B/C composition, baselines, mechanisms, experiments, and reproducibility;
- what can be improved without new experiments, and what should be prioritized if new evidence is needed;
- what can safely be said in rebuttal, and which risky rhetorical patterns to avoid.

#### 2. Generate a Reusable Domain-Specific Helper Skill

Use this when you expect to write more papers in the same area, or want to preserve reusable review and framing knowledge for a research direction.

In Codex, the main package can infer the domain/subdomain from a target paper, collect related papers, reviews, author replies, and meta-reviews, anonymize reusable patterns, and generate a domain-specific helper skill. The generated child skill can then help future papers reuse:

- strong framing routes common in the area;
- recurring reviewer attack patterns;
- effective rebuttal patterns;
- anonymized case-derived story routes and defense logic.

### Architecture

The English architecture figure above describes the overall `paper-contribution-helper` skill / skill factory, not the SemiDFL-specific child skill.

The left side provides the target paper and supporting materials. The middle `paper-contribution-helper` diagnoses contribution risks, recovers under-explained strengths, preplays reviewer attacks, proposes layered revision plans, and distills the experience into a domain-specific helper skill. The right side shows the generated child skill, which stores anonymized cases, recurring reviewer concerns, rebuttal patterns, and story routes for future reuse.

The modules are direct: contribution diagnosis tells you how the paper will be questioned; strength mining recovers real value already present in the paper; reviewer preplay surfaces novelty, A+B/C, baseline, and mechanism risks; layered revision separates no-new-experiment wording fixes from evidence-reorganization and true additional-evidence needs; domain generation turns one paper’s experience into a reusable area-level assistant.

The internal resources stay simple: `SKILL.md` controls entry points, rules, and output formats; `references/` stores contribution-framing methods, anonymized cases, reviewer attacks, and rebuttal patterns; `scripts/` supports material organization, case extraction, packaging, and validation; `assets/` provides templates and structures for generated domain skills. In the packaged resources, `paper-contribution-helper-v1.0.2.zip` is the v1.0.2 zip package for `paper-contribution-helper skill`.

### SemiDFL Example Results

`example_semiDFL/` is an end-to-end example. It shows two things in order: how to generate a SemiDFL-specific helper skill from the main package, and how to use that generated helper skill in Codex and ChatGPT web.

**Full optimization report: [`example_semiDFL/semidfl-reframing-report.md`](example_semiDFL/semidfl-reframing-report.md).**

In this example, the domain corpus intentionally uses papers from 2023 and 2024 because SemiDFL is a 2025 paper. To simulate a realistic pre-submission setting where only earlier public work is available, and to avoid leaking later or contemporaneous material back into the domain helper skill, the example only uses papers published before the target paper. The domain corpus is small not because the area lacks papers, but because this public demo did not have enough token budget; in actual use, the year range, venues, and number of papers per year can be expanded according to the available budget.

The example workflow is:

1. Use `semidfl.pdf` as the target paper.
2. Use `paper-contribution-helper skill` to analyze SemiDFL’s contribution, novelty risks, and reviewer defenses.

   Note: If the Codex run stops with a message like “The final skill zip has not been generated. The reason is that the current environment does not have OPENAI_API_KEY, acpx, or a local LLM backend,” reply:

   ```text
   No, that is not right. I said to use Codex to orchestrate the deep-reading process.
   ```

3. Generate the SemiDFL-specific helper skill: `semidfl-contribution-helper.zip`.
4. In Codex, use the generated `semidfl-contribution-helper.zip` to continue analyzing SemiDFL.
5. In ChatGPT web, test two supported modes: direct analysis with the main package, and analysis with the already generated helper skill.

Example artifacts:

- `semidfl.pdf`: target paper used in the example;
- `semidfl-reframing-report.md`: final paper optimization report;
- `semidfl-contribution-helper.zip`: SemiDFL-specific generated helper skill;
- `codex-child-skill-generation-and-analysis.mp4`: full Codex recording for generating and using the child skill;
- `chatgpt-web-main-skill-direct-analysis.mhtml`: ChatGPT web process using the main package’s built-in knowledge base;
- `chatgpt-web-semidfl-helper-analysis.mhtml`: ChatGPT web process using `semidfl-contribution-helper.zip`;
- `example-file-manifest.txt`: file manifest for the example folder.

Key SemiDFL rewrite from `semidfl-reframing-report.md`:

```text
SemiDFL identifies the missing consensus interfaces that make SSL hard in DFL, and builds a three-level consensus mechanism: label consensus for noisy pseudo supervision, data-space consensus for non-shareable heterogeneous data, and model-space consensus for aggregation without shared validation data.
```

Simply put:

```text
The real strength of the paper is that it identifies three missing interfaces in semi-supervised DFL: no reliable pseudo-labels, no shareable data space, and no shared validation set for deciding which models are trustworthy. NPL, consensus diffusion MixUp, and AdaGen are then framed as closing these three interfaces.
```

### How To Use

#### In Codex

Put the skill zip file `paper-contribution-helper-v1.0.2.zip` in your Codex project, then choose one task:

```text
Option A: Directly analyze target-paper.pdf and help me with contribution framing, reviewer attack preplay, and revision suggestions.
```

Or:

```text
Option B: Infer the domain from target-paper.pdf and generate a reusable domain-specific helper skill. Use reference years 2023 and 2024, up to 10 papers per year, from iclr-openreview.
```

#### In ChatGPT Web

The full factory workflow must run in Codex, especially domain-specific helper-skill generation. ChatGPT web cannot generate a domain-specific helper skill. It supports only two modes: directly analyzing a paper with the main package’s built-in knowledge base, or using a domain-specific helper skill already generated in Codex. Thinking Standard mode is recommended.

Mode 1: Directly analyze a paper with the main package’s built-in knowledge base.

1. Create a ChatGPT project.
2. Add the skill zip file `paper-contribution-helper-v1.0.2.zip` to Sources.
3. First prompt:

```text
启动 paper-contribution-helper skill
```

4. After uploading the PDF, prompt:

```text
方案A，直接分析semiDFL
```

Mode 2: Use an already generated domain-specific helper skill.

1. Create a ChatGPT project.
2. Add `semidfl-contribution-helper.zip` to Sources.
3. First prompt:

```text
启动semidfl-contribution-helper.zip 里面的skill
```

4. After uploading the PDF, prompt:

```text
使用这个skill分析这篇文章
```
