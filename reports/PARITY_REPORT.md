# P2 parity — completed 2026-10-16

Ten fixed real slice inputs were evaluated twice with the same plan, seed and FP32
settings through the locked native and observed paths. Slice indices came from
four evenly spaced native indices per smoke check, taking the first ten in frozen
check order, without consulting labels or outputs.

All ten pairs had:
- maximum absolute fused probability difference **0.0**;
- exactly equal final binary masks;
- equal retained candidate statistics and BH results;
- exactly equal sets/masks of all raw candidates.

Deleted-candidate statistics were saved in the observed path; the unobserved
PipelineOutput exposes only retained candidates, so direct paired statistic
comparison covers retained candidates. Both paths invoke the unchanged upstream
statistical evaluator. No threshold relaxation or algorithm patch was used.

After fixed-prompt warmup, all 1,131 network state entries were copied and compared
exactly after P2 and again after P3. Both comparisons found zero changes. Model
parameters were frozen and evaluation mode remained enabled. Six synthetic tests
also passed for geometry, schema separation, sparse tables, reference fallback and
one-to-one lesion matching. No memory/probe tests or hardware-failure injection
were claimed.
