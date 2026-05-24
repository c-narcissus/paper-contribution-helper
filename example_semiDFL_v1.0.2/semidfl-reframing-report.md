# SemiDFL 贡献包装与审稿防御报告

目标论文：`SemiDFL: A Semi-Supervised Paradigm for Decentralized Federated Learning`

生成路径：`semidfl-contribution-helper` 目标论文分析流程。`semiDFL.pdf` 的 PDF 抽取状态为 `ok`，抽取文本约 55,245 字符，未提供真实审稿意见，因此所有审稿质疑均标为 `simulated-review`。

## 0. 语言、证据与可读性约定

本报告用中文做诊断、排序、风险分析和修改策略；英文只用于可直接放入论文或 rebuttal 的片段。

证据边界：

- `target-paper-derived`：来自 `semiDFL.pdf` 的题名、摘要、正文、图表、实验与附录，是本文贡献判断的证据。
- `base-corpus analogy`：来自生成 skill 中的 2023/2024 ICLR OpenReview 匿名 casebook，只能作为包装类比，不能证明 SemiDFL 的事实。
- `simulated-review`：未提供真实 review，因此审稿攻击是预演，不冒充真实 reviewer 反馈。

可读性规则：每个抽象 story route 都先说“普通话版本”，再给技术 thesis、例子/类比、证据锚点和边界。本文的核心不是把三个模块列出来，而是解释为什么这三个模块在“无中心服务器 + 标签稀缺 + 非 IID + 客户端数据源不一致”这个场景里必须一起出现。

## 1. Deep Evidence Base

### 1.1 目标场景

普通话版本：这篇论文不是普通 SSL，也不是普通 FL。它处理的是一个更难的组合场景：没有中心服务器，每个 client 只能和邻居通信；有的 client 只有少量标签，有的只有无标签数据，有的两者都有；数据还高度 non-IID。这个场景下，简单把 CFL 里的 semi-supervised 方法搬过来会缺一个“全局协调器”和“共享监督信号”。

技术 thesis：SemiDFL targets semi-supervised decentralized federated learning where clients have heterogeneous data sources and non-IID distributions, and where central-server coordination or shared validation data is unavailable.

目标 PDF 证据：

- 第 1 页摘要：DFL 无中心服务器，缓解通信瓶颈和单点故障；现有 DFL 多假设 supervised learning，每个 client 有足够 labeled data。
- 第 1 页 introduction 明确提出 key question：`How can DFL be effective when clients have labeled and unlabeled data sources in highly non-iid scenarios?`
- 第 2 页 objective：定义三类 client：L-client、U-client、M-client，并给出 semi-supervised DFL 的目标函数。

边界：目前证据支持“首次系统研究/范式化 semi-supervised DFL 场景”，但不要写成“解决所有 DFL/SSL 场景”。

### 1.2 被打破的旧假设

| 旧假设 | 在 SemiDFL 场景里为什么失效 | 本文替代机制 | 证据锚点 |
|---|---|---|---|
| 每个 client 有足够 labeled data | 现实中大部分数据未标注，且 client 数据源不同 | 三类 client 建模：L/U/M clients | 第 1-2 页 |
| CFL 里有中心服务器传播监督信息 | DFL 没有中心协调，不能依赖 server 汇总或共享验证集 | 邻域伪标签、consensus diffusion、邻域自适应聚合 | 第 1、3-4 页 |
| 单个 client 的本地模型能给可靠 pseudo-label | 非 IID 使本地预测偏置更严重，动态 noisy supervision 会放大 | Neighborhood Pseudo-Labeling, neighborhood adaptive threshold | 第 3、7 页 Table 2 |
| 只靠 labeled/pseudo-labeled data 足够训练 | 标签少且 non-IID，local MixUp 仍受限于本地数据岛 | Consensus MixUp with consensus-based diffusion generated data | 第 4、7 页 Table 3 |
| 可以用共享 test/validation set 评估邻居模型 | DFL/privacy setting 下共享 test set 不现实 | 用生成数据上的 classifier accuracy 做 AdaGen 权重 | 第 4、7 页 Table 4 |

### 1.3 方法模块与证据锚点

