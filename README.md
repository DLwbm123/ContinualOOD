# Continual OOD 肿瘤分割 · Codex 启动包

公开仓库：https://github.com/DLwbm123/ContinualOOD 。当前阶段为环境准备，尚无真实实验结果。
准备状态见 `reports/PREPARATION.md`，限制见 `reports/BLOCKERS.md`。
后续每次实验完成后，代码、去标识结果和报告均需推送到本仓库，保留失败及负结果。

部署路径和激活脚本仅本地保存。检查脚本 `scripts/doctor.py` 与 `scripts/hardware_check.py`
读取操作员配置的 `COOD_ROOT`、`COOD_STORAGE_ROOT` 和其他数据/缓存环境变量；
完整依赖版本见 `configs/environment-pro5000.freeze.txt`。运行入口采用 `python - < script.py`。
原始机器检查输出仅本地保存，公开摘要见 `reports/ENVIRONMENT_CHECKS.json`。

以下为原始启动包说明：

这是一份实施交接包，不是已实现的研究仓库。它不包含模型权重、医学影像、论文 PDF、训练程序或实验成绩。

**入口：**先读 `CONTINUAL_OOD_STARTUP.md`。向 Codex 发送 `CODEX_START_PROMPT.md` 的正文即可启动。

| 文件 | 用途 |
|---|---|
| `CONTINUAL_OOD_STARTUP.md` | 完整任务定义、数据审核、方法细节、评价、接口、里程碑与停止条件 |
| `AGENTS.md` | Codex 的工作区执行约束，接入已有仓库时合并而非覆盖 |
| `CODEX_START_PROMPT.md` | 可直接粘贴给 Codex 的任务指令 |
| `configs/pilot.yaml` | FedBCa 首轮试验默认配置；需要 Codex 实现对应解析器/CLI |
| `configs/source_registry.yaml` | 官方来源与本次核查状态；运行前解析并锁定版本 |
| `configs/extensions.yaml` | S2/S3 与 CancerVerse 的后续扩展，默认禁用 |
| `schemas/runtime_study.schema.json` | 运行清单字段约束，排除当前标签/中心/阶段信息 |
| `schemas/evaluation_record.schema.json` | 独立评价清单结构与标注完备性约束 |
| `templates/PILOT_REPORT_TEMPLATE.md` | 首轮报告模板，无预填性能数值 |
| `templates/BLOCKERS_TEMPLATE.md` | 外部权限、数据和环境阻塞记录模板 |
| `docs/SOURCES.md` | 来源编号、用途与未验证事项 |
| `.gitignore` | 防止把医学数据、权重、病例级结果与密钥提交到 Git |
| `VALIDATION_REPORT.txt` | 本交接包文本、YAML、JSON schema 与 ZIP 的静态检查结果 |

主线采用冻结 BiomedParse v1，从小型 MRI 数据验证当前参考和持续参考，之后再扩展新器官、纵向随访与 CancerVerse 子集。

**重要：**本包中的 `cood ...` 是待实现 CLI 规范，不是安装后立即存在的命令。来源页面可访问不代表数据已下载、权限已取得或标注已审核。默认数值是研究起点，不是已验证最优参数。
