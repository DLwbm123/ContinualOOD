# Training-Free Continual OOD 肿瘤分割：Codex 启动文档

**文档版本：1.0 ｜ 编写日期：2026-10-16**  
**交付性质：研究实施说明、接口约定与配置草案；不是已完成的算法实现，也不包含已获得的实验结果。**  
**首轮目标：小规模数据审核 → R2-Seg 可追踪复现 → 当前参考诊断 → 有界历史参考记忆 → 可复现实验报告。**

---

## 0. 交给 Codex 的任务摘要

在当前工作目录中建立或接入一个研究项目，暂用项目标识 `continual-ood-tumor`，Python 包名建议 `continual_ood`，命令入口建议 `cood`。不要擅自创建新的远程仓库，也不要把目录结构覆盖到已有项目上。

研究目标是在**不更新基础模型网络参数**的条件下，利用持续到达的未标注检查构建有限参考状态，改善肿瘤分割及病灶检出。最终覆盖三个场景：

| 场景 | 变化内容 | 要回答的问题 | 实施顺序 |
|---|---|---|---|
| S1：同类肿瘤的持续域偏移 | 中心、设备、成像条件、患者分布 | 参考经验能否持续积累，并在旧域返回时有效？ | 首轮主任务 |
| S2：新肿瘤类型/新解剖部位出现 | 目标分布、解剖语义及可能伴随的域变化 | 历史是否帮助未见病灶，还是产生负迁移？ | S1 后扩展 |
| S3：同患者纵向随访 | 病灶范围、出现/消失及治疗相关状态 | 既往影像能否帮助当前分割而不压制真实变化？ | 最后扩展 |

**第一轮执行到 P5 为止。**优先 FedBCa 的 40–60 名独立患者，不全量下载 CancerVerse，不同时实现所有纵向或跨器官扩展。原始数据包若只能整体下载，可以下载获许可的小型完整压缩包，但只处理冻结清单中的病例。

核心待验证假设是：**匹配的解剖参考及其自然波动可以改善候选判别；不匹配或受污染的历史参考可能导致负迁移；保守读写能减轻这一问题。**这是假设，不是结果，不得预填性能或预设方法一定成功。

启动包内的 `configs/*.yaml` 与下文 CLI 是**要求 Codex 实现的项目接口**，不是上游 R2-Seg 已支持的参数或已存在的命令。先实现并测试，再执行。

---

## 1. 来源边界与本次核查发现

文中 `[P1]`、`[P2]` 指用户给定论文，`[S1]` 等指官方在线来源；完整目录见第 18 节与 `docs/SOURCES.md`。所有未注明来自论文/公开代码的算法细节、阈值、抽样规模、接口及验收标准，都是**本项目的初始设计**，不是论文原设定。

### 1.1 从论文继承什么

R2-Seg 使用冻结 BiomedParse，先通过解剖锚点和多尺度 ROI 产生候选，再比较候选与器官参考的分布，使用 MMD、置换检验、BH 校正及附加假阳性过滤。其 Figure 2 位于 PDF 第 4 页，方法细节见第 3–5 页。[P1]

CancerVerse 提供 CT、多癌种标注和纵向信息；其原文以确诊索引及可获得的既往检查构建轨迹，评价病灶级敏感性与 FP/scan。论文第 4 页明确，目标阴性队列不等于全身没有其他疾病或癌症。[P2]

### 1.2 必须纠正的实现预期

**R2-Seg 的公开 `evaluate_candidates()` 已经计算 `organ_mask AND NOT lesion_mask`。**因此，“排除当前候选”不是新增贡献。可研究的是：排除所有候选及其邻域、组织条件化、参考有效性判断、持续历史校准与污染防护。[S3]

公开代码还显示：候选提取使用阈值 0.4；常见统计配置最小区域为 50 像素；`PipelineOutput.candidate_results` 返回的是经过筛选的候选。完整错误追踪必须在筛选之前另存全部候选。代码在空锚点时可退回全图，但**本项目不得把全图回退区域写入“正常器官记忆”**。[S2]

公开配置的数据类默认关闭附加 FP mitigation，但命令层可能覆盖；最终配置必须由代码运行后导出，不能仅根据 README 或数据类认定开关状态。[S4]

**BiomedParse 版本必须匹配。**R2-Seg 配置指向 `biomedparse_v1.pt`。当前官方 BiomedParse 页面包含 v2，不能直接照抄其当前默认安装和推理流程来替代 v1。官方权重入口目前提示访问条件；仅在用户已有授权或完成确认后下载，不代替用户接受条款。[S4][S5][S6]

### 1.3 尚未核实，不能当成已知

目前没有在本启动包中下载并检查 FedBCa 原始压缩包，也没有完成 BiomedParse 权重加载、真实病例推理或性能复现。FedBCa 的患者关联、完整视野、标注完备性、各中心可用人数，以及纵向数据的具体配对情况，都要在 P1 实际审核。

论文、代码与当前数据版本可能不一致。建立 `reports/SOURCE_AUDIT.md`，逐项记录差异；不要默默把某一版本的细节当成另一版本。

---

## 2. 不可违反的研究与工程约束

### 2.1 Training-free 与信息权限

基础模型使用 `eval()` 和 `torch.inference_mode()`；所有参数 `requires_grad=False`。不调用反向传播，不创建用于适应的优化器，不更新 BatchNorm 运行统计，不训练 LoRA、分割头、门控网络或域分类器。

允许更新：有限参考样本、统计摘要、检索索引、患者历史预测及其来源记录。传统配准的变换优化属于单独的图像对齐，不得描述成整个流程没有任何优化。

开发集标注仅用于开发诊断和预先确定少数超参数；正式流中的标注只进入隔离的离线评价器。报告表述为“部署阶段无目标标注、无网络参数更新”，不自动声称开发也完全零标注。

**推理输入不得包含：**当前肿瘤真值、由真值产生的包围框/点提示、当前癌种真值、阳性切片列表、未来检查、未来确诊信息、评价得到的 TP/FP 标记、用于定义域的真实中心 ID 或阶段边界。

器官查询由冻结的任务设置给出。在单器官实验中，对每次检查询问同一个目标；多器官实验使用预先固定的查询集合，不能按患者真值选择正确目标。

### 2.2 时间与状态

每次检查采用 **predict → persist prediction → update memory**。群体记忆按整次检查更新，不逐切片更新。

同一检查的多个序列和切片共享一次逻辑检查事件，除非预先明确另一种任务定义。禁止在处理当前检查时读取其更新后的群体记忆。