| 模块 | 在论文中的角色 | 直接证据 | 目前包装问题 |
|---|---|---|---|
| Neighborhood Pseudo-Labeling (NPL) | 用邻居 classifier 和邻域 class-wise threshold 降低 non-IID 下 pseudo-label 噪声 | 第 3 页公式 (5)-(9)，第 7 页 Table 2 | 摘要里说“utilize neighborhood information”，但没有足够强调它是在替代缺失中心监督 |
| Consensus MixUp / diffusion-generated data | 通过 consensus diffusion 生成相似分布的数据，弥补本地数据岛并支持 MixUp | 第 3-4 页公式 (10)-(11)，第 7 页 Table 3 | 容易被读成“把 diffusion + MixUp 加进 FL”，需要改成“构造可共享但不共享原始数据的 consensus data space” |
| Adaptive Aggregation / AdaGen | 不使用共享测试集，改用生成数据评估 classifier performance 来确定 aggregation weights | 第 4 页公式 (12)，第 7 页 Table 4 | 当前写法像一个工程优化模块，需要强调它关闭了“无共享验证集时如何自适应聚合”的接口缺口 |
| Figure 1 | 把 topology、六步流程、三处主要贡献可视化 | 第 3 页 Figure 1 caption 指出 steps 1, 3, 6 是主要贡献 | caption 可以更主动解释三步分别修复监督、数据、模型三类 consensus 缺口 |

### 1.4 实验证据

| 证据 | 支持什么 | 风险 |
|---|---|---|
| Table 1：MNIST/Fashion-MNIST/CIFAR-10，IID/non-IID，多 labeled ratios，SemiDFL 除 DFL-UB 外超过 baseline | 支持端到端性能和稳定性 | 需要解释 DFL-UB 是 fully-labeled upper bound，不应被视为直接 SSL baseline |
| Figure 2：不同 non-IID degree 下鲁棒性 | 支持“non-IID 越强时仍相对稳” | 需避免写成对所有 topology/real-world shift 均鲁棒 |
| Figure 3：不同 labeled ratio 下鲁棒性 | 支持 label scarcity 下收益 | 需说明 label ratio 范围是实验设定内 |
| Table 2：NPL vs Vanilla PL/APL | 支持 NPL 不是单纯 threshold trick，而是邻域监督修复 | 需要在正文把 Table 2 映射到 mechanism claim |
| Table 3：C-MixUp with diffusion vs L-MixUp/GAN | 支持 consensus data space 和 diffusion choice | 需要避免“diffusion 一定优于 GAN”的泛化 |
| Table 4：AdaGen vs Constant/AdaTest | 支持无共享测试集下的 practical model-space consensus | 某些 setting 中 AdaGen 不严格超过 AdaTest 或 constant，需要边界化 |
| 附录第 10-12 页：topology robustness、PyTorch 2.0、2 RTX 4090、500 rounds、DDPM generation details | 支持复现和拓扑鲁棒性 | 计算/通信成本未作为主结果充分组织 |

## 2. Strong Packaging Diagnosis

### 2.1 当前弱表层贡献

当前摘要和贡献 bullets 容易被读成：

> We combine neighborhood pseudo-labeling, diffusion-based MixUp, and adaptive aggregation for semi-supervised DFL.

这个表层版本的问题是：三个模块都能被 reviewer 找到相邻先例。pseudo-labeling、MixUp、diffusion generation、adaptive aggregation 都不是完全陌生的 primitive。如果只说“我们设计了 A、B、C”，顶会 reviewer 很容易攻击为 A+B+C 组合，甚至问“为什么不是把 CBAFed/FlexMatch/MixMatch 简单 decentralized 化？”

### 2.2 更强实际贡献

更强的贡献不是“三个模块”，而是：

> SemiDFL identifies the missing consensus interfaces that make SSL hard in DFL, and builds a three-level consensus mechanism: label consensus for noisy pseudo supervision, data-space consensus for non-shareable heterogeneous data, and model-space consensus for aggregation without shared validation data.

普通话版本：这篇论文真正强的地方，是把 semi-supervised DFL 里的三个缺口拆清楚：没有可靠伪标签、没有可共享数据空间、没有共享验证集来决定谁的模型更可信。然后分别用 NPL、consensus diffusion MixUp、AdaGen 把这三个缺口接上。

### 2.3 为什么当前写法会招致攻击

