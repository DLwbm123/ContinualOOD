"""Screen same-grid volume duplicates; only compare full arrays on signature collisions."""
import collections
import json
import os
from pathlib import Path
import nibabel as nib
import numpy as np


def main():
    root=Path(os.environ['COOD_ROOT']);audit=json.loads((root/'private/data_audit_private.json').read_text())
    seen=collections.defaultdict(list);duplicates=[]
    for study in audit['studies']:
        a=np.asarray(nib.load(study['image']).dataobj)
        signature=(a.shape,tuple(a.ravel()[np.linspace(0,a.size-1,256,dtype=int)].tolist()))
        for previous in seen[signature]:
            if np.array_equal(a,np.asarray(nib.load(previous).dataobj)):
                duplicates.append([previous,study['image']])
        seen[signature].append(study['image'])
    (root/'private/duplicate_screen.json').write_text(json.dumps({'method':'256 regularly spaced voxel values plus shape; full comparison on collisions','images':len(audit['studies']),'duplicate_pairs':duplicates},indent=2))
    print(json.dumps({'images_screened':len(audit['studies']),'duplicate_pairs':len(duplicates)}))
    assert not duplicates,'Duplicate image groups require split repair before P3'


if __name__=='__main__':main()
