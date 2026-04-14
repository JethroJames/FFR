#!/usr/bin/env python3
"""
Preprocess SFT data: convert eval output JSON to SFT training format.

Input format (eval output):
{
  "results": [
    {
      "problem_id": 125739,
      "problem": "...",
      "data_type": "video",
      "problem_type": "multiple choice",
      "options": ["A. ...", "B. ...", ...],
      "solution": "<answer>B</answer>",
      "path": "./PerceptionTest/video_1007.mp4",
      "data_source": "Video-R1",
      "output": "The person is sitting... <answer>B</answer>",
      "prediction": "B",
      "reward": 1.0,
      "correct": true
    },
    ...
  ]
}

Output format (SFT training):
[
  {
    "problem_id": 125739,
    "problem": "...",
    "data_type": "video",
    "problem_type": "multiple choice",
    "options": ["A. ...", "B. ...", ...],
    "solution": "<answer>B</answer>",
    "path": "PerceptionTest/video_1007.mp4",  # cleaned path
    "data_source": "Video-R1",
    "process": "The person is sitting..."  # renamed from output, without answer tag
  },
  ...
]
"""

import json
import argparse
import re
from pathlib import Path


def extract_process_from_output(output: str) -> str:
    """Extract the reasoning process from output, removing the final <answer> tag."""
    # Remove trailing <answer>...</answer> tag
    pattern = r'\s*<answer>.*?</answer>\s*$'
    process = re.sub(pattern, '', output, flags=re.IGNORECASE | re.DOTALL)
    return process.strip()


def clean_video_path(path: str) -> str:
    """Clean video path by removing leading './' if present."""
    if path.startswith('./'):
        return path[2:]
    return path


def preprocess_data(input_path: str, output_path: str, filter_correct: bool = True):
    """
    Preprocess evaluation output to SFT training format.

    Args:
        input_path: Path to input JSON file (eval output)
        output_path: Path to output JSON file (SFT format)
        filter_correct: If True, only keep correct predictions for training
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both {"results": [...]} and [...] formats
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    elif isinstance(data, list):
        results = data
    else:
        raise ValueError(f"Unknown data format: expected dict with 'results' key or list")

    processed = []
    total_count = len(results)
    correct_count = 0

    for item in results:
        # Optionally filter for correct predictions only
        if filter_correct and not item.get('correct', False):
            continue

        correct_count += 1

        # Extract process from output
        output = item.get('output', '')
        process = extract_process_from_output(output)

        # Clean video path
        path = clean_video_path(item.get('path', ''))

        processed_item = {
            'problem_id': item.get('problem_id'),
            'problem': item.get('problem', ''),
            'data_type': item.get('data_type', 'video'),
            'problem_type': item.get('problem_type', 'multiple choice'),
            'options': item.get('options', []),
            'solution': item.get('solution', ''),
            'path': path,
            'data_source': item.get('data_source', 'Video-R1'),
            'process': process,
        }

        processed.append(processed_item)

    # Save processed data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print(f"Preprocessing complete!")
    print(f"  Total samples: {total_count}")
    print(f"  Correct samples: {correct_count}")
    print(f"  Output samples: {len(processed)}")
    print(f"  Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Preprocess SFT data')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file path')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file path')
    parser.add_argument('--all', action='store_true',
                        help='Include all samples (not just correct ones)')

    args = parser.parse_args()

    preprocess_data(
        input_path=args.input,
        output_path=args.output,
        filter_correct=not args.all
    )


if __name__ == '__main__':
    main()
