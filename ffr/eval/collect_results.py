#!/usr/bin/env python3
"""
Collect experiment results and generate Markdown report.
"""

import json
import os
import re
from collections import defaultdict


def load_results(filepath):
    """Load results from JSON file and compute accuracy."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check for final_acc (used by vsibench)
    if 'final_acc' in data and data['final_acc']:
        mean_acc = data['final_acc'][0].get('mean_acc', 0)
        return {'accuracy': mean_acc * 100}

    # Standard calculation
    results = data.get('results', data) if isinstance(data, dict) else data
    total = len(results)
    correct = sum(1 for r in results if r.get('correct', False))
    accuracy = correct / total * 100 if total > 0 else 0

    return {'accuracy': accuracy}


def parse_filename(filename):
    """Parse filename to extract benchmark name and config."""
    name = filename.replace('_greedy_output.json', '').replace('eval_', '')

    # Check for patch_tax pattern
    tax_match = re.search(r'_patch_tax_([\d.]+)$', name)
    if tax_match:
        tax_value = tax_match.group(1)
        benchmark = name.replace(f'_patch_tax_{tax_value}', '')
        return benchmark, f'patch_tax_{tax_value}'

    # Check for qwen3-32B pattern (sft model)
    if '_qwen3-32B' in name:
        benchmark = name.replace('_qwen3-32B', '')
        return benchmark, 'sft_32B'

    return name, 'unknown'


def collect_all_results():
    """Collect results from both directories."""
    base_dir = os.getenv("EVAL_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "outputs"))
    all_results = defaultdict(dict)

    # Collect ablation results
    ablation_dir = os.path.join(base_dir, 'ablation', 'vanilla')
    if os.path.exists(ablation_dir):
        for filename in os.listdir(ablation_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(ablation_dir, filename)
                benchmark, config = parse_filename(filename)
                result = load_results(filepath)
                all_results[benchmark][config] = result

    # Collect sft_test_32B results
    sft_dir = os.path.join(base_dir, 'sft_test_32B')
    if os.path.exists(sft_dir):
        for filename in os.listdir(sft_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(sft_dir, filename)
                benchmark, config = parse_filename(filename)
                result = load_results(filepath)
                all_results[benchmark][config] = result

    return all_results


def create_markdown_report(results, output_path):
    """Create Markdown report from results."""

    # Specified benchmark order
    benchmark_order = ['mmvu', 'vsibench', 'videommmu', 'holmes', 'longvideobench', 'lvbench', 'mvbench', 'tempcompass']

    # Config order
    config_order = ['sft_32B', 'patch_tax_0.3', 'patch_tax_0.5', 'patch_tax_0.7', 'patch_tax_1.0']

    # Config display names
    config_names = {
        'sft_32B': 'SFT-32B',
        'patch_tax_0.3': 'Patch-Tax-0.3',
        'patch_tax_0.5': 'Patch-Tax-0.5',
        'patch_tax_0.7': 'Patch-Tax-0.7',
        'patch_tax_1.0': 'Patch-Tax-1.0'
    }

    # Build markdown content
    lines = []
    lines.append("# Experiment Results\n")
    lines.append("")

    # Header row
    header = "| Model |"
    for bench in benchmark_order:
        header += f" {bench} |"
    lines.append(header)

    # Separator row
    sep = "|-------|"
    for _ in benchmark_order:
        sep += "--------|"
    lines.append(sep)

    # Data rows
    for config in config_order:
        row = f"| {config_names.get(config, config)} |"
        for bench in benchmark_order:
            if bench in results and config in results[bench]:
                acc = results[bench][config]['accuracy']
                row += f" {acc:.2f} |"
            else:
                row += " - |"
        lines.append(row)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Markdown report saved to: {output_path}")

    # Print to console
    print("\n" + '\n'.join(lines))


def main():
    results = collect_all_results()
    output_path = os.path.join(os.path.dirname(__file__), "experiment_results.md")
    create_markdown_report(results, output_path)


if __name__ == '__main__':
    main()