| 风险 | 触发写法 | 改写方向 |
|---|---|---|
| Novelty/incrementality | `first semi-supervised DFL method` 后面直接列模块 | 先定义“missing consensus interfaces”，再说 first 是 first formulation + interface closure |
| A+B/C combination | `neighborhood information + diffusion model + adaptive aggregation` | 把每个模块映射到一个不可替代的场景压力：pseudo-label noise / data island / no shared validation |
| Mechanism evidence | Table 2/3/4 分散在实验段 | 在 method/experiment 开头加入 evidence map：哪个表验证哪个 consensus interface |
| Baseline fairness | CFL SSL baselines 被 adapted to DFL，但资源条件不够显式 | 增加 comparison contract：same decentralized topology, same label budget, no central server/shared raw data |
| Cost/scalability | diffusion generation 和 500 rounds 带来计算成本 | 主动写 quality-cost boundary：1000 generated samples per 10 rounds、100 validation samples、2 RTX 4090；不要声称 negligible overhead |
| Scope/generalization | “remarkable superiority” 太满 | 改成 evaluated datasets/topologies/label ratios/non-IID degrees 内的 superiority |

## 2.5 Latent Contribution Mining

| 候选贡献 | 证据标签 | 普通话解释 | 证据锚点 | 安全用法 | 不安全说法 |
|---|---|---|---|---|---|
| Semi-supervised DFL problem formulation | `paper-explicit` | 把 L/U/M clients 和 non-IID DFL 合成一个明确目标函数 | 第 2 页 objective, Eq. (4) | 作为 setting contribution 放在第一贡献 | “solves all semi-supervised FL” |
| Missing-consensus-interface decomposition | `latent-but-supported` | 把问题拆成 label/data/model 三个 consensus 缺口 | 第 1-4 页三模块逻辑 | 作为主 story thesis | “theoretical decomposition” |
| NPL as decentralized supervision repair | `paper-explicit` | 用邻域模型和邻域阈值改善伪标签 | Eq. (5)-(9), Table 2 | 作为 mechanism route | “unbiased pseudo-labeling guaranteed” |
| Consensus diffusion as data-space bridge | `paper-explicit` | 不共享 raw data，但生成相似分布数据来 MixUp | Eq. (10)-(11), Table 3 | 作为 data-space consensus | “privacy-preserving generation is proven” |
| AdaGen as shared-validation replacement | `latent-but-supported` | 用生成数据替代不可用的共享测试集决定聚合权重 | Eq. (12), Table 4 | 作为 practical DFL interface closure | “always better than test-set aggregation” |
| Evidence system across scarcity/heterogeneity/topology | `story-level reframing` | 不是堆结果，而是逐个回答 reviewer concern | Table 1-4, Figure 2-3, appendix topology | 组织实验章节和 rebuttal | “comprehensive real-world deployment validation” |
| Extension to stronger privacy/accounting | `future-boundary hook` | 生成数据和通信成本可进一步分析 | 附录实现与 checklist | 放 limitation/future work | 当前声称 privacy guarantee 或 negligible cost |

## 2.6 Top-Conference Story Reconstruction

### 2.6.1 Problem Equation

普通话版本：中心化 FL 的 SSL 方法依赖中心服务器；传统 DFL 依赖本地有标签监督。SemiDFL 处在两者都不满足的交集，所以需要同时重建 supervision、data 和 aggregation 三个“共识接口”。

```text
Semi-supervised DFL difficulty
= no central coordinator
+ heterogeneous client data sources
+ non-IID local distributions
+ noisy pseudo-labels
+ no shared validation data for adaptive aggregation

SemiDFL contribution
= label-space consensus (NPL)
+ data-space consensus (diffusion MixUp)
+ model-space consensus (AdaGen)
under the same decentralized/resource-constrained evaluation contract.
```

### 2.6.2 Contribution Ladder

| Level | 普通话意义 | Paper-ready claim | 证据锚点 | 过度声称风险 |
|---|---|---|---|---|
| L1 Setting | 明确一个被忽视但现实的难场景 | We formulate semi-supervised DFL with labeled, unlabeled, and mixed clients under non-IID distributions. | 第 1-2 页 | 不要说所有 FL |
| L2 Failure diagnosis | 说明为什么旧方法不直接适用 | Existing SSL/DFL components lack the consensus interfaces needed for decentralized pseudo supervision, data-space alignment, and adaptive aggregation. | 第 1 页 challenges, 第 3-4 页 modules | 不要说旧方法完全无效 |
| L3 Mechanism | 三个模块各修一个缺口 | SemiDFL constructs label-, data-, and model-space consensus through NPL, consensus diffusion MixUp, and generated-data-based adaptive aggregation. | Eq. (5)-(12), Figure 1 | 不要把 primitive 写成全新 |
| L4 Evidence | 用结果和消融证明必要性 | Table 1-4 and Figure 2-3 support end-to-end gains and component-level effects under label scarcity and non-IID settings. | 第 6-7 页 | 不要把消融说成理论证明 |
| L5 Boundary | 主动限制 claim | The evidence supports evaluated datasets, topologies, label ratios, and non-IID degrees; broader deployment and cost/privacy accounting remain future work. | 附录第 10-12 页 | 不要写 universal robustness |

