import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock dependencies
sys.modules["runpod"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["cv2"] = MagicMock()

import handler

class TestHandler(unittest.TestCase):
    @patch('handler.engine')
    @patch('handler.download_image')
    @patch('handler.encode_video_to_base64')
    def test_handler_success(self, mock_encode, mock_download, mock_engine):
        # Setup
        mock_engine.generate_video.return_value = "output.mp4"
        mock_download.return_value = "input.jpg"
        mock_encode.return_value = "base64data"
        
        job = {
            "input": {
                "prompt": "test prompt",
                "image_url": "http://example.com/image.jpg"
            }
        }
        
        # Execute
        result = handler.handler(job)
        
        # Assert
        self.assertEqual(result, {"video_base64": "base64data"})
        mock_engine.generate_video.assert_called_once()
        
    def test_handler_missing_input(self):
        job = {"input": {}}
        result = handler.handler(job)
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
