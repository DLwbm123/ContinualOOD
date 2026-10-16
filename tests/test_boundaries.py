"""Small checks for geometry, table sparsity, and runtime/label separation."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import nibabel as nib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_data import rows
from volume_io import load_study,save_native,RUNTIME_FIELDS


class Boundaries(unittest.TestCase):
    def test_roundtrip_and_label_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'image.nii.gz'; a=np.arange(120,dtype=np.float32).reshape(4,5,6)
            affine=np.diag([-0.7,-0.8,4.,1.]);affine[:3,3]=[13,19,-5]
            nib.save(nib.Nifti1Image(a,affine),p)
            record={k:'' for k in RUNTIME_FIELDS};record['image_path']=str(p)
            image,v,spacing=load_study(record)
            self.assertEqual(v.shape,(6,5,4))
            out=Path(tmp)/'roundtrip.nii.gz';save_native(a.transpose(2,1,0),image,out)
            restored=nib.load(out)
            np.testing.assert_array_equal(restored.get_fdata(),a)
            np.testing.assert_allclose(restored.affine,affine)
            with self.assertRaises(ValueError):load_study(dict(record,label_path='forbidden'))
    def test_sparse_table_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'table.xlsx'
            ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{ns}"><si><t>image</t></si><si><t>mask_new</t></si><si><t>a.nii.gz</t></si></sst>')
                z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData><row><c r="A1" t="s"><v>0</v></c><c r="C1" t="s"><v>1</v></c></row><row><c r="A2" t="s"><v>2</v></c><c r="C2" t="s"><v>2</v></c></row></sheetData></worksheet>')
            self.assertEqual(rows(p),[{'image':'a.nii.gz','mask_new':'a.nii.gz'}])


if __name__=='__main__':unittest.main()
