"""Offline evaluator: only this process reads labels and prediction outputs together."""
import collections
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage


def component_matches(prediction,truth,threshold=.1,scores=None):
    p,npred=ndimage.label(prediction,structure=np.ones((3,3,3)))
    g,ngt=ndimage.label(truth,structure=np.ones((3,3,3)))
    matched=set()
    order=sorted(range(1,npred+1), key=lambda i: (-float(np.mean(scores[p==i])) if scores is not None else 0.,i))
    for pi in order:
        pm=p==pi;choices=[]
        for gi in np.unique(g[pm]):
            if gi==0 or gi in matched:continue
            gm=g==gi;iou=np.count_nonzero(pm&gm)/np.count_nonzero(pm|gm)
            if iou>=threshold:choices.append((iou,int(gi)))
        if choices:matched.add(max(choices)[1])
    return len(matched),int(ngt),int(npred),matched,g


def main():
    root=Path(os.environ['COOD_ROOT']);out=root/'outputs/p1_p3_v1'
    status=json.loads((out/'status.json').read_text())
    assert status['stage']=='P3_INFERENCE_COMPLETE','Inference not complete'
    records=[json.loads(x) for x in (root/'manifests_local/evaluation_dev.jsonl').read_text().splitlines()]
    methods=['B0_R2_NATIVE','B1_all_candidates','B1_physical_margin','B1_compartment','C0_CONFIDENCE_ONLY','C1_CURRENT_CALIBRATION']
    rows=[];failures=[];reference_reasons=collections.Counter();stage_counts=collections.Counter();slices=0;fallbacks=0
    for record in records:
        folder=out/record['study_uid']
        try:
            truth=np.asarray(nib.load(record['label_path']).dataobj)>0
            if not truth.any():raise ValueError('Unexpected empty positive annotation')
            with np.load(folder/'volume.npz') as cached:
                score_volume=cached['probability'].transpose(2,1,0)
            with np.load(folder/'research_candidates.npz') as cached:
                research_labels=cached['labels'].transpose(2,1,0)
            candidate_records=json.loads((folder/'research_candidates.json').read_text())
            for method in methods:
                pred_image=nib.load(folder/f'{method}.nii.gz');pred=np.asarray(pred_image.dataobj)>0
                gt_image=nib.load(record['label_path'])
                assert pred.shape==truth.shape and np.allclose(pred_image.affine,gt_image.affine)
                dice=2*np.count_nonzero(pred&truth)/(np.count_nonzero(pred)+np.count_nonzero(truth))
                scores=score_volume.copy()
                if method.startswith(('C0','C1')):
                    for c in candidate_records:
                        scores[research_labels==c['candidate']]=c['base_score' if method.startswith('C0') else 'calibrated_score']
                tp,ngt,npred,_,_=component_matches(pred,truth,scores=scores)
                rows.append(dict(study_uid=record['study_uid'],method=method,dice=float(dice),annotated_lesions=ngt,matched_lesions=tp,predicted_components=npred,unmatched_predictions=npred-tp,empty=not bool(pred.any()),recall_iou_005=component_matches(pred,truth,.05,scores)[0]/ngt,recall_iou_025=component_matches(pred,truth,.25,scores)[0]/ngt))
            with np.load(folder/'volume.npz') as cached:prob=cached['probability']
            raw=prob>=.4;small=np.zeros(raw.shape,bool);roi=np.zeros(raw.shape,bool)
            scan=json.loads((folder/'scan.json').read_text());slices+=len(scan['trace'])
            for z,trace in enumerate(scan['trace']):
                fallbacks+=int(trace['anchor_fallback'])
                for box in trace['rois']:roi[z,box['top']:box['bottom'],box['left']:box['right']]=True
                labs,n=ndimage.label(raw[z])
                for i in range(1,n+1):
                    if np.count_nonzero(labs==i)>=50:small[z]|=labs==i
            truthz=truth.transpose(2,1,0);gt,n=ndimage.label(truthz,structure=np.ones((3,3,3)))
            final=np.asarray(nib.load(folder/'B0_R2_NATIVE.nii.gz').dataobj).transpose(2,1,0)>0
            for gi in range(1,n+1):
                lesion=gt==gi;stage_counts['annotated_lesions']+=1
                if not (roi&lesion).any():stage_counts['no_ROI_overlap']+=1
                if not (raw&lesion).any():stage_counts['absent_from_probability_candidates']+=1
                elif not (small&lesion).any():stage_counts['lost_at_50_pixel_filter']+=1
                elif not (final&lesion).any():stage_counts['lost_at_statistics']+=1
                else:stage_counts['final_has_overlap']+=1
            candidates=json.loads((folder/'research_candidates.json').read_text())
            for c in candidates:reference_reasons[c['invalid_reason'] or 'valid']+=1
        except Exception as exc:failures.append(dict(study_uid=record['study_uid'],error=repr(exc)))
    aggregate={}
    for method in methods:
        subset=[r for r in rows if r['method']==method]
        aggregate[method]=dict(scans=len(subset),mean_positive_annotation_dice=float(np.mean([r['dice'] for r in subset])) if subset else None,median_positive_annotation_dice=float(np.median([r['dice'] for r in subset])) if subset else None,annotated_lesions=sum(r['annotated_lesions'] for r in subset),matched_lesions=sum(r['matched_lesions'] for r in subset),empty_scans=sum(r['empty'] for r in subset),unmatched_predictions=sum(r['unmatched_predictions'] for r in subset))
    result=dict(attempted_scans=len(records),failed_scans=len(failures),methods=aggregate,loss_stages=dict(stage_counts),local_reference=dict(reference_reasons),slices=slices,anchor_fallback_slices=fallbacks,FROC='not_identifiable_from_partial_annotations',FP_per_scan='not_identifiable_from_partial_annotations',screening_specificity='not_applicable_no_verified_negatives')
    (out/'evaluation_private.json').write_text(json.dumps({'cases':rows,'failures':failures},indent=2))
    (out/'evaluation_summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