### 2.6.3 Abstract Rewrite

```text
Decentralized federated learning (DFL) removes the central server, but this also removes the coordination mechanisms that centralized semi-supervised FL often relies on. We study a practical semi-supervised DFL regime in which clients may hold only a few labeled samples, only unlabeled samples, or both, under heterogeneous non-IID distributions. In this regime, the main challenge is not only to exploit unlabeled data, but also to rebuild the missing consensus interfaces for pseudo supervision, data augmentation, and model aggregation without raw-data sharing or a shared validation set.

We propose SemiDFL, a semi-supervised DFL framework that constructs consensus in label, data, and model spaces. First, neighborhood pseudo-labeling uses neighboring classifiers and adaptive class-wise thresholds to reduce noisy pseudo supervision under non-IID data. Second, a consensus-based diffusion model generates aligned synthetic data for MixUp, forming a data space that can be used across clients without sharing raw data. Third, generated data are used to estimate classifier reliability and adapt aggregation weights, replacing the impractical assumption of a shared validation set. Experiments on MNIST, Fashion-MNIST, and CIFAR-10 across label ratios, non-IID degrees, and communication topologies show that SemiDFL consistently improves over decentralized adaptations of SSL baselines, with ablations supporting the role of each consensus interface.
```

### 2.6.4 Introduction Framing

```text
The difficulty of semi-supervised DFL is an interface problem. Centralized semi-supervised FL can rely on a server to coordinate information, while supervised DFL can rely on local labeled data to drive each client update. Semi-supervised DFL has neither convenience: pseudo-labels are biased by non-IID local views, unlabeled-only clients cannot easily enrich their local data space, and adaptive aggregation cannot assume a shared validation set. This creates three missing consensus interfaces: how to form reliable pseudo supervision, how to construct a usable data space without raw-data sharing, and how to decide which neighbor models should have larger influence.
```

### 2.6.5 Contribution Bullets Rewrite

```text
- We formulate a semi-supervised DFL setting with labeled, unlabeled, and mixed clients under non-IID distributions, and identify three missing consensus interfaces that make centralized SSL or supervised DFL methods insufficient in this regime.
- We introduce neighborhood pseudo-labeling, which combines neighboring classifiers with adaptive class-wise thresholds to improve pseudo supervision when each client has a biased local view.
- We build a consensus data space through diffusion-based data generation and MixUp, enabling clients to augment local training without sharing raw data.
- We propose generated-data-based adaptive aggregation, which estimates classifier reliability on aligned synthetic data and avoids the impractical assumption of an extra shared validation set.
- We evaluate SemiDFL across datasets, label ratios, non-IID degrees, and communication topologies, and use ablations to map each component to the failure mode it addresses.
```

### 2.6.6 Related-Work Boundary

```text
Unlike centralized semi-supervised FL methods that can rely on a server to coordinate supervision, SemiDFL must construct supervision and aggregation signals through local neighborhoods. Unlike supervised DFL methods, it cannot assume that every client has sufficient labeled data. SemiDFL is therefore best understood as addressing the intersection where decentralized optimization, label scarcity, and non-IID data source heterogeneity simultaneously remove the usual coordination mechanisms.
```

### 2.6.7 Method Overview Rewrite

```text
SemiDFL is organized around three consensus interfaces. The label-space interface uses neighborhood pseudo-labeling to reduce client-local pseudo-label bias. The data-space interface trains consensus diffusion models to generate aligned synthetic samples, which are mixed with labeled and pseudo-labeled data for classifier training. The model-space interface uses generated samples as a common evaluation substrate for adaptive aggregation, so that clients can weight neighbor models without accessing a shared validation set. These three interfaces correspond to Steps 1, 3, and 6 in Figure 1 and are evaluated separately in Tables 2-4.
```

### 2.6.8 Figure/Captions Direction

Figure 1 caption 应从“六步流程”改成“故障修复图”。建议 caption：

