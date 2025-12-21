import unittest
from unittest.mock import patch
import download_models_distilled

class TestDownloadModelsDistilled(unittest.TestCase):
    @patch('download_models_distilled.snapshot_download')
    @patch('os.makedirs')
    def test_download_distilled_success(self, mock_makedirs, mock_snapshot):
        # Setup
        mock_snapshot.return_value = "/mock/path"
        
        # Execute
        result = download_models_distilled.download_distilled_model(target_dir="/tmp/mock-distilled")
        
        # Assert
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/tmp/mock-distilled", exist_ok=True)
        
        # Verify allow_patterns are correct
        mock_snapshot.assert_called_once()
        _, kwargs = mock_snapshot.call_args
        self.assertIn("allow_patterns", kwargs)
        self.assertIn("**/*2b*distilled*fp8*", kwargs["allow_patterns"])
        self.assertIn("configs/**", kwargs["allow_patterns"])
        self.assertIn("ignore_patterns", kwargs)

    @patch('download_models_distilled.snapshot_download')
    def test_download_distilled_failure(self, mock_snapshot):
        # Setup
        mock_snapshot.side_effect = Exception("Download failed")
        
        # Execute
        result = download_models_distilled.download_distilled_model(target_dir="/tmp/mock-distilled")
        
        # Assert
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
