"""P3 current-reference controls; no memory, labels, or additional model calls."""
import hashlib
import math
import numpy as np
from scipy import ndimage


def local_controls(rgb, probability, anchor, spacing, fallback, config, native_mask, seed):
    from tta_pipeline import statistical_test as st
    from tta_pipeline.postprocessing import extract_candidates, mask_from_candidates
    from native_adapter import seed_all
    candidates=extract_candidates({'bladder tumor':probability},min_pixels=config.min_pixels,threshold=.4)
    union=probability >= .4
    distance=ndimage.distance_transform_edt(~union,sampling=spacing)
    depth=ndimage.distance_transform_edt(anchor.astype(bool),sampling=spacing)
    outputs={};meta={}
    for variant in ['all_candidates','physical_margin','compartment']:
        seed_all(seed)
        refs=[];invalid=None
        for candidate in candidates:
            reference=anchor.astype(bool)&~union
            if variant != 'all_candidates':reference &= distance>3.
            if variant == 'compartment':
                core=bool(np.median(depth[candidate.mask.astype(bool)])>3.)
                reference &= (depth>3.) if core else (depth<=3.)
            if fallback or reference.sum()<config.min_pixels:
                invalid='anchor_fallback' if fallback else 'insufficient_reference'
            refs.append(reference)
        # A failed reference changes no native decisions in this slice.
        if invalid:
            outputs[variant]=native_mask.copy();meta[variant]={'fallback':invalid,'results':[]};continue
        results=[]
        for candidate,reference in zip(candidates,refs):
            result=st.evaluate_candidates(rgb,reference,[candidate],config)
            results.extend(result)
        qvalues=st.benjamini_hochberg([r.p_value for r in results]) if results else []
        for r,q in zip(results,qvalues):r.q_value=q
        outputs[variant]=mask_from_candidates([r.candidate for r in results if r.q_value<=config.alpha],probability.shape,.4)
        meta[variant]={'fallback':None,'results':[dict(label=r.candidate.label,statistic=r.test_statistic,p=r.p_value,q=r.q_value) for r in results]}
    return outputs,meta


def mmd(x,y):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    kernel=lambda a,b:np.exp(-((a[:,None]-b[None,:])**2)/.02)
    return float(kernel(x,x).mean()+kernel(y,y).mean()-2*kernel(x,y).mean())


def research_candidates(volume,probability,anchor,spacing,study_uid):
    labels,count=ndimage.label(probability>=.4,structure=np.ones((3,3,3)))
    distance=ndimage.distance_transform_edt(labels==0,sampling=spacing)
    depth=ndimage.distance_transform_edt(anchor.astype(bool),sampling=spacing)
    reference=anchor.astype(bool)&(distance>3.)
    records=[];c0=np.zeros(labels.shape,np.uint8);c1=c0.copy()
    for index in range(1,count+1):
        mask=labels==index;nvox=int(mask.sum());q=float(np.clip(probability[mask].mean(),1e-4,1-1e-4));base=math.log(q/(1-q))
        diameter=(6*nvox*np.prod(spacing)/math.pi)**(1/3)
        size=next((b for b in [4.,8.,16.] if diameter<=b),None)
        rank=None;reason=None;n=min(256,nvox)
        rng=np.random.default_rng(int.from_bytes(hashlib.sha256(f'42/{study_uid}/{index}'.encode()).digest()[:8],'big'))
        core=bool(np.median(depth[mask])>3.)
        region=reference&((depth>3.) if core else ((depth>0)&(depth<=3.)))
        patches=[]
        if n<16:reason='candidate_under_16_samples'
        elif size is None:reason='candidate_over_16mm'
        elif not region.any():reason='no_compatible_reference'
        else:
            widths=np.maximum(1,np.ceil(size/np.asarray(spacing)).astype(int))
            # Contiguous non-overlapping boxes, selected by seeded spatial order.
            points=np.argwhere(region)
            rng.shuffle(points)
            available=region.copy()
            for point in points[:2000]:
                lo=point-widths//2;hi=lo+widths
                if np.any(lo<0) or np.any(hi>region.shape):continue
                box=tuple(slice(int(a),int(b)) for a,b in zip(lo,hi))
                if not available[box].all() or available[box].size<n:continue
                coords=np.flatnonzero(np.ones(tuple(widths),bool))
                values=volume[box].ravel()
                patches.append(rng.choice(values,size=n,replace=False))
                available[box]=False
                if len(patches)==6:break
            fit_values=volume[available]
            if len(patches)<4:reason='fewer_than_4_null_patches'
            elif len(fit_values)<n:reason='insufficient_disjoint_fit'
            else:
                fit=rng.choice(fit_values,size=n,replace=False)
                candidate=rng.choice(volume[mask],size=n,replace=False)
                observed=mmd(candidate,fit);null=[mmd(p,fit) for p in patches]
                rank=(1+sum(v<=observed for v in null))/(len(null)+1)
        score=base if rank is None else base+.5*(2*rank-1)
        if base>=0:c0[mask]=1
        if score>=0:c1[mask]=1
        records.append(dict(candidate=index,voxels=nvox,mean_probability=q,base_score=base,calibrated_score=score,reference_rank=rank,invalid_reason=reason,null_patches=len(patches),diameter_mm=diameter,compartment='core' if core else 'shell'))
    return labels,c0,c1,records
