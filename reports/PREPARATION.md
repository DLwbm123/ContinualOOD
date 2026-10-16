# 环境准备报告（2026-10-16）

项目处于环境准备阶段，尚未执行 P1–P5 实验。部署和所有大文件位于服务器 data 盘；
具体路径、原始日志与准备历史仅本地保存。

已安装 Python 3.12、PyTorch 2.7.1+cu128、torchvision 0.22.1+cu128，适配 Blackwell。
已通过存储写入读回、配置/schema 检查、GPU FP32 矩阵乘法/卷积/torchvision NMS、
Detectron2 CPU 扩展、BiomedParse v1 后端导入和 pip check。
公开检查摘要见 ENVIRONMENT_CHECKS.json，完整依赖版本与源码 revision/补丁随仓库保存。
Detectron2 的 CPU 扩展不提供其自有 CUDA 算子；默认 v1 FPN 路径未启用可选 deformable encoder。

用户提供的三个模型文件已传到服务器：checkpoint 1,803,167,371 bytes，
config.yaml 4,537 bytes，target_dist.json 11,739 bytes。大小和小型配置可读性已检查，
未额外计算摘要、未验证逐字节一致，未加载 checkpoint。

FedBCa 锁定记录 13622759，大小 1,028,171,551 bytes。准备阶段的最后一次记录为后台下载中，
约完成 35.4%；这是历史快照，不代表当前下载状态。未做解压、患者划分或病例处理。

所有 GPU 检查均为合成环境检查。真实病例处理数为 0；没有性能指标或 pilot 结论。
未验证辅助 tokenizer/BiomedBERT 资产和完整模型前向。已保留依赖安装及测试中的失败记录，
问题和限制见 BLOCKERS.md。

公开交付范围：启动规格、配置、检查脚本、依赖版本、兼容补丁及准备报告。
数据、权重、第三方完整源码、私人部署配置和原始运行日志不发布。
