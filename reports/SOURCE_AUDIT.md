# 准备阶段来源审核（2026-10-16）

本次仅环境与资源准备；没有真实推理或性能结果。原包中的 P0–P5 是研究规格。

| 来源 | 实际核验 | 限制 |
|---|---|---|
| R2Seg | 经本机代理取得源码，commit `48a0a14ce1f0da6a51cdf26bcc821d64b176c0c5` | 尚未加载模型；源码放在忽略的 third_party/R2Seg |
| 上游 environment.yml | Python 3.9.19、PyTorch 2.4.0、CUDA 12.4 | 用户明确允许适配 pro5000；采用独立的 Python 3.12 / PyTorch 2.7.1 cu128 环境 |
| 上游依赖文件 | environment.yml 的 NumPy 为 1.23.1，requirements 为 1.26.4；Detectron2 Git 依赖未固定 revision | 不将其当成完全解析的可复现锁；本机需求列表及安装后 freeze 单独保留 |
| Detectron2 fork | GitHub codeload 归档的 PAX comment 给出 commit `42121d75e10d9f858f3a91b6a39f5722c02868f0` | Git/API 两种访问失败，归档经同一代理取得；CPU 扩展编译成功；Pillow LINEAR→BILINEAR 别名兼容补丁单列 |
| FedBCa | 通过旧记录 latest 关系解析到 [13622759](https://zenodo.org/records/13622759)，CC-BY-4.0，FedBCa.rar 1,028,171,551 bytes | 原包 10409145 已非最新；患者映射、几何、标注完整性均未审核 |
| BiomedParse v1 | [官方模型元数据](https://huggingface.co/microsoft/BiomedParse) revision `e473e5b2b1a3f44649734afd3dc7cf1770aaa9e2`，1,803,167,371 bytes，gated=auto，CC-BY-NC-SA-4.0 | 已复用用户提供的 checkpoint/config/target_dist 并同步服务器；未代用户接受条款；未加载；公开摘要只是期望值，未验证本地内容的 revision |

上游源码审阅还发现：`run_with_plan` 可用；模型加载内部采用 `strict=False`，
CUDA 不可用时包装器会提示回退 CPU。这些行为不能直接满足本项目严格加载/禁止静默回退要求，
后续模型接入需要独立校验，当前没有修改 native 源码。

`sources.lock.json` 只完成部分来源解析，明确 `inference_ready=false`。
不把服务器基础运算测试当成 BiomedParse v1 推理，也不填造数据审核结果。

论文 PDF 不在压缩包中，本次没有声称核验论文内容；S2/S3/CancerVerse 未下载。