```text
Figure 1: SemiDFL closes three missing consensus interfaces in semi-supervised DFL. Step 1 builds label-space consensus through neighborhood pseudo-labeling; Step 3 builds data-space consensus through diffusion-based synthetic data for MixUp; Step 6 builds model-space consensus through generated-data-based adaptive aggregation. Steps 2, 4, and 5 provide the standard training/evaluation flow connecting these interfaces.
```

## 3. Story Route Candidate Board

| Rank | Story route | Novelty defense | Evidence fit | A+B/C resistance | Baseline control | Mechanism control | Cost/repro control | Rewrite cost | New-experiment pressure | Best use |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Missing consensus interfaces | Very strong | Very strong | Strong | Medium | Strong | Medium | Medium | Low | Main thesis, abstract, intro, Fig. 1 |
| 2 | First semi-supervised DFL problem formulation | Strong | Strong | Medium | Strong | Medium | High | Low | Low | Contributions, related work |
| 3 | Three-space consensus mechanism | Strong | Strong | Strong | Medium | Strong | Medium | Medium | Low | Method overview |
| 4 | Evidence system under label scarcity/non-IID | Medium | Very strong | Medium | Strong | Medium | Medium | Medium | Low | Experiments and rebuttal |
| 5 | Resource-aware no-shared-validation aggregation | Medium | Medium | Medium | Medium | Medium | Strong if cost bounded | Medium | Medium | Method + limitations |
| 6 | Broad privacy/deployment story | Unsupported as main route | Weak-to-medium | Weak | Medium | Weak | Weak | High | High | Limitation/future work only |

## 4. Main Route Expansions

### Route 1: Missing Consensus Interfaces

普通话版本：不要说“我们加了三个模块”，要说“这个场景缺三个接口，我们补上了三个接口”。

技术 thesis：Semi-supervised DFL fails because it lacks consensus interfaces for pseudo supervision, data alignment, and model reliability; SemiDFL closes these interfaces without a central server.

证据：第 1 页 key question，第 3-4 页 NPL/C-MixUp/AdaGen，第 7 页 Table 2-4。

匿名类比：`combination-method-needs-mechanism-claim`，借的是“承认 primitive 可见，但强调 constraint-driven coupling”。

风险边界：不要说这是一个理论完备的 consensus framework；它是 evidence-supported framework。

可直接使用片段：

```text
The novelty of SemiDFL lies in identifying and closing the missing consensus interfaces of semi-supervised DFL: reliable pseudo supervision, aligned data augmentation, and adaptive model aggregation without a central server.
```

### Route 2: First Semi-Supervised DFL Formulation

普通话版本：先让 reviewer 接受“这个问题本身值得做”，再讨论模块。

技术 thesis：The paper contributes a practical SSL objective for DFL with L/U/M clients and non-IID distributions.

证据：第 2 页 L-client/U-client/M-client 定义和 objective Eq. (4)。

风险边界：如果只靠“first”防守会很危险；必须搭配 Route 1 和消融。

可直接使用片段：

```text
We focus on the semi-supervised DFL regime where clients differ not only in data distribution but also in supervision availability, including labeled-only, unlabeled-only, and mixed clients.
```

### Route 3: Three-Space Consensus Mechanism

普通话版本：把“data/model spaces”再拆得更清楚：label-space consensus 负责伪标签，data-space consensus 负责生成和 MixUp，model-space consensus 负责聚合。

技术 thesis：SemiDFL builds coordinated supervision and aggregation through label-, data-, and model-space consensus.

证据：摘要已有 data/model spaces；正文可加入 label-space consensus；Figure 1 steps 1/3/6。

风险边界：不要说 label-space consensus 是原文术语，建议作为 framing term 使用。

可直接使用片段：

```text
SemiDFL can be viewed as a three-space consensus design: label-space consensus for pseudo-labeling, data-space consensus for synthetic-data MixUp, and model-space consensus for adaptive aggregation.
```

### Route 4: Evidence System Route

普通话版本：实验不要按“Table 1, Figure 2, Figure 3...”机械堆，要按 reviewer 会问什么来排。

技术 thesis：The evaluation is a defense map: end-to-end performance, non-IID robustness, label-scarcity robustness, component necessity, topology robustness, and reproducibility.

证据：Table 1, Figure 2, Figure 3, Table 2-4, appendix topology, reproducibility checklist。

风险边界：实验覆盖仍是 benchmark-level，不是 deployment proof。

