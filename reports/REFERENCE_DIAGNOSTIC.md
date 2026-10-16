# P3 current-reference diagnostic — completed 2026-10-16

The run completed all **12 dev checks / 289 slices**, followed by an independent
label-reading evaluator. There were zero inference/evaluation failures. The merged
annotations contain 14 three-dimensionally connected lesions. Results concern
released subject keys and annotated lesions; clinical patient linkage and exhaustive
annotation remain unconfirmed. All results below are development diagnostics.

| Method | Mean positive annotation Dice | Median Dice | Lesion matches, IoU ≥0.1 | Empty checks | Unmatched predicted components |
|---|---:|---:|---:|---:|---:|
| B0 native | 0.04417 | 0.01642 | 4/14 | 0/12 | 242 |
| B1 exclude all candidates | 0.04566 | 0.01642 | 4/14 | 0/12 | 242 |
| B1 +3 mm margin | 0.04407 | 0.01642 | 4/14 | 0/12 | 243 |
| B1 +shell/core compartment | 0.04417 | 0.01642 | 4/14 | 0/12 | 242 |
| C0 confidence | 0.06290 | 0.01528 | 5/14 | 0/12 | 176 |
| C1 current calibration | 0.06290 | 0.01528 | 5/14 | 0/12 | 176 |

Unmatched counts are **not verified false positives**. Partial/unconfirmed annotation
precludes definitive FP/scan, FROC and patient screening specificity. Candidate
matching is score-ordered, one-to-one, maximum IoU; GT components use 26-connectivity.
At IoU 0.05/0.25, B0 matches 6/1 lesions; B1 all-exclusion and compartment match 6/1;
B1 margin matches 6/0; C0/C1 match 5/2. This sensitivity to matching threshold further
limits interpretation of small differences.

## Where are lesions lost?

All 14 annotated lesions overlap a planned ROI somewhere; no slice uses the
full-frame anchor fallback. This is not proof of accurate bladder localization.
Native combines ROI and full-image predictions, so ROI overlap is a separate
coverage diagnostic rather than a strict sequential rejection stage.

At a permissive any-voxel overlap criterion, one lesion is absent from the ≥0.4
probability candidates, none is newly eliminated by the 50-pixel rule, one is lost
at statistical filtering, and 12 still overlap the final native mask. Mitigation is
disabled, so no later mitigation losses occur. These overlap counts must not be
confused with accepted lesion matches: only 5/14 lesions match the fixed raw 3D
candidate set at IoU ≥0.1 and only 4/14 match native output. At least one lesion is
completely unavailable to reference rescoring; nine remain unmatched under the frozen score-ordered matcher (this count
alone does not prove that every alternative assignment is impossible). Low shape overlap/large connected predictions are therefore a major bottleneck.
Reference rescoring cannot repair a missing or poorly shaped fixed proposal.

## Does changing current references help?

B1 all-candidate exclusion gives a small mean Dice increase of 0.001493: four checks
improve and eight are unchanged, with no recall gain. Removing the most favorable
check reduces the mean difference to 0.000466, indicating concentration in one check.
The paired 1,000-resample, seed-42 bootstrap percentile interval is approximately
[0.000004, 0.004044], conditional on these released subject units; it is not a
confirmatory significance claim. The margin variant worsens one check and leaves
11 unchanged (mean −0.000103). Compartment leaves all 12 unchanged. No method creates
an empty whole-check prediction, so these results are not an improvement obtained
by rejecting every check.

The B1 slice-wide fallback to native occurs on 153/289 (52.9%), 227/289 (78.5%) and
245/289 (84.8%) slices for all-exclusion, margin and compartment respectively. These
are conservative implementation fallbacks when a candidate lacks sufficient valid
reference, not evidence that the reference test itself succeeded. No numeric
thresholds were tuned after observing outcomes.

C1 obtains **zero valid calibrations among 297 candidates**:
- 94 exceed the predefined 16 mm physical-size bins;
- 127 cannot form at least four disjoint null patches;
- 76 contain fewer than 16 candidate samples.

Every C1 correction is therefore zero. C0/C1 masks are exactly equal in all 12
checks. This establishes reference unavailability under the frozen defaults, not
that a valid current reference has no value. The larger C0/C1 Dice and recall than
native cannot be attributed to references: C0 uses different fixed 3D candidates
and confidence scoring, so only C1 versus C0 isolates calibration.

## Next-step decision and limits

Prioritize candidate quality/localization and diagnosing reference availability
before adding historical memory. Current evidence does not justify larger memory,
new gating or claims of continual benefit. No oracle clean-reference diagnostic was
run, so its potential remains unknown. No parameter search, stream/probe evaluation,
historical B2/B3/B4, new organ or P4/P5 execution occurred.

Machine-readable aggregate results are in `P3_RESULTS.json`; case-level predictions,
statistical traces and evaluator records remain private. The 221-versus-228 cohort
count discrepancy, source-key identity assumption, unavailable official split,
affine exclusions and incomplete annotation limits remain in DATA_AUDIT/BLOCKERS.
P3 is finished with a weak B1 effect and an unavailable C1 correction, not a successful
clinical segmentation result or a generalization claim.
