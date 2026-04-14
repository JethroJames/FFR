"""
Video Processing Utilities - Convert video to OpenAI API format.

Core functionality:
1. Extract video frames using qwen_vl_utils
2. Convert frames to base64 format for OpenAI API
"""

import base64
from io import BytesIO
from typing import List, Dict, Any

import torch
import numpy as np
from PIL import Image
from qwen_vl_utils import process_vision_info


def process_video_to_frames(video_path: str, nframes: int = 16, max_pixels: int = 128 * 28 * 28):
    """
    Extract video frames using qwen_vl_utils.

    Args:
        video_path: Path to the video file
        nframes: Number of frames to extract
        max_pixels: Maximum pixel count

    Returns:
        Video frames (Tensor or None)
    """
    messages = [{
        "role": "user",
        "content": [{
            "type": "video",
            "video": video_path,
            "nframes": nframes,
            "max_pixels": max_pixels,
        }]
    }]
    
    try:
        _, video_inputs, _ = process_vision_info(messages, return_video_kwargs=True)
        if video_inputs is not None and len(video_inputs) > 0:
            return video_inputs[0]
        return None
    except Exception as e:
        print(f"Error processing video {video_path}: {e}")
        return None


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    """
    Convert Tensor to PIL Image.

    Args:
        tensor: Image tensor, supports [C, H, W] or [H, W, C] format

    Returns:
        PIL Image
    """
    if tensor.dim() == 3:
        if tensor.shape[0] in [1, 3, 4]:  # [C, H, W]
            img_array = tensor.permute(1, 2, 0).cpu().numpy()
        else:  # [H, W, C]
            img_array = tensor.cpu().numpy()
    else:
        img_array = tensor.cpu().numpy()

    # Normalize to [0, 255]
    if img_array.max() <= 1.0:
        img_array = (img_array * 255).astype(np.uint8)
    else:
        img_array = img_array.astype(np.uint8)
    
    return Image.fromarray(img_array)


def image_to_base64(image, format: str = "PNG") -> str:
    """
    Convert image to base64 string.

    Args:
        image: PIL Image or Tensor
        format: Image format (PNG, JPEG, etc.)

    Returns:
        Base64 encoded string
    """
    if torch.is_tensor(image):
        image = tensor_to_image(image)
    
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode()


def frames_to_base64_list(frames) -> List[str]:
    """
    Convert video frames to a list of base64 strings.

    Args:
        frames: Video frames (4D Tensor [N,C,H,W], 3D Tensor [C,H,W], or list)

    Returns:
        List of base64 strings
    """
    base64_list = []
    
    if torch.is_tensor(frames):
        if frames.dim() == 4:  # [N, C, H, W]
            for i in range(frames.shape[0]):
                base64_str = image_to_base64(frames[i])
                base64_list.append(base64_str)
        elif frames.dim() == 3:  # [C, H, W]
            base64_str = image_to_base64(frames)
            base64_list.append(base64_str)
    else:  # list format
        for frame in frames:
            base64_str = image_to_base64(frame)
            base64_list.append(base64_str)
    
    return base64_list


def create_openai_video_message(video_path: str,
                                text_prompt: str,
                                nframes: int = 16) -> List[Dict[str, Any]]:
    """
    Create OpenAI API message containing video frames.

    Args:
        video_path: Path to the video
        text_prompt: Text prompt
        nframes: Number of video frames

    Returns:
        List of messages in OpenAI API format
    """
    frames = process_video_to_frames(video_path, nframes)
    
    if frames is None or len(frames) == 0:
        raise ValueError(f"Failed to process video: {video_path}")
    
    base64_list = frames_to_base64_list(frames)

    content = []

    # Add video frames
    for base64_str in base64_list:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_str}"
            }
        })
    
    # Add text
    content.append({
        "type": "text",
        "text": text_prompt
    })
    
    return [{
        "role": "user",
        "content": content
    }]


def create_openai_image_message(image_path: str,
                                text_prompt: str) -> List[Dict[str, Any]]:
    """
    Create OpenAI API message containing a single image.

    Args:
        image_path: Path to the image
        text_prompt: Text prompt

    Returns:
        List of messages in OpenAI API format
    """
    image = Image.open(image_path)
    base64_str = image_to_base64(image)
    
    return [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_str}"
                }
            },
            {
                "type": "text",
                "text": text_prompt
            }
        ]
    }]


# Convenience functions

def quick_video_to_openai(video_path: str, prompt: str, nframes: int = 16) -> List[Dict]:
    """Convenience function: video -> OpenAI message (one step)."""
    return create_openai_video_message(video_path, prompt, nframes)


def quick_image_to_openai(image_path: str, prompt: str) -> List[Dict]:
    """Convenience function: image -> OpenAI message (one step)."""
    return create_openai_image_message(image_path, prompt)