独立 probe 评价不更新记忆，不改变后续流的 RNG 状态、写入计数或淘汰顺序。允许预计算冻结模型输出，但在线模块只能按序读取当前及过去条目。

### 2.3 数据、隐私与版本

所有患者的检查、重复体数据、同体数据的多病灶副本和裁剪必须绑定同一分组。先划分患者，再派生切片。

缺失标注不等于空掩膜；部分病灶标注不等于全扫描完整标注；阳性病例中的阴性切片不等于健康阴性检查。

默认不向外部 LLM 上传影像、病历、报告或患者元数据。使用固定解剖计划，不需要在线 LLM 服务。

原始数据、权重、病例级预测、特征记忆、日期及患者对应表不得进入 Git。特征记忆也可能包含患者信息，不宣称形式化隐私保证。

每轮固定源代码 commit、模型 revision/校验和、数据记录版本/文件校验和、配置、患者划分、流顺序及随机种子。不得边跑边更新依赖或数据。

---

## 3. 数据准备：先小型 MRI，后选择性 CT

### 3.1 下载前先生成清单，不直接跑全量脚本

下载器需要支持 `--dry-run`、文件大小预算、断点续传、校验和检查和明确错误状态。未知大小的下载不应绕过预算。禁止执行未经检查的远程脚本，也不要猜测数据文件名或私有下载地址。

首轮建议预算：新增数据下载不超过 5 GiB，模型及必要资产不超过 10 GiB，工作目录总量不超过 50 GiB。它们是保护性默认值，不是数据大小预测。超过预算时输出清单请求确认；不得自动清理用户既有文件腾空间。

### 3.2 FedBCa：首轮主数据

官方数据论文报告 275 个三维 T2 MRI 样本、228 名患者和四个中心；版本记录中可见约 1 GB 的 `FedBCa.rar`。旧记录页面还提示存在更新版本，下载前应跟随官方版本关系并锁定选定版本，不硬编码“最新”等于旧记录。[S7][S8]

获取步骤：

1. 读取官方论文和 Zenodo 记录，记录许可、版本、文件列表和 checksum；如果现有本地数据已校验，优先复用。
2. 下载数据到 Git 之外的 `COOD_DATA_ROOT/raw/fedbca/<version>/`，只读保留原始包。安全解压，检查路径穿越与异常文件。
3. 按真实目录结构实现适配器，不按论文扫描总数生成虚构 ID。
4. 检查每个文件代表独立扫描、同一扫描的病灶副本，还是裁剪 ROI。比较标识、体素内容、shape、affine 与可用元数据。
5. 核查同一体数据的多个病灶掩膜是否可合并：只有确认来自相同物理网格、不同真实病灶时才取并集，并记录来源。不能把不同裁剪或不同时间的掩膜直接相加。
6. 核查标注范围：全检查所有目标病灶、仅索引病灶、局部切片、还是不明确。后几种不能直接用于全检查 FP/scan。
7. 每中心抽取至少 2 个检查做影像—标注叠加检查；额外检查所有异常几何和多病灶样本。

**硬性分岔：**若患者映射无法建立，暂停正式持续实验；仍可做少量去标识 smoke test，但必须标记“非独立患者验证”。若只有 GT 引导裁剪，任务应改标为病灶 ROI 分割，不能报告无提示筛查或完整检查误报。不得用自动填充空白区伪造全视野。

本数据为膀胱癌患者队列，不据此报告健康人筛查特异性。[S7]

### 3.3 Prostate158：新器官扩展

先使用 T2 MRI，保持模态较接近。官方项目说明包括解剖区域和癌灶标注；训练/测试原始记录分别列在来源目录，部分页面本次核查出现限流或超时，Codex 必须重新验证，不把候选地址的存在等同于下载已成功。[S9][S10]

核查 tumor mask 与 anatomy mask 的标签含义，不能把全前列腺标注当作肿瘤。DWI、ADC、T2 或不同读者掩膜不得计为不同患者。保留官方测试集边界，不将其加入开发调参。

**跨器官同时跨数据来源时，结果命名为“新部位＋来源变化”，不宣称已单独识别纯语义偏移的效果。**

### 3.4 CC-Tumor-Heterogeneity：纵向扩展候选

R2-Seg 引用了该放疗过程连续影像来源；官方条目索引显示 23 名患者及 MR/RTSTRUCT 等内容。本次正文访问失败，因此具体下载方式、逐时间点标注和可用序列均保持待审核。[P1，参考文献 27][S11]

第一步仅下载获授权的目录/元数据或小样本，审核患者、时间点、序列、RTSTRUCT 引用的影像 UID，以及哪些时间点可构成有真值的评价对。不要假定 23 人都可形成完整随访轨迹。

RTSTRUCT 转换必须基于引用的物理坐标和序列，不按文件名猜对应关系。只把目标肿瘤体积纳入评价；GTV、CTV、PTV 等结构名称需要明确审核，不能混同。注册、轮廓栅格化和时间排序分别做质控。

日期无法可靠排序或轮廓无法可靠对应时，该分支标记 `BLOCKED_DATA_AUDIT`；不得用文件排序伪装为临床时间。

### 3.5 CancerVerse：仅按需要扩展

先读取元数据和远程文件清单，再选病例。官方数据卡列出逐检查目录和肿瘤标注入口，并区分当前发布版与原论文规模；全量脚本不是本项目的默认入口。[S12]

初期 CT 扩展计划为 100–200 次经审核检查，只是规模建议。纵向子集按患者轨迹选取，而不是随机抽扫描。明确目标阴性定义与 annotation completeness；无对应 mask 文件首先记为 `unknown`，只有发布说明和元数据能确认时才认定为真阴性。[P2]

下载器必须只请求选定检查及所需标注。先确认标注是否支持逐文件下载；若只能取大归档，先报告大小和选择，不能为了少量病例自动下载全部影像/标注。

无需下载报告、病理全文或临床变量来完成首轮影像实验。对公共数据之间的来源重叠与重复影像进行审核。

---

## 4. 数据清单、几何与划分

### 4.1 三种清单分离

不要给推理器一个包含标签、中心和阶段的“万能 DataFrame”。

| 文件 | 使用方 | 核心字段 |
|---|---|---|
| `runtime_manifest.jsonl` | 推理器 | `study_uid`、`patient_key`、影像路径、模态/序列、几何侧车、允许的先前检查 ID |
| `evaluation_manifest.jsonl` | 独立评价器 | `study_uid`、标签路径/映射、标注完备性、目标范围、读者版本 |
| `split_registry.jsonl` / `stream_schedule.jsonl` | 划分器、调度器、报告器 | 患者分组、来源中心、dev/stream/probe、流索引、阶段与顺序种子 |

