# Parity status — 2026-10-16

Not yet completed. Ten real inputs are fixed by four evenly spaced native slice
indices per smoke check, taking the first ten in frozen check order; neither GT nor
model output selects them. Identical seed and FP32 settings are used for each paired
native/observed call. Required checks are exact binary masks, zero maximum probability
difference, retained statistics and all raw candidate masks. A failure aborts P3;
no tolerance relaxation is allowed.

Post-warmup network parameters and buffers are compared exactly with a CPU snapshot.
Six synthetic tests passed, covering geometry, input-field isolation, sparse table
parsing, invalid-reference fallback and one-to-one lesion matching. They are not
real-input parity evidence. History/memory/probe tests are outside this run.
