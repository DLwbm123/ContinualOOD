"""Reproduce paired development diagnostics from private evaluator outputs."""
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np
from evaluate_p3 import component_matches


def main():
    root=Path(os.environ['COOD_ROOT']);out=root/'outputs/p1_p3_v1'
    rows=json.loads((out/'evaluation_private.json').read_text())['cases']
    by={(x['study_uid'],x['method']):x for x in rows}
    pairs={}
    for a,b in [('B0_R2_NATIVE','B1_all_candidates'),('B0_R2_NATIVE','B1_physical_margin'),('B0_R2_NATIVE','B1_compartment'),('C0_CONFIDENCE_ONLY','C1_CURRENT_CALIBRATION')]:
        differences=np.array([x['dice']-by[(x['study_uid'],a)]['dice'] for x in rows if x['method']==b])
        if len(differences)<2:raise ValueError('Insufficient paired checks')
        rng=np.random.default_rng(42)
        bootstrap=np.mean(rng.choice(differences,(1000,len(differences)),replace=True),axis=1)
        pairs[b]=dict(mean_dice_delta=float(differences.mean()),improved=int((differences>1e-12).sum()),worsened=int((differences< -1e-12).sum()),unchanged=int((abs(differences)<=1e-12).sum()),leave_one_out_delta_range=[float((differences.sum()-x)/(len(differences)-1)) for x in [differences.max(),differences.min()]],bootstrap_percentile_95=np.percentile(bootstrap,[2.5,97.5]).tolist())
    sensitivity={}
    for method in sorted({x['method'] for x in rows}):
        subset=[x for x in rows if x['method']==method]
        sensitivity[method]={k:sum(x[k]*x['annotated_lesions'] for x in subset)/sum(x['annotated_lesions'] for x in subset) for k in ['recall_iou_005','recall_iou_025']}
    matches=total=equal=0
    for line in (root/'manifests_local/evaluation_dev.jsonl').read_text().splitlines():
        record=json.loads(line);folder=out/record['study_uid']
        truth=np.asarray(nib.load(record['label_path']).dataobj)>0
        with np.load(folder/'volume.npz') as cache:probability=cache['probability'].transpose(2,1,0)
        tp,n,*_=component_matches(probability>=.4,truth,scores=probability)
        matches+=tp;total+=n
        equal+=np.array_equal(np.asarray(nib.load(folder/'C0_CONFIDENCE_ONLY.nii.gz').dataobj),np.asarray(nib.load(folder/'C1_CURRENT_CALIBRATION.nii.gz').dataobj))
    summary=dict(paired=pairs,sensitivity_analysis=sensitivity,fixed_candidate_iou01_matches=matches,annotated_lesions=total,C0_C1_exact_mask_equal_scans=equal)
    (out/'additional_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
