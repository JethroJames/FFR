"""
Teacher Model Core Implementation
"""

import json
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
import time
from ffr.teacher.prompts import (
    get_prompt_for_analysis,
    format_input_information
)
from ffr.teacher.video_utils import create_openai_video_message, create_openai_image_message
import os

class TeacherModel:
    """Teacher model for analyzing student model responses"""
    
    def __init__(self, 
                 api_key: str,
                 api_base: str = "https://api.openai.com/v1",
                 model_name: str = "gpt-4o",
                 temperature: float = 0.1,
                 max_retries: int = 3):
        """
        Initialize Teacher Model
        
        Args:
            api_key: OpenAI API key
            api_base: API base URL
            model_name: Model name to use
            temperature: Temperature for generation
            max_retries: Maximum retry attempts for API calls
        """
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
    
    def analyze_student_response(self,
                                question: str,
                                video_path: str,
                                student_response: str,
                                student_score: float,
                                ground_truth: str,
                                reference_reasoning: Optional[str] = None,
                                incorrect_only: bool = False,
                                nframes: int = 16) -> Dict[str, Any]:
        """
        Analyze student model's response and provide feedback
        
        Args:
            question: The question asked
            video_path: Path to video/image file
            student_response: Student model's response
            student_score: Score from rule-based evaluator
            ground_truth: The correct answer
            reference_reasoning: Optional reference reasoning process
            incorrect_only: Use error-only analysis prompt
            nframes: Number of frames to extract from video
        
        Returns:
            Dictionary containing analysis results
        """
        # Format input information
        input_info = format_input_information(
            question=question,
            ground_truth=ground_truth,
            student_response=student_response,
            student_score=student_score,
            reference_reasoning=reference_reasoning
        )
        
        # Select appropriate prompt
        prompt_template = get_prompt_for_analysis(
            incorrect_only=incorrect_only,
            include_tools=False
        )

        # Format the full prompt
        full_prompt = prompt_template.format(input_information=input_info)
        # Create OpenAI message with video/image
        messages = self._create_message_with_media(
            video_path, full_prompt, nframes
        )
        # Get teacher model response
        analysis = self._get_model_response(messages)       
        # Parse the response
        result = self._parse_analysis(analysis)
        # Add metadata
        result['metadata'] = {
            'student_score': student_score,
            'incorrect_only_mode': incorrect_only,
            'model_used': self.model_name,
            'timestamp': time.time()
        }
        return result
    
    def _create_message_with_media(self, 
                                   media_path: str, 
                                   prompt: str,
                                   nframes: int) -> List[Dict[str, Any]]:
        """
        Create OpenAI API message with video or image
        """
        # Check if it's a video or image
        if media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return create_openai_video_message(media_path, prompt, nframes)
        else:
            return create_openai_image_message(media_path, prompt)
    
    def _get_model_response(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get response from teacher model with retry logic
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)
        
        return ""
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """
        Parse teacher model's analysis response
        """
        result = {
            'raw_response': response,
            'thinking': None,
            'error_classification': None,
            'evidence_patch': None,
            'parse_success': False
        }
        
        # Extract thinking section
        think_pattern = r'<think>(.*?)</think>'
        think_match = re.search(think_pattern, response, re.DOTALL)
        if think_match:
            result['thinking'] = think_match.group(1).strip()
        
        # Extract answer section
        answer_pattern = r'<answer>(.*?)</answer>'
        answer_match = re.search(answer_pattern, response, re.DOTALL)
        
        if answer_match:
            answer_text = answer_match.group(1).strip()
            try:
                answer_data = json.loads(answer_text)
                result['error_classification'] = answer_data.get('error_classification')
                result['evidence_patch'] = answer_data.get('evidence_patch')
                result['parse_success'] = True
            except json.JSONDecodeError:
                result['evidence_patch'] = {
                    'content': answer_text,
                    'key_frames': [],
                    'temporal_markers': [],
                    'spatial_regions': []
                }
        
        return result