可直接使用片段：

```text
We organize the evaluation around the failure modes of semi-supervised DFL: limited labels, non-IID distributions, missing component interfaces, and topology sensitivity.
```

### Route 5: Resource-Aware Aggregation

普通话版本：AdaGen 不只是“更好的权重”，它是在没有共享验证集时给 adaptive aggregation 找了一个替代评估基准。

技术 thesis：Generated-data-based adaptive aggregation approximates a shared evaluation substrate without requiring an extra shared test set.

证据：第 4 页 shared test dataset impractical，Eq. (12)，Table 4。

风险边界：Table 4 中 AdaGen 并非所有 setting 都严格优于 AdaTest/constant，因此写成 practical replacement/comparable alternative，而不是 universal improvement。

可直接使用片段：

```text
Generated samples provide a common evaluation substrate for adaptive aggregation, allowing clients to estimate neighbor reliability without assuming access to an extra shared validation set.
```

### Route 6: Broad Privacy/Deployment Story

普通话版本：这条路线诱人但不能当主线。论文不共享 raw data，但没有做 formal privacy proof，也没有把通信/计算成本做成主贡献。

安全用法：放 limitation/discussion。

可直接使用片段：

```text
SemiDFL avoids raw-data sharing by design, but formal privacy guarantees and detailed deployment-cost accounting are beyond the scope of the current evaluation.
```

## 5. Recommended Route Combination

默认主线：Route 1 `Missing consensus interfaces`。

方法/Figure route：Route 3 `Three-space consensus mechanism`，把 Figure 1 改成故障-接口-模块映射图。

Related-work/baseline route：Route 2 + comparison contract。明确 centralized SSL FL、supervised DFL、adapted SSL baselines 和 SemiDFL 的资源条件差别。

实验组织 route：Route 4。把 Table 1-4、Figure 2-3、appendix topology 改写成 defense map。

Limitation/discussion route：Route 5 + Route 6。承认计算/通信/privacy formalization 的边界。

最小 Tier 0 组合：摘要第一段改 problem equation；贡献 bullets 改成 interface closure；Figure 1 caption 改故障修复图；实验开头加 evidence map。

## 6. Reviewer Attack Preplay

| Attack | Label | Why reviewer will ask | Manuscript trigger | Strong defense posture | No-new-experiment repair |
|---|---|---|---|---|---|
| Novelty: is this just pseudo-labeling + diffusion + aggregation? | `simulated-review` | primitives 都有先例 | 摘要和贡献 bullets 列模块 | 贡献是 missing consensus interfaces, not primitives | 改摘要/贡献/方法 overview，加入 failure-interface mapping |
| A+B/C combination | `simulated-review` | 三模块组合明显 | Figure 1 六步流程像 pipeline | 每个模块对应一个不可省的场景缺口 | 在 Figure 1 caption 和 method 开头加入三缺口表 |
| Baseline fairness | `simulated-review` | CFL SSL baselines adapted to DFL 的资源条件可能不清 | Baseline methods 只说 adapted | 定义 comparison contract：same topology, no server, same label budget | 在 experimental setup 增加 baseline resource table |
| Mechanism evidence | `simulated-review` | Table 2-4 分散，未直接服务 thesis | 实验按表格顺序写 | Table 2/3/4 分别验证 label/data/model consensus | 在 experiments 开头加 evidence map |
| Cost/scalability | `simulated-review` | diffusion generation 和 500 rounds 可能重 | 摘要说 alleviates bottleneck，但未报告成本主线 | 承认成本边界，强调当前目标是 accuracy/robustness under constraints | 在 limitation 加 generated samples schedule 和 hardware |
| Privacy/safety | `simulated-review` | 生成数据用于评估/混合，可能泄露信息 | “without raw data sharing” 可能被读成 privacy guarantee | 只声称 no raw-data sharing, not formal privacy | 加 safe wording |
| Scope/generalization | `simulated-review` | MNIST/Fashion-MNIST/CIFAR-10 + simulated topology | “remarkable superiority” 太满 | 限定 evaluated datasets/topologies/ratios | 替换强词，并引用 appendix topology |
| Reproducibility | `simulated-review` | 复杂 pipeline + diffusion | 代码链接有，但正文成本/seed细节有限 | 附录已有 PyTorch/hardware/rounds/checklist | 在 appendix pointer 和 reproducibility paragraph 中集中说明 |

## 7. Manuscript Trigger Localization

