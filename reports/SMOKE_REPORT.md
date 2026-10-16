# P2 real smoke — completed 2026-10-16

Run `p1_p3_v1` completed three distinct released subject-image checks spanning three
centers: 20, 28 and 25 native slices, **73/73 slices processed**, no exceptions.
These checks are included in the 12-check dev evaluation, not additional patients.
The checks were selected before inference without labels or lesion-slice selection.
Patient-identity limits remain as documented in DATA_AUDIT.

Execution used the assigned GPU, FP32, batch one, frozen BiomedParse v1, fixed
`bladder tumor` query and the locked upstream bladder plan, with no external LLM.
Native ROI padding was 30 mm (upstream YAML override), TTA aggregation max, three
scale jitters, candidate threshold 0.4, minimum 50 pixels, MMD permutation testing,
BH alpha 0.05, and **mitigation disabled**. The plan's descriptive 10 mm prose does
not override the actual numeric ROI configuration. Actual model/config paths and
source identities are recorded in the private provenance, distinct from upstream
configuration defaults.

Full native-grid predictions, anchor/ROI maps, fused/intermediate probabilities,
all candidates, small-region removal and statistical skip/BH outcomes are private.
Native shape/affine were checked by the independent evaluator on all 12 dev outputs.
A synthetic test additionally verifies XYZ↔ZYX roundtrip and rejects label fields
at the runtime interface. Loading requires CUDA and exceptions remain visible;
no CPU inference fallback was used. Deliberate hardware-failure injection was not run.

Across the 12 dev checks, 289 slices were processed with no inference failures.
Recorded native scan wall time totals 1,362.85 s, including 1,182.87 s in model calls
and 132.47 s in statistics. The remaining 47.50 s includes I/O and orchestration;
I/O was not separately instrumented. These sums exclude warmup, parity and B1/C1
postprocessing and are not total campaign runtime. Peak PyTorch allocated memory
was 2,785,821,184 bytes (2.59 GiB), not total process/device memory.

P2 engineering gates passed for these inputs. This does not establish clinical
accuracy or independent patient generalization. Ten-input parity and unchanged
network-state evidence are detailed in PARITY_REPORT.