患者与检查 ID 使用项目内不透明标识；原始对应表仅保存在受限本地目录。清单里的类别真值、中心 ID 和评价信息不能流入方法接口。

`sources.lock.json` 记录代码 commit 和资产 revision；`dataset_audit.json` 记录实际患者数、检查数、缺失率、可评价范围及排除理由。

### 4.2 必须保存的几何

保留原始 shape、voxel-to-world affine、spacing、orientation、原始序列标识和所有重采样变换。NIfTI qform/sform 不一致时报告并人工/规则审核，不能直接覆盖。

工作数组可以采用明确的 `[z, y, x]` 约定，但必须与坐标变换统一。切片输入的 spacing 是 `[row_mm, col_mm]`，不能从原始三维 spacing 随意取前两项。

默认不为了统一尺寸而把原始体数据强制重采样成 1 mm 各向同性。依照经过审核的视图生成二维输入，保留可逆映射，在原生网格评价。图像重采样与标签重采样应分别采用合适的连续插值与最近邻插值。

基线的 uint8/RGB 输入严格依照锁定的 v1 路径；灰度复制、百分位裁剪、缩放都必须有记录。研究统计分支可以使用当前体数据的独立强度归一化，但所有比较方法保持相同，且必须与基线输入变化分开消融。

MRI 初始统计归一化建议：当前检查影像内的非零有效支持上计算 1/99 百分位，裁剪后映射到 `[0,1]`。若有效支持或动态范围不足，返回 `INVALID_INTENSITY`，不通过加入 GT 或未来扫描修复。CT 采用独立冻结的窗宽规则，不能复用 MRI 百分位规则冒充 HU 处理。

不得以真值筛选“值得处理的切片”。正式检查处理全部符合预设采集范围的切片；快速 smoke test 可以用按索引等间距抽样，但不能据此计算完整检查性能。

### 4.3 首轮 60 人计划：仅在审核支持时采用

优先选择至少有 20 名可用独立患者的三个中心，每中心 20 人：4 dev、10 stream、6 probe。合计 12 dev、30 stream、18 probe；组间严格患者独立。

S1 首个流设为 `A_first(6) → B(10) → C(10) → A_return(4)`，所有检查来自不同患者。probe 集在阶段边界重复只读评价；A_return 是旧域的新患者，不是旧病例重放。

如中心人数不足，按真实数量重新生成 40–60 人计划并输出差异；可以用两个中心，但不得凑患者或把多个病灶副本视为独立患者。选择中心只依据可用量和数据质量，不能依据算法表现。

默认患者划分种子 42。确认流程正确后，以相同患者集合运行三个预定义顺序种子 `[42,43,44]`。第一轮单顺序仅用于调试，不能报告顺序稳健性。

正式实验开始前冻结划分、超参数与评价规则。probe 结果只能用于当前冻结版本的评价；若查看 probe 后继续改方法，该集合应降为开发用途，另设未触碰测试集。

---

## 5. 模型接入与原始 R2-Seg 复现

### 5.1 保留两条明确标识的路径

`B0_R2_NATIVE`：锁定上游提交与有效配置，保留其原始候选生成、MMD/BH、门控及输出。工程插桩不得改变预测。

`RESEARCH_SHARED_PROPOSALS`：使用相同冻结模型前向结果，但采用本项目统一三维候选/评分接口，用于比较当前参考与历史参考。它是新实验路径，不得标为“完全复现原方法”。

模型接入包装 `FrozenBiomedParseBackend`。优先包装现有实现，不重写网络、不引入另一基础模型。先记录缺失/多余 checkpoint keys；未能正确加载时直接失败，不能 `strict=False` 后宣称加载成功，也不能以随机参数继续跑真实实验。

### 5.2 环境先探测，不能盲装最新版本

记录 OS、Python、CUDA/驱动、GPU 型号/可用显存、RAM、磁盘和环境工具。参考锁定 R2-Seg 版本的环境文件构建隔离环境。不要覆盖全局 CUDA、驱动或其他用户环境；不要为了装依赖默认调用 sudo。

v1 环境兼容性通过实际 import 和单样本测试确认，不能拿官方 v2 的新依赖列表当作 v1 安装说明。[S5]

无 GPU 时可继续 CPU 单元测试和数据审核，真实 GPU 推理任务标记阻塞。不默默退回 CPU 后让用户误以为 GPU 实验正常运行。

### 5.3 固定提示和计划

使用 `run_with_plan` 或等效的显式计划接口，禁止运行时调用 LLM。先从上游模板/已公布示例导出计划，保存为配置并检查其 anchor vocabulary。

对同一任务中的全部检查使用一致的目标查询。不得通过阳性掩膜、病理诊断或文件夹癌种标签为每例选择正确查询。单器官研究的任务目标是显式给定条件，不等同于全身自动发现癌种。

未知提示或不兼容模型词表时，记录为 `UNSUPPORTED_QUERY`；不得悄悄退化为只分器官后作为肿瘤结果。

### 5.4 插桩与一致性

每次检查缓存：各切片原始概率图、锚点概率/掩膜、ROI 变换、视图预测或一致性摘要、全部原始候选、各步保留/删除理由、最终结果。

上游输出文件名存在按目标概念命名的路径，因此包装器必须显式使用检查/切片唯一目录，不能让不同病例覆盖。[S2]

在固定随机状态下比较未插桩与插桩路径：概率误差、二值掩膜、统计量和候选保留集合均记录。用 10 张固定输入做初始 parity test；同一版本 FP32 路径目标为二值结果一致。近阈值数值差异必须解释，不通过放宽阈值掩盖。

若发现真实代码错误，保留可复现的 native 路径，另建 `B0_R2_PATCHED` 及 patch diff，报告影响，不静默修改对照。

---

## 6. 分阶段方法实现

### 6.1 第一组：只改变当前参考，判断研究空间

实现 `B1_R2_LOCAL_CONTROL`，相对 native 只改变参考选择，其余候选、MMD、BH 和门控保持不变。

依次检查：原代码当前候选排除 → 排除全部候选 → 再加物理邻域排除 → 按预测器官内部位置限制参考。每一步独立命名，不将全部变化打包后声称是某一模块的作用。

当前参考区域初始形式：

`R = predicted_anchor_support - dilate(union_of_all_current_proposals, 3 mm)`。

