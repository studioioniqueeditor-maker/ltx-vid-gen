import os
import unittest
from unittest.mock import patch, MagicMock
import download_models

class TestDownloadModels(unittest.TestCase):
    @patch('download_models.snapshot_download')
    @patch('os.makedirs')
    def test_download_ltx_model_success(self, mock_makedirs, mock_snapshot):
        # Setup
        mock_snapshot.return_value = "/mock/path"
        
        # Execute
        result = download_models.download_ltx_model(target_dir="/tmp/mock-models")
        
        # Assert
        self.assertTrue(result)
        mock_snapshot.assert_called_once()
        mock_makedirs.assert_called_once_with("/tmp/mock-models", exist_ok=True)

    @patch('download_models.snapshot_download')
    def test_download_ltx_model_failure(self, mock_snapshot):
        # Setup
        mock_snapshot.side_effect = Exception("Download failed")
        
        # Execute
        result = download_models.download_ltx_model(target_dir="/tmp/mock-models")
        
        # Assert
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
