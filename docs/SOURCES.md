# 来源与待核验事项


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


本文件只记录本次查阅支持的内容。下游实现必须更新 source lock，但不能修改本记录来伪装成已经在编写启动包时验证的事实。