3 mm 是项目试验起点。参考的 shell/core 可依据预测器官内到边界距离的固定分区定义；不能用候选强度选一个最像候选的正常组。器官锚点可能包含腔内容物而非对应组织，必须审核其语义，并在分组不可靠时停用该参考。

当锚点为全图回退、剩余区域过少、候选几乎占满器官或 compartment 无法匹配时，标记参考无效。native 的处理保持原样；研究分支则取消该项参考修正，而不是因“无法检验”就删除候选。

开发诊断可构造 `ORACLE_CLEAN_REFERENCE_DIAGNOSTIC`，用真值去除参考中的病灶，仅测试潜力。它不能参与正式在线状态，也不能进入主结果表。

### 6.2 第二组：统一候选上的研究对照

为避免三维候选、评分和记忆同时改变造成混淆，增加两个不可省略的对照：

| 标识 | 当前参考 | 历史检索 | 写入策略 |
|---|---|---|---|
| `C0_CONFIDENCE_ONLY` | 无 | 无 | 无 |
| `C1_CURRENT_CALIBRATION` | 项目经验校准 | 无 | 无 |
| `B2_FIFO_MEMORY` | 同 C1 | 同器官/序列内最近参考，不做上下文匹配 | 基本候选排除 |
| `B3_MATCHED_MEMORY` | 同 C1 | 加上下文匹配及回退 | 与 B2 相同 |
| `B4_SAFE_MEMORY` | 同 C1 | 与 B3 相同 | 加可靠性写入保护 |

B2/B3/B4 共享固定容量、候选、距离、评分公式和计算预算。B4 必须与 C1 比较，不能仅与原始 R2-Seg 比较后将所有差异归功于 continual memory。

研究候选：由冻结的全图/ROI 融合概率图在阈值 0.4 下生成，恢复原生三维网格后提取 26 连通域。首版不额外删除小三维区域。native 的 50 像素规则只保留在 native 路径，不能悄悄放松它来制造性能差距。

在这组研究比较中，候选形状与集合固定，方法只改变分数/是否输出。候选内边界不被重新训练或细化。候选缺失或巨大连通块的情况单独报告，必要时停止参考路线、转向候选生成，而不是声称评分能修复所有分割问题。

### 6.3 非目标组织参考与经验异常排序

首版使用独立统计支路中的归一化强度，不依赖新编码器。冻结深层特征只作为后续消融，不与记忆机制同时引入。

距离初始采用有偏、非负的 Gaussian-kernel MMD²：

`D(X,R) = mean(k(X,X)) + mean(k(R,R)) - 2*mean(k(X,R))`，

其中 `k(a,b)=exp(-||a-b||²/(2σ²))`，`σ=0.1`，输入已映射到 `[0,1]`。这是研究支路的工程定义，与原始无偏 MMD＋置换检验不同，故必须保留 C0/C1。不要把不同估计器混在同一“原方法复现”结果中。

每个候选最多取 256 个强度样本。使用由 run seed、study UID、candidate UID 派生的局部随机生成器，不依赖可变的全局调用顺序。参考与 null patch 使用匹配的样本数；小于 16 个有效样本时该统计项不可用，不通过重复采样伪造独立样本。

对当前或某个历史 donor 的参考分为相互不重叠的 `R_fit` 和若干 null patches `N_i`。计算：

`d_C = D(X_C, R_fit)`，`a_i = D(X_Ni, R_fit)`。

经验排序为：

`r(C) = (1 + count[a_i <= d_C]) / (N + 1)`。

每个候选的 null patch 在同一预定义 compartment 中，物理尺度按候选等效直径归入 `[4,8,16] mm` 档位。候选过大、对应尺寸参考不足，或 null patch 不够时禁用该项并记录。首版有效 null patch 目标 6，最低 4；这是稀疏诊断性排序，不能声称有精确尾概率估计。

`R_fit` 与 null patch 不得使用同一批体素，且所有候选/候选邻域均被排除。历史条目要保存足以重算的紧凑样本与分组，而不是把不同 kernel、不同归一化产生的标量直接合并。

**该排序不是肿瘤概率、p 值或风险保证。**伪正常污染、空间相关、参考选择与在线分布变化都未被这一简单构造消除。

### 6.4 候选评分：有限修正，而非必须服从历史

候选原始证据 `q_C` 定义为固定候选区域内概率的均值，裁剪到 `[1e-4,1-1e-4]`；所有研究方法使用相同定义。

建议初始分数：

`score(C) = logit(q_C) + λ_local*w_local*(2*r_local-1) + λ_hist*w_hist*(2*r_hist-1)`。

初始 `λ_local=0.5`、`λ_hist=0.5`。`w_local` 在参考有效时为 1，否则 0。历史分数为兼容 donor 排序的中位数；donor 数不足时 `w_hist=0`。

上下文描述先用参考组织的固定强度分位数向量 `[0.1,0.25,0.5,0.75,0.9]`。同器官、模态、序列、工作视图的记录才可匹配；描述向量的平均绝对差作为距离。检索 top-3 个不同患者 donor，距离大于 0.15 的不使用；少于 2 个 donor 则退回 C1。不要把真实中心 ID 当作检索键。

可令 `w_hist = max(0,1-d_bar/0.15) * max(0,1-MAD(r_j)/0.25)`，范围限制为 `[0,1]`。B2 不应用上下文距离权重，但采用相同 donor 数要求和排序分歧处理。以上阈值都是初始设计，开发集可按预注册小范围检查，正式流不再调整。

第一轮固定输出阈值为 score ≥ 0，同时输出完整候选 score 用于 FROC。开发阶段可以确定一个冻结阈值版本；不得在每个测试域按标签重新选阈值。没有兼容记忆时，B3/B4 必须与对应 C1 输出一致。

边界：有界修正减少了极端干预，不代表数学上保证不会删除真病灶。真实敏感性变化必须通过实验评价。

### 6.5 记忆条目、容量与写入

`ReferenceEntry` 至少包含：来源检查/患者的不透明 ID、写入流索引、anchor、模态/序列/视图、上下文分位数、物理尺度档、参考样本、null-patch 样本、质量标志与记录版本。

默认最多 64 个检查条目，每检查最多 24 个参考 patch（每个物理尺度档最多 8 个，R_fit 与 null patch 均计入），每 patch 最多 256 个 float32 样本；全部序列化群体状态硬上限 64 MiB，达到任何一个上限都必须淘汰。实际字节数以测量为准。三个方法不能通过隐藏缓存突破预算。

