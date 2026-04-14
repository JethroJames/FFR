"""
Utility functions for Teacher Model API
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
import logging


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Setup logging configuration
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if log_file:
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=level,
            format=log_format
        )
    
    return logging.getLogger('teacher_model')


def load_json_file(file_path: str) -> Any:
    """
    Load JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Any, file_path: str, indent: int = 2):
    """
    Save data to JSON file
    """
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def validate_sample_format(sample: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate that a sample has the required format
    """
    required_fields = ['question', 'model_rollout_result', 'model_rollout_score', 'standard_answer']
    
    for field in required_fields:
        if field not in sample:
            return False, f"Missing required field: {field}"
    
    # Validate score is numeric
    try:
        float(sample['model_rollout_score'])
    except (TypeError, ValueError):
        return False, "model_rollout_score must be numeric"
    
    return True, None


def aggregate_error_statistics(analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate statistics from analysis results
    """
    stats = {
        'total_samples': len(analysis_results),
        'successful_analyses': 0,
        'failed_analyses': 0,
        'error_type_distribution': {},
        'samples_by_score': {
            'correct': 0,
            'incorrect': 0
        }
    }
    
    for result in analysis_results:
        # Parse success
        if result.get('parse_success'):
            stats['successful_analyses'] += 1
        else:
            stats['failed_analyses'] += 1
        
        # Error types
        error_type = result.get('error_classification')
        if error_type:
            stats['error_type_distribution'][error_type] = \
                stats['error_type_distribution'].get(error_type, 0) + 1
        
        # Score distribution
        metadata = result.get('metadata', {})
        if 'student_score' in metadata:
            if metadata['student_score'] > 0:
                stats['samples_by_score']['correct'] += 1
            else:
                stats['samples_by_score']['incorrect'] += 1
    
    # Calculate success rate
    total = stats['total_samples']
    if total > 0:
        stats['success_rate'] = (stats['successful_analyses'] / total) * 100
    
    return stats