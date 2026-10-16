"""Strict CUDA loading plus observation-only hooks around locked upstream code."""
from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import random
import time

import numpy as np
import torch
from verify_model import load_verified


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)


def make_pipeline(output):
    model = load_verified()
    from tta_pipeline.biomedparse_inference import BiomedParseSegmenter
    from tta_pipeline.config import PipelineConfig
    from tta_pipeline.pipeline import PromptedSegmentationPipeline
    from tta_pipeline.roi_planning import RoiPlanner
    from tta_pipeline.llm_inference import DEFAULT_PLANS
    config = PipelineConfig(output_dir=output)
    config.roi.padding_mm = 30.0  # Locked upstream YAML overrides dataclass's 25 mm.
    pipeline = PromptedSegmentationPipeline.__new__(PromptedSegmentationPipeline)
    pipeline.config = config
    pipeline.planner = None  # Explicit plan only; no LLM client is constructed.
    pipeline.roi_planner = RoiPlanner(config.roi)
    segmenter = BiomedParseSegmenter.__new__(BiomedParseSegmenter)
    segmenter.config = config.biomedparse
    segmenter.device = torch.device('cuda')
    segmenter._model = model
    pipeline.segmenter = segmenter
    output.mkdir(parents=True, exist_ok=True)
    plan = DEFAULT_PLANS['bladder tumor']
    (output/'effective_config.json').write_text(json.dumps(asdict(config), default=str, indent=2))
    (output/'plan.json').write_text(json.dumps(asdict(plan), indent=2))
    return pipeline, plan


@contextmanager
def trace_native(pipeline):
    import tta_pipeline.pipeline as native
    original_extract, original_eval = native.extract_candidates, native.evaluate_candidates
    original_segment = pipeline.segmenter.segment
    trace = dict(candidates=[], results=[], forwards=[], statistics_seconds=0.)
    def extract(maps, **kwargs):
        trace['raw_candidates'] = original_extract(maps, min_pixels=1, threshold=kwargs['threshold'])
        result = original_extract(maps, **kwargs)
        trace['candidates'] = result
        return result
    def evaluate(image, organ_mask, candidates, config):
        start = time.monotonic()
        result = original_eval(image, organ_mask, candidates, config)
        trace['statistics_seconds'] += time.monotonic()-start
        trace['control'] = organ_mask.copy()
        trace['results'] = result
        return result
    def segment(*args, **kwargs):
        torch.cuda.synchronize(); start=time.monotonic()
        result=original_segment(*args, **kwargs)
        torch.cuda.synchronize()
        trace['forwards'].append(dict(prompts=list(kwargs.get('prompts', [])),rois=kwargs.get('rois'),seconds=time.monotonic()-start,maps={k:v.copy() for k,v in result.items()}))
        return result
    native.extract_candidates, native.evaluate_candidates = extract, evaluate
    pipeline.segmenter.segment = segment
    try:
        yield trace
    finally:
        native.extract_candidates, native.evaluate_candidates = original_extract, original_eval
        pipeline.segmenter.segment = original_segment


def run_slice(pipeline, plan, rgb, spacing, output, seed, instrument=True):
    pipeline.config.output_dir=output; output.mkdir(parents=True,exist_ok=True)
    seed_all(seed)
    kwargs=dict(image=rgb,plan=plan,target_concept='bladder tumor',modality='MRI',prompts=['bladder tumor'],pixel_spacing_mm=tuple(spacing),enable_tta=True,save_intermediates=False)
    if not instrument:
        return pipeline.run_with_plan(**kwargs), None
    with trace_native(pipeline) as trace:
        result = pipeline.run_with_plan(**kwargs)
    serial=[]
    tested={r.candidate.label:r for r in trace['results']}
    for c in trace['raw_candidates']:
        r=tested.get(c.label)
        reason='small_region' if c.area < pipeline.config.stats.min_pixels else 'insufficient_reference' if r is None else 'BH_retained' if r.q_value <= pipeline.config.stats.alpha else 'BH_deleted'
        serial.append(dict(label=c.label,area=c.area,mean_probability=c.mean_probability,reason=reason,statistic=None if r is None else r.test_statistic,p=None if r is None else r.p_value,q=None if r is None else r.q_value))
    anchor_fallback='full_frame' in result.anchor_masks
    meta=dict(candidates=serial,rois=[asdict(r) for r in result.roi_proposals],anchor_fallback=anchor_fallback,mitigation_enabled=pipeline.config.mitigation.enabled,statistics_seconds=trace['statistics_seconds'],forward_seconds=sum(f['seconds'] for f in trace['forwards']))
    (output/'trace.json').write_text(json.dumps(meta,indent=2,allow_nan=False))
    arrays={'probability':result.probability_maps['bladder tumor'],'control':trace['control'],'final':result.final_mask}
    for i,f in enumerate(trace['forwards']):
        for j,(key,value) in enumerate(f['maps'].items()):
            arrays[f'call_{i}_prompt_{j}']=value
    np.savez_compressed(output/'trace.npz',**arrays)
    return result, meta