B2/B3 基本写入：预测锚点有效，排除全部当前高召回候选与 3 mm 邻域，满足最低参考量后才写入。

B4 在此基础上要求：锚点区域平均预测置信度至少 0.8、参考区所有保留视图的目标概率不高于 0.1、视图概率标准差不超过 0.05。若上游未保留逐视图概率，必须先实现捕获，不能用全零方差替代缺失信息。常量、损坏输入或 full-frame fallback 不写入。

写入条件不读取最终是否被判为 TP/FP，也不将“统计不显著的候选”视为正常。首版不以多次出现作为正常确认，不设置假定可靠的“已确认正常”标签。

按病例有限写入，不能让一个长序列贡献几千条样本。默认 FIFO 淘汰用于所有方法以控制变量；上下文多样性保留单独作为后续消融。

当 B4 几乎无有效写入时，报告 `memory_write_coverage`，不能悄悄降低可靠性阈值让方法看起来在学习。

---

## 7. 在线运行、缓存与可恢复性

### 7.1 执行伪代码

```python
# 接口示意，需 Codex 实现；没有当前真值或真实中心参数。
for event in stream:
    snapshot = memory.read_only_snapshot()
    study = runtime_reader.load(event.study_uid)
    raw = backend.forward_or_verified_cache(study, frozen_query_policy)
    proposals = proposal_builder(raw, study.geometry)
    prediction, diagnostics = method.predict(study, raw, proposals, snapshot)
    persist_prediction_atomically(prediction, diagnostics, snapshot.version)
    writes = method.propose_writes(study, raw, proposals, snapshot)
    memory.commit_after_prediction(event, writes, expected_version=snapshot.version)
```

同一检查的所有目标查询完成后才能写入。评价器在独立进程或明确隔离的任务中读取 prediction 与 evaluation manifest；评价结果不得回传给在线算法。

### 7.2 缓存必须带来源哈希

缓存键包含模型 checkpoint checksum、代码 commit、预处理版本、原始影像 checksum、提示/计划 hash、视图设置及数值精度。改变任一字段则缓存失效。

允许并行预计算所有检查的冻结前向结果；它们不是在线记忆的一部分。在线方法接口只能收到当前检查的数据，不能把未来候选统计用于标准化、kernel 选择或参数配置。

同时报告端到端推理时间和缓存后的参考模块时间，不能将后者冒充全系统时延。

### 7.3 恢复与审计

每个检查完成后保存流位置、记忆版本、RNG 状态、配置 hash 和资产锁。恢复时要求 hash 一致。同一检查不能重复写入，半次检查失败不污染记忆。

记忆快照使用受控格式，例如 JSON＋NumPy 数组，不从不可信来源反序列化任意对象。模型权重也仅加载经过核验的可信官方/用户授权来源。

---

## 8. 三个场景的独立定义

### 8.1 S1：域持续变化

使用同一器官、同一序列家族，中心仅用于调度与分组报告，不作为算法输入。默认 A→B→C→A_return；增加混合顺序后再讨论任务边界不可见的稳健性。

每阶段评估固定 probe 集，更新状态关闭。记录 Dice、固定阈值敏感性/误报、候选召回、记忆写入量、检索命中率与回退率。旧域回访使用新患者。

### 8.2 S2：新肿瘤类型/部位

先准确称为“适应流中未见类型”，除非已完成基础模型预训练来源审核，否则不能称为 pretrained-unseen。

在新类型进入流之前，用只读独立评价集计算 `FWT_j = R(M_before_j,E_j) - R(M_empty,E_j)`；之后接触新类型的未标注检查，再评价适应曲线与旧类型保持。

**结构性限制：**本项目首版严格按器官分开参考。新器官若没有兼容历史，输出应退回 C1，因此首次接触前的跨器官 FWT 可能严格为零。这不是实现错误，也不是正向迁移。必须报告“避免负迁移”与“产生正向迁移”的区别。

如要证明跨器官正向迁移，需要新增明确的可共享信息，例如所有检查预先固定查询的共享正常锚点；只有这些结构确实在视野中、且没有借用 GT 时才允许使用。该扩展应另列方法和计算预算，不在 P0–P5 默认实现。

Prostate158 和宫颈癌数据若出现序列、平面和来源变化，应同时记录。完整影像可能已经包含另一目标器官或病灶，留出类型需按可审核标注检查，不能只按主诊断名称分组。

### 8.3 S3：纵向患者历史

首版采用“历史定位 → 当前影像重新查询”，而非复制历史肿瘤掩膜。固定当前独立分割路径；历史只增加至多 2 个 ROI 查询，不排除其他区域。

记忆分两层：群体 `M_pop` 与患者 `M_pat`。初始 S3 实验冻结已得到的群体状态，仅更新当前患者历史，以隔离个体随访收益；组合持续更新作为后续实验。

以当前检查为 fixed、上次检查为 moving，配准映射定义为 `φ: Ω_current → Ω_previous`。注册优先刚性/仿射，形变方法后置。检查器官对齐、重叠视野及数值异常；不以当前肿瘤真值判断是否启用历史。

从历史预测掩膜生成旧病灶包围范围，经可靠空间对应映射到当前后扩张，再对当前图像重新运行冻结分割器。历史的存在不强制当前非空，历史的缺失也不否定当前新发病灶。

所有方法获得相同既往信息；历史人工标注仅列为独立辅助信息条件。加入“当前影像同等额外 ROI 次数”的计算量匹配对照。

核心比较：`H0_current`、`H1_warp_previous_mask`、`H2_direct_fusion`、`H3_history_guided_requery`、`H4_compute_matched_current_requery`。不得默认把这些模块称为完整 continual learning，必须通过状态保留/重置对照说明其时间积累价值。

---

## 9. 评价规范

### 9.1 主指标与适用范围

阳性检查上的三维 Dice：漏检的阳性检查计 0；不把大量 GT/pred 均为空的切片混入主平均。空病例另报告扫描级特异性与 FP/scan。没有可靠阴性检查时，特异性返回 `NA`，不是 1。

病灶级指标只在标注完整性满足预设要求时报告。首版将二值 GT 转为 26 连通病灶；若有可靠实例标签则优先使用实例标签并单独说明。分辨率导致相邻病灶粘连时记录限制。

匹配规则项目初值：三维 IoU ≥ 0.1，按预测候选分数降序，每个预测最多匹配一个未匹配 GT，并选择最大 IoU；每个 GT 最多被匹配一次。并列分数按稳定候选 ID 处理。这个阈值不是 CancerVerse 官方定义；其论文未在给定正文里提供完整匹配实现。补充报告 0.05/0.25 匹配阈值敏感性分析，但不能择优当主结果。

