# Current limits — 2026-10-16

- No execution blocker remains for this bounded P3 run: complete smoke, parity,
  network-state checks, 12 dev inferences and independent evaluation finished.
  The scientific limitations below remain unresolved.
- The released 221 subject-image keys differ from the paper's 228 patients.
  Workbooks establish exact image/mask grouping; they do not provide an independent
  cross-center identity registry or longitudinal identifiers. No duplicate arrays
  were found, but differently resampled duplicates cannot be ruled out.
- Official train/test CSV files referenced by the authors are not distributed in
  the inspected archive/repository. The frozen dev/stream/probe registry is a new
  diagnostic split, not a reproduction of the official split.
- Fourteen image groups with affine mismatches are excluded without modification.
- Exhaustive scan-wide annotations are unconfirmed. Full FROC, true FP/scan and
  screening specificity are therefore unavailable; use annotated-lesion outcomes.
- The selected model configuration passed a real forward using the existing
  environment. Optional deformable-attention CUDA operators remain unbuilt and
  unused; this is not evidence about other architectures.

Resolved: auxiliary asset availability, strict checkpoint coverage, full real GPU
smoke, the recorded parity checks and independent dev evaluation. Original network/preparation failures remain in private logs; no CPU
fallback, model retraining or broad dependency upgrade was used.

C1 had no valid current-reference correction in 297 proposals. This is a negative
feasibility result under the frozen defaults, not evidence that valid reference
calibration cannot help. No further experiment is authorized past the P3 stop.
