import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock ltx_video before importing inference_engine
mock_ltx = MagicMock()
sys.modules["ltx_video"] = mock_ltx
sys.modules["ltx_video.inference"] = mock_ltx.inference

import inference_engine

class TestInferenceEngine(unittest.TestCase):
    @patch('inference_engine.InferenceConfig')
    @patch('inference_engine.infer')
    def test_generate_video(self, mock_infer, mock_config_class):
        # Setup
        # Make InferenceConfig return itself or a mock we can inspect
        mock_config_instance = MagicMock()
        mock_config_class.return_value = mock_config_instance
        
        engine = inference_engine.LTXInferenceEngine(
            repo_path="/mock/LTX-Video",
            config_file="configs/ltxv-2b-0.9.8-distilled-fp8.yaml"
        )
        
        # Execute
        engine.generate_video(
            prompt="A test prompt",
            image_path="test.jpg",
            output_path="output.mp4"
        )
        
        # Assert
        mock_config_class.assert_called_once()
        _, kwargs = mock_config_class.call_args
        self.assertEqual(kwargs['prompt'], "A test prompt")
        self.assertEqual(kwargs['conditioning_media_paths'], ["test.jpg"])
        self.assertEqual(kwargs['output_path'], "output.mp4")
        
        mock_infer.assert_called_once_with(mock_config_instance)

if __name__ == "__main__":
    unittest.main()
