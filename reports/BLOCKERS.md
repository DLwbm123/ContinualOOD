# 准备阶段限制（2026-10-16）

- **三个模型文件已到位。** 用户随后提供了文稿目录中的 biomedparse_v1.pt、config.yaml、
  target_dist.json，已同步到 data 盘并核对已知大小和小型配置可读性。
  无需为这三个文件再次登录/下载；没有代用户接受任何条款。尚未加载 checkpoint，
  tokenizer/BiomedBERT 等辅助资产也未在本次验证，不把文件存在当作完整模型可运行。
- **真实推理未验证。** 没有权重加载、真实病例 smoke、插桩 parity 或持续实验；
  GPU 合成运算与模块 import 检查只能说明环境检查的具体项目通过。
- **数据审核未开始。** FedBCa 后台下载独立于环境准备；下载完成也不代表已完成患者分组、
  全视野、几何和标注完整性审核。此前前台下载超时，已保留断点继续下载。
- **模型环境边界。** 系统 CUDA toolkit 为 13.2，PyTorch 使用独立 cu128 runtime。
  Detectron2 使用 CPU 扩展构建；所选 v1 配置是 transformer_encoder_fpn。
  可选 MultiScaleDeformableAttention CUDA 扩展未构建，不能用于 deformable encoder 分支。
- **项目实现。** 启动包中的 cood CLI、方法、数据适配器和 P1–P5 测试仍是后续实施任务，
  没有用空壳命令或合成结果冒充完成。
- **GitHub。** 已授权建立公开仓库；本次发布准备材料，不代表实验完成。

已解决的准备问题及日志保留：GitHub Git/API 访问失败后经同一代理的 codeload 取得
Detectron2；旧版 mpi4py-mpich 没有 Python 3.12 分发包，改为 mpi4py＋MPICH；
Python 开发头文件补在 data 盘，不安装系统软件；Pillow 旧别名替换有独立 patch。
环境测试最初错误地调用了 fork 未导出的 `_C.box_iou_rotated`，已改为源码实际注册的
`torch.ops.detectron2.box_iou_rotated` 并通过。旧 Ninja wheel 的标签元数据导致 pip check
报平台不支持，已针对该问题更新依赖版本；原始失败记录保留在 logs。
