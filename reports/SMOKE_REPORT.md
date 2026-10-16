# Real smoke status — 2026-10-16

Run: `p1_p3_v1`, assigned GPU, FP32, batch size one, fixed `bladder tumor` query,
locked upstream bladder plan, external LLM disabled. Every native slice is scheduled;
no GT slice filtering is used. The frozen selection contains three distinct released
subject-image keys from three centers. Patient-linkage limits are in DATA_AUDIT.

The initial fixed middle-slice end-to-end diagnostic passed. At the last status
snapshot, two complete checks had finished and no failure had been recorded. The
third check and subsequent ten-input parity gate were still pending. Therefore
**P2 is not yet accepted**. The process runs independently of the SSH/session.

Private outputs preserve per-slice anchor/ROI data, fused and intermediate probability
maps, all raw candidates, small-region deletion, statistical skip/BH outcomes, final
masks and timings. Native-grid output is written after all slices finish. Empty
predictions remain distinct from inference exceptions. No full-check Dice or lesion
recall is reported before independent offline evaluation.