FP/scan 分母是具有完整目标标注的独立检查数，阳性检查中的非匹配预测也计 FP。多目标部署应汇总一次检查的全部目标查询误报，不把各器官分别允许的误报预算当作系统总预算。

若只具备部分标注，应输出可支持的局部分割指标；不得将所有未标注预测计 FP，也不得直接忽略它们后声称完整 FROC。

### 9.2 FROC 与在线工作点分开

在固定候选分数上遍历阈值绘制经验 FROC，报告 0.25、0.5、1.0 FP/scan 预算下可实现的最大敏感性。初版采用保守经验阶梯值，不做向不可达区间的外推。

全拒绝点应显式存在。若没有非空工作点达到低误报预算，则报告该预算下敏感性为 0，并标明无非空可行工作点；若该任务缺乏完整标注或有效分母，则为 `NA`。不能将这两种情况混同。

FROC 是测试描述性指标；实际部署只用预先冻结的 score 阈值。每个测试域用标签重新选阈值的结果不能称为在线无标注工作点。

### 9.3 持续指标

建立 `R[t,j]`：阶段 t 后在域/类型 j 的固定 probe 集上只读评价。固定阈值 Dice/敏感性为主，FROC 派生指标另列。

`BWT = mean_j<T (R[T,j]-R[j,j])`。FWT 使用新类型进入流之前的快照与空记忆基线，测试不写入。报告各顺序原始结果，不只给一个均值。

状态重置对照与正式方法使用相同当前影像、参数和计算量，只改变跨检查状态是否保留。

### 9.4 纵向指标

在每次检查原生物理空间上计算体积，不以变形后的体积代替真实变化。体积变化误差：

`E_deltaV = abs((Vhat_t-Vhat_prev)-(Vgt_t-Vgt_prev))`。

单独报告新发病灶检出与旧病灶不再可见时的错误延续。新发/消失分组依赖经核实的跨时间病灶对应或专家标注；不能用算法配准后的无重叠自动作为临床真值。

若仅有肿瘤总体积，无病灶身份对应，则只报告检查/器官级变化，不声称病灶级新发识别。治疗反应类别需要对应临床定义与治疗时间支持，不由体积变化指标自动推导。

### 9.5 诊断与不确定性

所有阶段保留候选召回、ROI 覆盖（仅离线 GT 诊断）、被各过滤级删除的真实病灶数、小病灶表现、参考污染率、记忆占用与回退率。

参考污染率只能由隔离评价器用 GT 事后计算，不用于写入控制。没有完整 GT 的区域，不声称已测得真实污染率。

按患者聚类 bootstrap。固定 probe 的区间表示当前快照条件下的不确定性；在线流的完整适应不确定性还需要重跑流顺序，不能将逐检查重采样等同于重跑状态演化。首轮小样本结论标为 pilot。

---

## 10. 模块结构与接口

建议目录如下。现有项目中有等效模块时复用，不复制一套平行框架。

```text
continual-ood-tumor/
  AGENTS.md
  CONTINUAL_OOD_STARTUP.md
  pyproject.toml                       # Codex 实现
  configs/
  src/continual_ood/
    cli.py
    data/                             # adapters, manifests, geometry, splits
    backends/biomedparse_v1.py
    proposals/                        # native trace + shared 3D proposals
    reference/                        # extraction, distances, null ranking
    memory/                           # entries, retrieval, update, serialization
    methods/                          # B0/B1/C0/C1/B2/B3/B4
    streaming/                        # predict-before-update, resume, probes
    longitudinal/                     # P6 后实现
    evaluation/                       # isolated labels, matching, FROC, CL metrics
    provenance/                       # source lock, cache keys, state audit
  tests/unit/
  tests/integration/
  scripts/
  reports/
  third_party/                        # pinned source only, not data
```

推荐接口及返回条件：

| 接口 | 责任 |
|---|---|
| `DataAdapter.index(raw_root)` | 读取真实文件生成受限审核清单，不凭空补记录 |
| `RuntimeStudyReader.load(study_uid)` | 只返回运行权限内影像与几何 |
| `FrozenBackend.predict(study, query_policy)` | 返回可追踪概率、锚点、ROI 与视图摘要 |
| `ReferenceExtractor.extract(study, raw)` | 返回伪非目标参考及有效性原因，无 GT 参数 |
| `ReferenceMemory.retrieve(query, snapshot)` | 只读、确定性、受预算约束，不接收 center ID |
| `Method.predict(..., snapshot)` | 当前预测与诊断，不能写入 |
| `Method.propose_writes(...)` | 单独的写入建议，不接收最终 TP/FP |
| `Memory.commit_after_prediction(...)` | 原子提交、重复事件幂等、版本检查 |
| `Evaluator.evaluate(prediction_root, eval_manifest)` | 独立读取真值，仅输出评价文件 |

异常不得被统一吞为全零预测。至少区分 `FAILED_MODEL_LOAD`、`FAILED_GEOMETRY`、`MISSING_LABEL`、`REFERENCE_UNAVAILABLE`、`UNSUPPORTED_QUERY`、`BLOCKED_ACCESS`、`OUT_OF_BUDGET` 和 `INFERENCE_FAILED`。

---

## 11. 待实现 CLI 与执行顺序

以下为项目 CLI 合同。各命令应有 `--help`，默认不静默下载，不用假输出通过流程。

```bash
# P0：环境与来源审核，不下载完整数据。
cood doctor --config configs/pilot.yaml --output reports/environment.json
cood sources resolve --registry configs/source_registry.yaml --output sources.lock.json
cood data inspect-remote --dataset fedbca --dry-run

# P1：在许可和预算允许后获取并审核真实数据。
cood data fetch --dataset fedbca --config configs/pilot.yaml
cood data audit --dataset fedbca --config configs/pilot.yaml
cood data build-manifests --dataset fedbca --config configs/pilot.yaml
cood data make-splits --config configs/pilot.yaml --seed 42

# P2：模型与插桩一致性；不能用 mock 替代这里的真实运行。
cood model verify --config configs/pilot.yaml
cood smoke --config configs/pilot.yaml --real-studies 3
cood parity --config configs/pilot.yaml --slices 10
cood cache build --config configs/pilot.yaml

# P3：原始路径与当前参考诊断。
cood run --method B0_R2_NATIVE --config configs/pilot.yaml --split dev
cood run --method B1_R2_LOCAL_CONTROL --config configs/pilot.yaml --split dev
cood run --method C0_CONFIDENCE_ONLY --config configs/pilot.yaml --split dev
cood run --method C1_CURRENT_CALIBRATION --config configs/pilot.yaml --split dev
cood evaluate --config configs/pilot.yaml --split dev

# P4/P5：冻结参数后，运行真实未标注流与只读 probe。
cood stream run --method B2_FIFO_MEMORY --config configs/pilot.yaml --order-seed 42
cood stream run --method B3_MATCHED_MEMORY --config configs/pilot.yaml --order-seed 42
cood stream run --method B4_SAFE_MEMORY --config configs/pilot.yaml --order-seed 42
cood evaluate --config configs/pilot.yaml --split stream,probe
cood report --config configs/pilot.yaml --output reports/PILOT_REPORT.md
```

