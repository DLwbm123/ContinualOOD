# Current limits — 2026-10-16

- Full-scan smoke and parity are not yet accepted. P3 must not be called complete
  until these gates and the independent evaluator finish.
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

Resolved: auxiliary asset availability, strict checkpoint coverage and initial real
GPU forward. Original network/preparation failures remain in private logs; no CPU
fallback, model retraining or broad dependency upgrade was used.
