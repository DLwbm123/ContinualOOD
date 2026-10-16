# P1 data audit — 2026-10-16

The locked Zenodo record is [13622759](https://zenodo.org/records/13622759).
The existing 1,028,171,551-byte RAR was reused. libarchive extraction completed with
exit status 0 after rejecting absolute/traversal member names. The archive contains
496 NIfTI files and four workbooks; expanded member size is 1,032,973,710 bytes.
No redundant archive digest or second full extraction was performed.

| Released center | Image volumes | Tumor masks | Geometry-compatible image groups |
|---|---:|---:|---:|
| 1 | 119 | 160 | 116 |
| 2 | 47 | 48 | 42 |
| 3 | 24 | 32 | 19 |
| 4 | 31 | 35 | 30 |
| Total | 221 | 275 | 207 |

All 275 workbook image/mask pairs resolve to existing files. All masks are binary
and nonempty; none is a verified negative scan. Multiple masks referring to the
same workbook image key are grouped as one image/subject unit, not independent
patients. Merging is allowed only within that exact image key and compatible
native geometry. The current release has 221 image keys, unlike the paper's 228
patients; the missing seven cannot be reconstructed from this package.

The [data paper](https://www.nature.com/articles/s41597-024-03971-0) describes
subject images and the image-to-annotation workbook mapping. This is the grouping
provenance; no longitudinal identifiers or independent cross-center patient linkage
are supplied. The split is release-key grouped and must not be represented as an
externally validated patient identity registry. Same-image multi-lesion copies do
not cross splits. A same-grid duplicate screen (shape and 256 fixed voxel samples, followed by full
array comparison on signature collisions) found zero duplicate pairs across 221
volumes. This does not detect differently resampled scans. Within-image workbook
age/sex fields have no conflicts; no demographic fields enter inference.

Fourteen image groups have sixteen annotation affine mismatches at the fixed
1e-4 comparison tolerance. Shapes agree, but the largest observed corner displacement
is 0.314 mm. These groups are excluded; no affine correction or label resampling is
performed. Native shape, affine, spacing, orientation and qform/sform codes are
recorded privately. Available images have varying in-plane sizes, rather than the
paper's fixed 160×160 annotation-centered training crops. This supports working on
the released field of view; it does not establish that every acquired clinical slice
was released.

A seed-42 frozen release-subject registry uses centers 1, 2 and 4, chosen by eligible quantity,
with 20 image/subject keys each: 12 dev, 30 stream and 18 probe. Three smoke keys are
the first shuffled dev key in each selected center. Selection uses no performance
or lesion-slice information. Runtime and evaluator manifests are separate; runtime
paths are opaque and contain no source-center identifiers. Stream/probe are not run.
The paper mentions official train/test splits, but neither the released package nor
the inspected official repository tree includes the referenced CSVs. Accordingly,
this registry is not a reconstruction of the authors' official split.

Annotation completeness is conservatively `partial`: all released lesions are
merged, but exhaustive scan-wide annotation is not independently established.
Report annotated-lesion recall and positive annotation-mask Dice, not definitive
FP/scan, FROC, or patient screening specificity. All case-level mappings, native
volumes, masks, geometry records and manifests remain private.

Validation: real-volume audit completed; sparse workbook-column parsing, geometry
roundtrip and rejection of a label field at the inference interface passed synthetic
unit checks. P1 establishes release-subject grouping under the publisher's subject-image
convention, not an independent clinical identity verification; the 221-versus-228
cohort discrepancy and unavailable official split remain limitations.