| Manuscript area | Current strength | Weak trigger | Risk created | Concrete repair |
|---|---|---|---|---|
| Abstract | 清楚说明 DFL + SSL + non-IID | 直接说 first method + 三模块 | novelty/A+B/C attack | 改成 missing consensus interfaces |
| Introduction | 有 key question | challenge 与三模块的映射还不够显式 | reviewer 不知道为什么每个模块必要 | 加“three missing interfaces”段落 |
| Contributions | 四条贡献完整 | 模块命名多，机制关系弱 | 像 list of components | 按 setting/failure/interface/evidence 重排 |
| Related Work | 涵盖 DFL/SSL | 与 CBAFed/MixMatch/FlexMatch 的 resource boundary 不够强 | baseline fairness attack | 加 comparison contract |
| Method | 细节充分 | 三模块之间的共同逻辑不够概括 | mechanism attack | method overview 先给 interface map |
| Experiments | 主结果和消融多 | 结果解释按表格顺序 | evidence 不服务 story | 加 defense-map paragraph |
| Limitations | 不明显 | privacy/cost/scope 未主动边界化 | reviewer 扩大攻击面 | 新增 boundary paragraph |

## 8. Tiered Revision Plan

### Tier 0: 不加实验，最高收益

| Action | Location | Evidence reused | Reviewer-defense purpose | Ready English |
|---|---|---|---|---|
| 改写 abstract 第一段为 missing consensus interfaces | Abstract | 第 1 页 key question | 防 novelty/A+B/C | 见 2.6.3 |
| 重写 contribution bullets | End of Introduction | 第 2-4 页 modules, Table 2-4 | 把模块变成机制闭环 | 见 2.6.5 |
| 加 Figure 1 新 caption | Figure 1 | steps 1/3/6 | 把 pipeline 变成故障修复图 | 见 2.6.8 |
| 实验前加 evidence map | Experiments intro | Table 1-4, Figure 2-3 | 防 mechanism/evidence attack | `We organize the evaluation around the failure modes...` |
| 加 claim boundary paragraph | Conclusion/Discussion | Appendix setup/checklist | 防 privacy/cost/scope attack | 见 residual snippets |

### Tier 1: 小改实验组织/附录，不新增大实验

| Action | Location | Evidence reused | Purpose | Ready English |
|---|---|---|---|---|
| Baseline resource contract table | Experimental Setup | Baselines paragraph | 防 baseline fairness | `We distinguish same-resource baselines from diagnostic baselines...` |
| Component-to-attack matrix | Experiments | Table 2-4 | 防 ablation 不充分 | `Tables 2-4 isolate the three consensus interfaces...` |
| Cost schedule paragraph | Appendix/Limitations | 1000 samples per 10 rounds, 100 eval samples, hardware | 防 scalability | `We report the generation and evaluation schedule to clarify the computational boundary...` |
| Topology robustness pointer | Main experiments or appendix pointer | Appendix topology table | 防 topology scope | `Additional topology results show the same qualitative trend under three communication graphs...` |

### Tier 2: 若还有时间可补

| Action | Location | Evidence needed | Purpose |
|---|---|---|---|
| 通信/计算成本曲线 | Appendix | runtime/communication logs | 强化 scalability defense |
| 生成数据 privacy leakage sanity check | Appendix | membership/visual examples or privacy analysis | 避免 privacy attack |
| 更多真实 DFL topology 或 larger client count | Appendix | additional runs | 强化 deployment scope |
| 统计显著性说明 | Appendix | reported run counts/tests | 强化 result reliability |

## 9. Rebuttal Pattern Library

### Novelty / Incrementality

Defense posture：承认 primitive 有先例，强调 SemiDFL 的新意在 semi-supervised DFL 中缺失接口的联合闭合。

```text
We agree that pseudo-labeling, generative augmentation, and adaptive aggregation are known primitives. The contribution of SemiDFL is not to present each primitive in isolation, but to identify how semi-supervised DFL lacks three coordination interfaces and to instantiate them as label-, data-, and model-space consensus mechanisms.
```

Risky wording to avoid：`all components are novel`。风险：reviewer 很容易举已有 SSL/FL work 反驳。

### A+B/C Combination

```text
The components are coupled by the constraints of the setting: neighborhood pseudo-labeling addresses biased local supervision, consensus generation addresses the lack of a shareable data space, and generated-data-based aggregation addresses the absence of a shared validation set.
```