开发器按上述语义实现命令，不必拘泥于内部框架。源解析之后还需显式模型资产下载入口或复用本地权重，是否需要用户授权由 `model verify`/下载检查报告，不默认绕过。

---

## 12. 默认配置说明与调参边界

`configs/pilot.yaml` 是统一配置起点。运行前必须把 source revision、checkpoint hash、实际路径和数据审核状态解析到单独 resolved config；未完成解析时只允许 audit，不允许正式推理。

默认参数的用途是使首次实验可执行，不代表最优。先使用单一默认配置完成 P3；若需要开发调参，仅在 dev 上检查少数单因素改动，例如 `λ_hist ∈ {0.25,0.5,1.0}`。不能将所有阈值、记忆大小、ROI 尺度同时做大规模组合搜索，再把最优 probe 结果当正式结果。

核心消融必须保持：基础模型、前向视图、候选、推理次数、患者序列、评分规则、容量和评价定义一致。增加深层特征、更多 ROI 或额外器官时单列消融并计入计算。

---

## 13. 必须通过的测试

| 测试 ID | 测试内容 | 验收 |
|---|---|---|
| T01 | 参数与模型运行 buffer 冻结 | 预热并固定提示后，连续真实推理前后校验和一致 |
| T02 | 标签隔离 | 修改/删除 eval 标签路径不改变在线预测与记忆 |
| T03 | 中心/阶段隔离 | 改变仅供报告的 center/stage 字段不改变方法输入和结果 |
| T04 | 未来信息隔离 | 替换未来缓存不影响此前检查输出 |
| T05 | predict-before-update | 当前检查预测读取的版本始终是提交前版本 |
| T06 | probe 无副作用 | probe 前后记忆、RNG、事件计数一致 |
| T07 | 无兼容参考回退 | 未见器官、序列或参考不足时 B3/B4 等于 C1 |
| T08 | 原始插桩 parity | 固定输入/随机状态下 native 与 instrumented 一致或差异清楚记录 |
| T09 | 完整候选跟踪 | 被统计跳过/被 BH/门控删除的候选均可追溯 |
| T10 | 物理空间变换 | 各向异性、轴翻转、裁剪后掩膜回到正确原生位置 |
| T11 | 重复扫描与患者分组 | 同患者、同体数据多掩膜不跨 split、不重复计分母 |
| T12 | 缺失不等于阴性 | 无标注、空 GT、部分标注走不同分支 |
| T13 | MMD 与秩分数边界 | 常量输入、空区域、低样本数、NaN、重复值均可解释 |
| T14 | 参考不自比较 | R_fit 与 null patch 不重叠；候选及邻域被排除 |
| T15 | 写入保护 | full-frame fallback、低可靠参考、候选区域不被写入 |
| T16 | 容量上限 | 长合成流运行后条目数、patch 数和实际字节均不超限 |
| T17 | 恢复一致性 | 中断恢复与不中断运行结果、顺序及最终状态一致 |
| T18 | 匹配与 FROC | 一对多/多对一、全空、全拒绝、小病灶及同分候选计数正确 |
| T19 | 缓存失效 | 改变 checkpoint/plan/preprocess 任一 hash 会拒绝旧缓存 |
| T20 | GPU 错误可见 | OOM/无 CUDA 不被吞成成功或无病灶 |
| T21 | S3 时间顺序 | 不能读取当前之后检查；日期缺失不伪造时间 |
| T22 | S3 变化保真 | 合成新发、消失、生长、缩小案例中历史不会强制复制旧结果 |

合成数据用于测试软件性质，必须标记 `synthetic_unit_test`。不得把合成测试数值、mock 概率图或预置数组当作真实医学实验结果。

---

## 14. GPU、效率与实验资源

先单 GPU、batch size 1、FP32 建立正确性基线。记录模型前向、统计模块、I/O 的独立耗时和显存峰值。确定瓶颈后再增加同检查的切片/ROI 批次、数据预取和固定前向缓存。

合理提高 GPU 利用率，但不能占用未分配的 GPU、驱逐其他任务或为了占满显存制造无用计算。多 GPU 可并行运行独立流种子或冻结前向缓存；同一在线记忆仍必须严格顺序提交。

自动批量探测应有显存余量和 OOM 回退，不把失败病例直接跳过。混合精度只在与 FP32 对照检查通过后启用，并记录候选及阈值附近的差异。

不在每个小操作后机械清理 CUDA 缓存；任何性能修改先确认输出一致。统计矩阵按 256 样本上限计算，避免把原始 4k×4k 置换检验无限扩展到每个记忆条目。native 与研究分支计算差异独立报告。

---

## 15. 里程碑、产物与停止条件

| 阶段 | 必须完成 | 主要产物 | 进入下一阶段条件 |
|---|---|---|---|
| P0 | 工作区、环境、来源与预算审核 | `environment.json`、`SOURCE_AUDIT.md`、source lock | 清楚知道能读哪些资产、缺什么授权 |
| P1 | FedBCa 数据审核与患者划分 | 三种 manifest、`DATA_AUDIT.md`、QC 图 | 患者映射、几何与标注范围可解释 |
| P2 | v1 模型加载、真实 smoke、native 插桩 | parity、真实预测、运行日志 | 不是 mock，checkpoint 正确，所有候选可追踪 |
| P3 | 当前参考与候选瓶颈诊断 | `REFERENCE_DIAGNOSTIC.md` | 决定是否存在继续研究参考的空间 |
| P4 | 有界记忆与无泄漏 runner | B2/B3/B4、测试、resume | 核心软件测试通过，回退和容量正确 |
| P5 | 小规模持续流与初步报告 | `PILOT_REPORT.md`、指标、状态审计 | 完整报告正/负结果，不要求性能必然提升 |
| P6 | S2/S3 或 CT 子集扩展 | 独立配置、数据审核与实验 | 依据 P5 证据选择下一步，不默认全做 |

