import handler
import os
import base64

def simulate_runpod_event():
    print("Simulating RunPod event...")
    
    # We will mock the engine's generate_video to avoid the ltx_video dependency
    from unittest.mock import MagicMock
    handler.engine = MagicMock()
    handler.engine.generate_video.side_effect = lambda **kwargs: open(kwargs['output_path'], 'wb').write(b'fake video data')

    # Mock download_image
    handler.download_image = MagicMock(return_value="mock_input.jpg")
    
    event = {
        "input": {
            "prompt": "A cinematic shot of a sunset",
            "image_url": "http://example.com/sunset.jpg",
            "num_steps": 20
        }
    }
    
    result = handler.handler(event)
    
    if "error" in result:
        print(f"FAILED: Handler returned error: {result['error']}")
    elif "video_base64" in result:
        print("SUCCESS: Handler returned video_base64")
        # print(f"Base64 data (first 50 chars): {result['video_base64'][:50]}...")
    else:
        print(f"FAILED: Unexpected result format: {result}")

if __name__ == "__main__":
    simulate_runpod_event()