Risky wording to avoid：`we simply integrate diffusion into DFL`。风险：把 contribution 降成工程组合。

### Baseline Fairness

```text
We clarify the comparison contract by adapting SSL baselines to the same decentralized topology and label budget, while DFL-UB is reported only as a fully labeled diagnostic upper bound rather than a directly comparable semi-supervised baseline.
```

Risky wording to avoid：`DFL-UB is out of scope`。风险：显得回避强 baseline。

### Mechanism Evidence

```text
The ablations are designed to isolate the three consensus interfaces: Table 2 studies pseudo-supervision quality, Table 3 studies the consensus data space, and Table 4 studies model-space aggregation without a shared validation set.
```

Risky wording to avoid：`the ablation proves the mechanism`。风险：实验消融只能 support/indicate，不能证明。

### Cost / Scalability

```text
SemiDFL introduces additional generation cost, and we therefore keep the claim focused on accuracy and robustness under the evaluated resource schedule. In our setup, generated samples are produced periodically and a small generated validation set is used for aggregation.
```

Risky wording to avoid：`negligible overhead`。风险：没有完整成本曲线时不可防守。

### Reproducibility

```text
The appendix reports model architectures, training rounds, generation schedule, hardware, and implementation details, and the code link is provided to support reproduction of the evaluated setting.
```

Risky wording to avoid：`fully reproducible in all environments`。风险：依赖 GPU、diffusion implementation、randomness。

## 10. Anonymous Case Appendix

| Anonymous case | 原始弱点模式 | 可借用包装动作 | SemiDFL 借法 | 边界 |
|---|---|---|---|---|
| `combination-method-needs-mechanism-claim` | known components assembly | 把组件映射到约束场景里的不同压力 | NPL/data consensus/AdaGen 分别对应监督、数据、模型三缺口 | 不说每个 primitive 全新 |
| `incremental-gain-with-ablation-pressure` | 小性能提升或单点替换 | 先命名 failure mode，再用 ablation 支撑必要性 | Table 2-4 分别服务三类 consensus | 不把 ablation 写成理论证明 |
| `baseline-contract-fairness-defense` | baseline 资源边界不清 | 先定义 same-resource vs diagnostic baselines | DFL-UB 是 upper bound，CFL/SSL baselines 是 adapted diagnostic | 不说 baseline 不可比 |
| `evidence-system-coverage-defense` | 实验结果有但没有对应 reviewer concern | 把实验组织成 defense map | Table 1/Fig 2/Fig 3/Table 2-4/appendix topology | 不自动推出 universal generalization |
| `efficiency-system-claim-under-cost-scrutiny` | 系统方法被追问成本 | 主动定义 quality-cost boundary | 承认 diffusion generation cost，报告 schedule | 不说 negligible overhead |
| `scope-generalization-boundary-defense` | claims 太满 | 前置 evaluated regime | 限定 datasets/topologies/label ratios/non-IID degrees | 不说 real-world deployment solved |

## 11. Residual Risks And Safe/Unsafe Boundaries

| Boundary | Safe wording | Unsafe wording | Evidence needed to strengthen |
|---|---|---|---|
| Mechanism | `supports the role of each consensus interface` | `proves each mechanism is necessary in all settings` | 更多跨数据集/拓扑消融 |
| Privacy | `without raw-data sharing` | `privacy-preserving` or `privacy-guaranteed` | formal DP or leakage analysis |
| Cost | `additional generation cost under reported schedule` | `negligible overhead` | runtime/communication/memory curves |
| Scope | `evaluated datasets, topologies, non-IID degrees, label ratios` | `general DFL solution` | larger real-world FL workloads |
| Reproducibility | `code and implementation details are provided` | `fully reproducible everywhere` | seeds, exact scripts, environment lockfile |

## 12. Executive Recommendation

最推荐的主线是：`SemiDFL is an interface-closure paper, not a component-combination paper.`

把 abstract、intro、contribution、method overview 和 Figure 1 全部围绕“三个 missing consensus interfaces”重写。实验部分不要只报告 accuracy，而要显式说明：Table 1 是端到端，Figure 2 是 non-IID robustness，Figure 3 是 label scarcity，Table 2 是 label-space consensus，Table 3 是 data-space consensus，Table 4 是 model-space consensus。这样最能防 novelty、A+B/C、mechanism、baseline fairness 和 scope 攻击，同时不需要新增实验即可显著改善顶会叙事。