**工程成功与研究成功不同。**B4 没有优于 C1 时，代码可以是正确的，但“持续参考有收益”的假设尚未得到支持。报告零效果或负效果，不能通过修改 probe 规则或筛掉失败病例修饰。

如果候选召回低、oracle clean reference 也无帮助，下一步应转向候选生成或当前影像重新查询；不要先堆叠更大 memory、多个专家或新门控网络。

外部权限、访问失败、患者关联不明、无法配对的标注、数据预算超额、无 GPU 等是明确阻塞项。出现阻塞时继续可以独立进行的代码/单元测试工作，集中输出 `BLOCKERS.md`；不反复请求用户确认已明确的普通工程细节。

---

## 16. 报告必须回答的问题

`PILOT_REPORT.md` 至少包含以下信息：

**实际完成了什么。**真实患者/检查数、中心数、使用的数据版本、checkpoint、运行配置、处理范围和失败病例数。

**错误发生在哪里。**ROI 缺失、候选缺失、候选连片、统计筛除、附加门控各造成多少问题。明确哪些指标有完整 GT 支持。

**参考有没有价值。**B1 对 native、C1 对 C0 的比较；如使用 oracle clean reference，单独展示，不计入部署方法。

**历史有没有额外价值。**B2/B3/B4 对 C1，状态重置对照、旧域返回、参考检索/写入覆盖，以及隐藏标签诊断的污染率。

**是否牺牲病灶敏感性。**固定阈值与固定误报预算结果、大小分层、代表性漏检，不能只报平均 Dice。

**成本与限制。**端到端运行时间、额外模型调用、CPU/GPU/显存、记忆真实字节、缓存大小、全部回退和无法完成的事项。

每个指标文件携带 `data_scope`、`annotation_scope`、`method_id`、`config_hash`、`source_lock_hash`、`stream_order_hash` 和 `is_real_run`。没有真实运行输出，不生成看起来像已完成结果的表。

---

## 17. 工作区、Git 与交付规则

先读当前工作区已有 `AGENTS.md` 和 README，检查 `git status`、远程及未提交改动。保留用户既有工作，必要时只增加本项目子目录；本启动包的规则应合并，不覆盖已有更具体规则。

每个完成里程碑形成清楚的 commit。若工作区已有用户授权的远程，按已有工作流推送代码、配置、测试和不含敏感信息的汇总报告。不要猜测远程地址，不新建公开仓库，不强推，不提交数据或权重。

推送前检查 staged 文件、体积和敏感内容。病例对应表、原始日期、影像、特征、预测及带患者细节的 QC 图保持本地。远程缺失或权限失败时记录，不能宣称 push 成功。

交付包含可运行源码、锁定环境、配置、数据审核、真实 smoke 输出说明、测试结果、研究报告与阻塞项。只有骨架或 mock 时明确写“骨架完成，真实推理尚未完成”。

---

## 18. 来源目录与访问状态

以下 URL 供 Codex 核验与获取官方资源。页面核查日期为 2026-10-16；未锁定 commit 的在线内容可能改变，运行时必须解析并记录。

- **[P1] 用户提供 PDF。**Shen 等，*R²-Seg: Training-Free OOD Medical Tumor Segmentation via Anatomical Reasoning and Statistical Rejection*。第 3–5 页：方法；第 5 页：数据与评价；第 8 页：敏感性权衡。PDF 不随启动包重新分发，可由用户在工作区提供。
- **[P2] 用户提供 PDF。**Li 等，*CancerVerse: A Fully Open Longitudinal and Multimodal Dataset for Multicancer Screening*。第 4 页：轨迹与阴性定义；第 7 页：病灶级 FROC。PDF 不随包重新分发。
- **[S1] R2-Seg 官方代码入口。**`https://github.com/Eurekashen/R2Seg`；页面已核查，尚未运行。
- **[S2] R2-Seg orchestration。**`https://raw.githubusercontent.com/Eurekashen/R2Seg/main/tta_pipeline/pipeline.py`；已核查，运行时锁定提交。
- **[S3] R2-Seg statistical test。**`https://raw.githubusercontent.com/Eurekashen/R2Seg/main/tta_pipeline/statistical_test.py`；已核查，包括当前候选排除。
- **[S4] R2-Seg configuration。**`https://raw.githubusercontent.com/Eurekashen/R2Seg/main/tta_pipeline/config.py`；已核查，CLI 的最终覆盖仍须导出。
- **[S5] BiomedParse 官方仓库。**`https://github.com/microsoft/BiomedParse`；当前页面包含 v2，不能替代 v1 审核。
- **[S6] BiomedParse 官方模型文件页。**`https://huggingface.co/microsoft/BiomedParse/tree/main`；页面列出 v1/v2，权重访问需要按官方条件处理。
- **[S7] FedBCa 原始论文。**`https://www.nature.com/articles/s41597-024-03971-0`；正文已核查，部分后续页面请求失败。
- **[S8] FedBCa 版本记录入口。**`https://zenodo.org/records/10409145`；旧版本记录可读且提示更新版本。确认后固定选用版本；未下载原始包。
- **[S9] Prostate158 官方代码/数据说明。**`https://github.com/kbressem/prostate158`；已核查。
- **[S10] Prostate158 数据记录候选。**训练 `https://zenodo.org/records/6481141`，测试 `https://zenodo.org/records/6592345`；训练记录可由检索确认，直接请求限流；测试记录本次超时，必须再次核验，不能宣称文件已可用。
- **[S11] CC-Tumor-Heterogeneity 官方集合。**`https://www.cancerimagingarchive.net/collection/cc-tumor-heterogeneity/`；官方搜索索引可见，正文访问失败；逐时间点标签与下载流程待审核。
- **[S12] CancerVerse 官方数据卡。**`https://huggingface.co/datasets/BodyMaps/CancerVerse`；数据卡可读，版本与实际文件需在选择性下载时锁定。

---

## 19. 第一轮完成后的决策

先回答两件事：**更合适的当前参考是否有帮助，持续历史是否带来超出当前参考的额外价值。**有证据后，再扩展到新部位与纵向场景。

不要以实现模块数量作为研究进度。阶段性最有价值的交付是：一个正确、可复现、信息权限清楚的小实验，以及它对方法假设支持或不支持的真实证据。
