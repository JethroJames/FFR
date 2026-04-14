"""Reward functions for GRPO training."""

import os
import re
from datetime import datetime

from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer


def extract_answer(text):
    """Extract content from <answer>...</answer> tags."""
    pattern = r'<answer>\s*(.*?)\s*</answer>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def normalize_number(num_str):
    """Parse a number string, handling commas."""
    try:
        num_str = num_str.replace(',', '')
        return float(num_str)
    except Exception:
        return None


def word_error_rate(reference, hypothesis):
    """Compute word error rate between reference and hypothesis."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    m, n = len(ref_words), len(hyp_words)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])
    return d[m][n] / max(1, m)


def compute_rouge_score(reference, hypothesis, use_stemmer=True):
    """Compute average ROUGE F-measure across rouge1, rouge2, rougeL."""
    scorer = rouge_scorer.RougeScorer(
        ['rouge1', 'rouge2', 'rougeL'], use_stemmer=use_stemmer
    )
    scores = scorer.score(reference, hypothesis)
    average_fmeasure = (
        scores['rouge1'].fmeasure
        + scores['rouge2'].fmeasure
        + scores['rougeL'].fmeasure
    ) / 3
    return average_fmeasure


def accuracy_reward(completions, solution, **kwargs):
    """Reward function based on answer correctness.

    Supports multiple question types: multiple choice, numerical, OCR,
    free-form, and regression.
    """
    question_type = kwargs['problem_type'][0]
    contents = [completion[0]["content"] for completion in completions]
    current_time = datetime.now().strftime("%d-%H-%M-%S-%f")
    rewards = []

    for content, sol in zip(contents, solution):
        try:
            output_ans = extract_answer(content)
            gt_ans = extract_answer(sol)

            if question_type == "multiple choice":
                reward = 1.0 if output_ans.strip() == gt_ans.strip() else 0.0

            elif question_type == "numerical":
                gt_has_decimal = ("." in gt_ans) or ("," in gt_ans)
                out_has_decimal = ("." in output_ans) or ("," in output_ans)
                if gt_has_decimal != out_has_decimal:
                    reward = 0.0
                else:
                    gt_number = normalize_number(gt_ans)
                    out_number = normalize_number(output_ans)
                    if gt_number is None or out_number is None:
                        reward = 0.0
                    else:
                        reward = 1.0 if round(gt_number, 2) == round(out_number, 2) else 0.0

            elif question_type == "OCR":
                error_rate = word_error_rate(gt_ans, output_ans)
                reward = max(0.0, min(1.0, 1 - error_rate))

            elif question_type == "free-form":
                score = compute_rouge_score(gt_ans, output_ans)
                reward = max(0.0, min(1.0, score))

            elif question_type == "regression":
                gt_number = normalize_number(gt_ans)
                out_number = normalize_number(output_ans)
                if gt_number is None or out_number is None:
                    reward = 0.0
                else:
                    rel_diff = (abs(out_number - gt_number) + 1e-9) / (abs(gt_number) + 1e-9)
                    rel_diff = min(1.0, max(0.0, rel_diff))
                    reward = 1 - rel_diff
            else:
                reward = 0.0

        except Exception as e:
            print(f"Error in reward_fn for question_type '{question_type}': {e}")
            reward = 0.0

        rewards.append(reward)

        if os.getenv("DEBUG_MODE") == "true":
            log_path = os.getenv("LOG_PATH")
            if log_path:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"------------- {current_time} Accuracy reward: {reward} -------------\n")
                    f.write(f"Content: {content}\n")
                    f.write(f"Solution: {sol}\n")

    return rewards


def format_reward(completions, **kwargs):
    """Reward function that checks <think>...</think><answer>...</answer> format."""
    pattern = r"<think>.*?</think>\s*<answer>.*?</answer>"
    completion_contents = [completion[0]["content"] for completion in completions]
    matches = [re.fullmatch(pattern, content, re.DOTALL) for content in completion_contents]
    return [1.0 if match else 0.0 for match in matches]


REWARD_REGISTRY = {
    "accuracy": accuracy_reward,
    "format": format_reward,
}
