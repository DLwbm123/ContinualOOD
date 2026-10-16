"""Native XYZ volumes ↔ ZYX slices, without resampling or label access."""
import json
from pathlib import Path
import nibabel as nib
import numpy as np

RUNTIME_FIELDS={'study_uid','patient_key','image_path','geometry_path','modality','sequence','working_view','past_study_uids'}


def load_study(record):
    if set(record) != RUNTIME_FIELDS:
        raise ValueError('Runtime record violates the inference-only schema')
    image=nib.load(record['image_path'])
    data=np.asarray(image.dataobj,dtype=np.float32)
    if data.ndim != 3 or not np.isfinite(data).all():
        raise ValueError('Invalid image volume')
    support=data[data != 0]
    if not len(support):
        raise ValueError('Empty image support')
    lo,hi=np.percentile(support,[1,99])
    if hi <= lo:
        raise ValueError('Degenerate intensity range')
    normalized=np.clip((data-lo)/(hi-lo),0,1).transpose(2,1,0)
    return image,normalized,tuple(float(x) for x in image.header.get_zooms()[::-1])


def rgb_slice(volume,z):
    return np.repeat(np.rint(volume[z]*255).astype(np.uint8)[...,None],3,axis=-1)


def save_native(array_zyx,image,path):
    native=array_zyx.transpose(2,1,0)
    if native.shape != image.shape:
        raise ValueError('Native roundtrip shape mismatch')
    header=image.header.copy();header.set_data_dtype(native.dtype)
    result=nib.Nifti1Image(native,image.affine,header)
    result.set_qform(image.get_qform(),int(image.header['qform_code']))
    result.set_sform(image.get_sform(),int(image.header['sform_code']))
    nib.save(result,path)
