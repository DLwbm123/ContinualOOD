import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_p3 import component_matches

class Matching(unittest.TestCase):
    def test_one_prediction_cannot_claim_two_lesions(self):
        truth=np.zeros((8,3,3),bool);truth[1:3,1,1]=True;truth[5:7,1,1]=True
        pred=np.zeros_like(truth);pred[1:7,1,1]=True
        tp,ngt,npred,_,_=component_matches(pred,truth)
        self.assertEqual((tp,ngt,npred),(1,2,1))
    def test_empty_prediction_keeps_denominator(self):
        truth=np.ones((2,2,2),bool)
        self.assertEqual(component_matches(np.zeros_like(truth),truth)[:3],(0,1,0))

if __name__=='__main__':unittest.main()
