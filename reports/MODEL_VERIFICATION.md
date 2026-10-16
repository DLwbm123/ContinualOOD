# Model verification — 2026-10-16

Real BiomedParse v1 loading succeeded on the assigned GPU, FP32, with no CPU fallback.
The existing checkpoint was hashed once: SHA-256
`66716517a59e5b8060dc87732a4d65fea1f699ecec3f6a8440749f3ea2b917dc`, matching the publisher
metadata at revision `e473e5b2b1a3f44649734afd3dc7cf1770aaa9e2`.
The user-supplied config successfully builds the matching architecture. This does
not independently establish the companion files' original download revision.

All 1,131 architecture state entries (450,663,426 elements) match checkpoint keys
and shapes. Missing keys: zero. Shape mismatches: zero. One extra checkpoint entry,
`criterion.empty_weight`, belongs to the training criterion, absent from this demo
inference architecture. It is explicitly excluded; remaining keys load strictly.
Parameters are frozen and the model is in evaluation mode. Peak allocated GPU
memory during load/text initialization was 2,010,257,408 bytes.

Previously absent public auxiliary assets were downloaded within the model budget:
BiomedBERT at `e1354b7a3a09615f6aba48dfad4b7a613eef7062`, and CLIP tokenizer files at
`3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268`. Offline cache refs pin these exact revisions.
The server's first network attempt failed; transfer then succeeded through the
existing local proxy tunnel. No access terms were accepted on the user's behalf.

One fixed real middle slice passed the full anchor/ROI/target/statistical path,
including actual CUDA inputs and outputs. Model calls took about 3.82 seconds and
statistics 0.26 seconds in that diagnostic. It is not a full-scan performance result.
The CPU-built Detectron2 extension suffices for this observed locked configuration;
unbuilt deformable attention remains unused. No environment rebuild was needed.

Complete-scan smoke, ten-input parity and post-warmup state invariance remain separate
P2 acceptance checks. One successful slice and strict loading do not imply P2 passed.
