# Current-reference diagnostic — awaiting P2 gate

There is no P3 result yet. No claim of reference benefit, harm, or equivalence is made.
The running job enters P3 only if the three complete smoke checks, ten-input parity
and post-warmup state-invariance checks pass. It processes only the frozen dev set
and terminates before P4.

Implemented comparisons:
- B0 native versus B1 excluding all candidates, then adding a 3 mm neighborhood,
  then predicted-organ shell/core matching. Candidate extraction, statistical test,
  BH threshold and disabled mitigation remain native. When a local reference is
  invalid, the whole slice retains its native result; fallback frequency is saved.
- C0 confidence versus C1 current calibration on identical 26-connected 3D proposals
  at threshold 0.4, with the same fused probabilities and no additional model calls.
  Invalid current references give exactly zero score correction.

The independent evaluator is implemented but has not run. It will report annotated
lesions absent from probability candidates, lost at the 50-pixel filter, lost at
statistics, or retained with overlap; ROI coverage is reported separately because
native also merges a full-image prediction. It also reports positive annotation-mask
Dice, one-to-one lesion recall, empty outputs and unmatched prediction counts.
Unmatched counts cannot be interpreted as true FP/scan under unconfirmed annotation
completeness. Full FROC and screening specificity are unavailable.

The requested research questions—dominant loss stage, unrecoverable candidate misses,
B1/B0 and C1/C0 effects, sensitivity/Dice tradeoffs, reference-invalid frequency and
whether history is worth pursuing—remain unanswered until execution and evaluation
finish. No oracle diagnostic or historical method has been run. Small dev diagnostics
will not establish generalization or clinical utility even after completion.
