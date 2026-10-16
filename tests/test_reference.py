import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reference_methods import mmd,research_candidates

class Reference(unittest.TestCase):
    def test_mmd_and_no_reference_fallback(self):
        a=np.linspace(0,1,32)
        self.assertAlmostEqual(mmd(a,a),0.)
        self.assertGreater(mmd(np.zeros(32),np.ones(32)),1.9)
        image=np.zeros((5,5,5),np.float32);prob=image.copy();prob[1:4,1:4,1:4]=.7
        labels,c0,c1,records=research_candidates(image,prob,np.zeros_like(image),(1,1,1),'test')
        self.assertEqual(len(records),1)
        np.testing.assert_array_equal(c0,c1)
        self.assertEqual(records[0]['invalid_reason'],'no_compatible_reference')
        self.assertEqual(int(c0.sum()),27)
    def test_small_candidate_is_kept_without_calibration(self):
        image=np.zeros((3,3,3),np.float32);prob=image.copy();prob[1,1,1]=.9
        _,c0,c1,records=research_candidates(image,prob,np.ones_like(image),(1,1,1),'small')
        self.assertEqual(records[0]['invalid_reason'],'candidate_under_16_samples')
        self.assertEqual(int(c1.sum()),1)

if __name__=='__main__':unittest.main()
