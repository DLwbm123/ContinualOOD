"""Audit the released tables and native volumes; outputs are private."""
import collections
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import nibabel as nib
import numpy as np


def rows(path):
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
        result = []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:row', ns):
            values = {}
            for cell in row.findall('m:c', ns):
                column = ''.join(c for c in cell.attrib['r'] if c.isalpha())
                val = cell.find('m:v', ns)
                text = val.text if val is not None else ''
                values[column] = strings[int(text)] if cell.attrib.get('t') == 's' else text
            result.append(values)
        header = result[0]
        return [{header[k]: v for k, v in row.items() if k in header} for row in result[1:]]


def audit(root, output):
    output.mkdir(parents=True, exist_ok=True)
    studies, issues, centers = [], [], {}
    for table in sorted(root.glob('*/*/*.xlsx')):
        center = table.parent.name
        images = {p.name: p for p in (table.parent / 'T2WI').glob('*.nii.gz')}
        masks = {p.name: p for p in (table.parent / 'Annotation').glob('*.nii.gz')}
        mapping = collections.defaultdict(list)
        for row in rows(table):
            im = row.get('image_name', row.get('image', ''))
            ma = row.get('mask_new', row.get('mask_name', ''))
            if not im and not ma:
                continue
            if im not in images or ma not in masks:
                issues.append({'center': center, 'type': 'missing_table_file', 'image': im, 'mask': ma})
                continue
            mapping[im].append(ma)
        for im, path in sorted(images.items()):
            image = nib.load(path)
            a = np.asarray(image.dataobj)
            shape = image.shape
            record = dict(center=center, image=str(path), image_name=im, masks=[], shape=shape,
                          affine=image.affine.tolist(), spacing=image.header.get_zooms(), orientation=nib.aff2axcodes(image.affine),
                          qform_code=int(image.header['qform_code']), sform_code=int(image.header['sform_code']),
                          finite=bool(np.isfinite(a).all()), nonzero=int(np.count_nonzero(a)), errors=[])
            if len(shape) != 3 or not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3, :3])) < 1e-8:
                record['errors'].append('invalid_geometry')
            for name in mapping[im]:
                mask = nib.load(masks[name]); m = np.asarray(mask.dataobj)
                matched = shape == mask.shape and np.allclose(image.affine, mask.affine, atol=1e-4)
                record['masks'].append(dict(path=str(masks[name]), matched=matched, labels=np.unique(m).tolist(), nonzero=int(np.count_nonzero(m))))
                if not matched:
                    record['errors'].append('mask_geometry_mismatch')
            if not record['masks']:
                record['errors'].append('missing_annotation')
            studies.append(record)
        centers[center] = dict(images=len(images), masks=len(masks), table_pairs=sum(map(len, mapping.values())),
                               unreferenced_masks=sorted(set(masks)-{m for v in mapping.values() for m in v}))
    result = dict(centers=centers, issues=issues, studies=studies)
    (output/'data_audit_private.json').write_text(json.dumps(result, indent=2, default=lambda x: x.item()))
    print(json.dumps(dict(centers=centers, issues=len(issues), studies=len(studies), errors=collections.Counter(e for s in studies for e in s['errors']), shapes=collections.Counter(str(s['shape']) for s in studies)), indent=2))


if __name__ == '__main__':
    audit(Path(os.environ['COOD_DATA_ROOT'])/'raw/fedbca/13622759/extracted', Path(os.environ['COOD_ROOT'])/'private')
