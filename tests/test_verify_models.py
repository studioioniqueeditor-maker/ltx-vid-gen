import unittest
import os
import shutil
import verify_models

class TestVerifyModels(unittest.TestCase):
    def setUp(self):
        self.test_dir = "/tmp/test-models"
        os.makedirs(self.test_dir, exist_ok=True)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_verify_success(self):
        os.makedirs(os.path.join(self.test_dir, "configs"), exist_ok=True)
        result = verify_models.verify_ltx_model_files(self.test_dir)
        self.assertTrue(result)
        
    def test_verify_failure(self):
        result = verify_models.verify_ltx_model_files(self.test_dir)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
