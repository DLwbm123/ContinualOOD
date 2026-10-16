"""Freeze a table-key grouped split and physically separate inference/evaluation files."""
import collections
import hashlib
import json
import os
from pathlib import Path
import random
import shutil

import nibabel as nib
import numpy as np


def write_jsonl(path, records):
    path.write_text(''.join(json.dumps(x)+'\n' for x in records))


def main():
    root = Path(os.environ['COOD_ROOT'])
    audit = json.loads((root/'private/data_audit_private.json').read_text())
    groups = collections.defaultdict(list)
    for study in audit['studies']:
        if not study['errors']:
            groups[study['center']].append(study)
    centers = sorted(groups, key=lambda c: (-len(groups[c]), c))[:3]
    assert all(len(groups[c]) >= 20 for c in centers)
    out = root/'manifests_local'; out.mkdir(exist_ok=True)
    data = root/'data/prepared'; data.mkdir(exist_ok=True)
    runtime, evaluation, registry, mapping = [], [], [], []
    rng = random.Random(42)
    for center in centers:
        pool = sorted(groups[center], key=lambda s: s['image_name'])
        rng.shuffle(pool)
        for i, study in enumerate(pool[:20]):
            uid = 's'+hashlib.sha256((center+'/'+study['image_name']).encode()).hexdigest()[:20]
            split = 'dev' if i < 4 else 'stream' if i < 14 else 'probe'
            path = data/uid; path.mkdir(exist_ok=True)
            # Links expose only opaque paths to inference, without copying the full dataset.
            image_path = path/'image.nii.gz'
            if not image_path.exists():
                os.link(study['image'], image_path)
            im = nib.load(image_path)
            union = np.zeros(im.shape, dtype=np.uint8)
            for mask in study['masks']:
                union |= np.asarray(nib.load(mask['path']).dataobj) > 0
            label_path = path/'label.nii.gz'
            nib.save(nib.Nifti1Image(union, im.affine, im.header), label_path)
            geometry = path/'geometry.json'
            geometry.write_text(json.dumps({k: study[k] for k in ['shape','affine','spacing','orientation','qform_code','sform_code']}))
            runtime.append(dict(study_uid=uid, patient_key=uid, image_path=str(image_path), geometry_path=str(geometry), modality='MRI', sequence='T2w', working_view='native_audited', past_study_uids=[]))
            evaluation.append(dict(study_uid=uid,patient_key=uid,label_path=str(label_path),annotation_completeness='partial',evaluation_target='bladder tumor',negative_verified=False,verification_source='Released table pairs merged on exact image key and matching native geometry; exhaustive scan annotation not independently confirmed'))
            registry.append(dict(study_uid=uid,patient_key=uid,center=center,split=split,index_in_center=i))
            mapping.append(dict(study_uid=uid,center=center,image=study['image'],masks=study['masks']))
    assert len({x['patient_key'] for x in registry}) == 60
    for split in ['dev','stream','probe']:
        ids={r['study_uid'] for r in registry if r['split']==split}
        write_jsonl(out/f'runtime_{split}.jsonl',[r for r in runtime if r['study_uid'] in ids])
        write_jsonl(out/f'evaluation_{split}.jsonl',[r for r in evaluation if r['study_uid'] in ids])
    smoke = [next(r['study_uid'] for r in registry if r['center']==c and r['split']=='dev') for c in centers]
    (out/'smoke_ids.json').write_text(json.dumps(smoke))
    write_jsonl(out/'split_registry.jsonl',registry)
    write_jsonl(root/'private/patient_mapping.jsonl',mapping)
    stream = {c:[r for r in registry if r['center']==c and r['split']=='stream'] for c in centers}
    ordered=stream[centers[0]][:6]+stream[centers[1]]+stream[centers[2]]+stream[centers[0]][6:]
    write_jsonl(out/'stream_schedule.jsonl',[dict(index=i,study_uid=r['study_uid']) for i,r in enumerate(ordered)])
    hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json*')}
    (root/'private/split_identity.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps(dict(selected_centers=centers,dev=12,stream=30,probe=18,smoke=3,annotation='partial_conservative',patient_unit='released_center_image_subject_key')))


if __name__ == '__main__':
    main()
