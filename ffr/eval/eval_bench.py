import os
import re
import json
import argparse
from typing import Dict, List

import torch
from tqdm import tqdm

from transformers import AutoProcessor, AutoTokenizer
from vllm import LLM, SamplingParams
from qwen_vl_utils import process_vision_info

BSZ = 128

os.environ["DECORD_EOF_RETRY_MAX"] = "20480"

QUESTION_TEMPLATE = (
        "{Question}\n"
        "Please think about this question as if you were a human pondering deeply. "
        "Engage in an internal dialogue using expressions such as 'let me think', 'wait', 'Hmm', 'oh, I see', 'let's break it down', etc, or other natural language thought expressions "
        "It's encouraged to include self-reflection or verification in the reasoning process. "
        "Provide your detailed reasoning between the <think> and </think> tags, and then give your final answer between the <answer> and </answer> tags."
    )

TYPE_TEMPLATE = {
        "multiple choice": " Please provide only the single option letter (e.g., A, B, C, D, etc.) within the <answer> </answer> tags.",
        "numerical": " Please provide the numerical value (e.g., 42 or 3.14) within the <answer> </answer> tags.",
        "OCR": " Please transcribe text from the image/video clearly and provide your text answer within the <answer> </answer> tags.",
        "free-form": " Please provide your text answer within the <answer> </answer> tags.",
        "regression": " Please provide the numerical value (e.g., 42 or 3.14) within the <answer> </answer> tags."
    }

# ---------- Utility functions ----------
def load_dataset(path: str) -> List[dict]:
    if path.endswith(".jsonl"):
        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data.append(json.loads(line))
        return data
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            return [obj]
        return obj
    else:
        raise ValueError("Input file must be .json or .jsonl")

def extract_between(text: str, tag: str) -> str:
    import re as _re
    m = _re.search(fr'<{tag}>\s*(.*?)\s*</{tag}>', text, _re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_think(s: str) -> str:
    return extract_between(s, "think")

def extract_answer(s: str) -> str:
    return extract_between(s, "answer")

def normalize_number(num_str: str):
    try:
        return float(num_str.replace(",", ""))
    except Exception:
        return None

def mean_relative_accuracy(pred, target, start=0.5, end=0.95, interval=0.05):
    if not torch.is_tensor(pred):
        pred = torch.tensor(pred, dtype=torch.float32)
    if not torch.is_tensor(target):
        target = torch.tensor(target, dtype=torch.float32)
    eps = 1e-8
    rel_error = torch.abs(pred - target) / (torch.abs(target) + eps)
    thresholds = torch.arange(start, end + interval/2, interval, dtype=torch.float32)
    mra = (rel_error < (1 - thresholds)).float().mean()
    return mra.item()

def reward_fn(sample: dict, model_output: str, question_type: str) -> float:
    try:
        output_ans = extract_answer(model_output)
        if output_ans == '':
            output_ans = model_output
        gt_ans = extract_answer(sample.get("solution", ""))
        if question_type == "multiple choice":
            return 1.0 if output_ans.strip() == gt_ans.strip() else 0.0
        elif question_type == "numerical":
            gt_has_decimal = ("." in gt_ans) or ("," in gt_ans)
            out_has_decimal = ("." in output_ans) or ("," in output_ans)
            if gt_has_decimal != out_has_decimal:
                return 0.0
            gt_number = normalize_number(gt_ans)
            out_number = normalize_number(output_ans)
            if gt_number is None or out_number is None:
                return 0.0
            return 1.0 if round(gt_number, 2) == round(out_number, 2) else 0.0
        elif question_type == "regression":
            gt_number = normalize_number(gt_ans)
            out_number = normalize_number(output_ans)
            if gt_number is None or out_number is None:
                return 0.0
            return mean_relative_accuracy(out_number, gt_number)
        else:
            return 0.0
    except Exception:
        return 0.0

def ensure_abs(p: str) -> str:
    return p if os.path.isabs(p) else os.path.abspath(p)

def load_dataset_config(path: str) -> Dict[str, Dict[str, str]]:
    """Load external config: {name: {'json':'/abs/file.json','video':'/abs/dir'}}"""
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    out = {}
    for k, v in cfg.items():
        out[k] = {
            "json": ensure_abs(v["json"]),
            "video": ensure_abs(v["video"]),
        }
    return out

# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="Evaluation benchmark (absolute paths)")
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model")
    parser.add_argument("--file_name", type=str, required=True, help="Run tag / suffix for output")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="ABSOLUTE directory to save outputs")
    parser.add_argument("--nframes", type=int, default=16, help="Frames per video")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top_p", type=float, default=0.001)
    parser.add_argument("--max_tokens", type=int, default=1024)
    parser.add_argument("--max_model_len", type=int, default=64000)
    parser.add_argument("--gpu_mem_util", type=float, default=0.9)
    parser.add_argument("--datasets", type=str, nargs="+", default=None,
                        help="Subset to run. Default: run ALL datasets in mapping.")
    parser.add_argument("--dataset_config", type=str, default="",
                        help="Optional JSON file to override dataset mapping. "
                             "Format: {name: {'json':'/abs/file.json','video':'/abs/dir'}}")
    args = parser.parse_args()

    MODEL_PATH = ensure_abs(args.model_path)
    OUTPUT_DIR = ensure_abs(args.output_dir)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Default dataset mapping (override with --dataset_config)
    ROOT = os.getenv("EVAL_DATA_ROOT", "")
    if not ROOT:
        print("[WARN] EVAL_DATA_ROOT not set. Use --dataset_config or set the env var.")
    default_mapping: Dict[str, Dict[str, str]] = {
        "holmes":        {"json": f"{ROOT}/valid_data/holmes.json",          "video": f"{ROOT}/Video-Holmes"},
        "lvbench":       {"json": f"{ROOT}/valid_data_old/lvbench_partial.json", "video": f"{ROOT}/LVBench"},
        "longvideobench":{"json": f"{ROOT}/valid_data/longvideobench.json",  "video": f"{ROOT}/LongVideoBench"},
        "mmvu":          {"json": f"{ROOT}/valid_data/mmvu.json",            "video": f"{ROOT}/MMVU"},
        "mvbench":       {"json": f"{ROOT}/valid_data/mvbench.json",         "video": f"{ROOT}/MVBench"},
        "tempcompass":   {"json": f"{ROOT}/valid_data/tempcompass.json",     "video": f"{ROOT}/TempCompass"},
        "vsibench":      {"json": f"{ROOT}/valid_data/vsibench.json",        "video": f"{ROOT}/VSI-Bench"},
        "videommmu":     {"json": f"{ROOT}/valid_data/videommmu.json",       "video": f"{ROOT}/VideoMMMU"},
        "mlvu":          {"json": f"{ROOT}/valid_data/mlvu.json",            "video": f"{ROOT}/MLVU_Test"},
        "videomme":      {"json": f"{ROOT}/valid_data/videomme.json",        "video": f"{ROOT}/Video-MME"},
    }
    for k in list(default_mapping.keys()):
        default_mapping[k]["json"] = ensure_abs(default_mapping[k]["json"])
        default_mapping[k]["video"] = ensure_abs(default_mapping[k]["video"])

    # Optional config override
    if args.dataset_config:
        override = load_dataset_config(args.dataset_config)
        default_mapping.update(override)

    # Run all datasets by default; use --datasets to select a subset
    run_list = args.datasets if args.datasets else list(default_mapping.keys())

    # Initialize LLM
    llm = LLM(
        model=MODEL_PATH,
        tensor_parallel_size=torch.cuda.device_count(),
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_mem_util,
        limit_mm_per_prompt={"image": 1, "video": 1},
    )
    sampling_params = SamplingParams(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        stop_token_ids=[],
    )
    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    tokenizer.padding_side = "left"
    processor.tokenizer = tokenizer

    for name in run_list:
        if name not in default_mapping:
            print(f"[Skip] dataset '{name}' not in mapping; use --dataset_config to add.")
            continue
        json_path = default_mapping[name]["json"]
        video_base = default_mapping[name]["video"]

        if not os.path.exists(json_path):
            print(f"[Skip] JSON not found: {json_path}")
            continue
        if not os.path.isdir(video_base):
            print(f"[Warn] Video base not a directory: {video_base}")

        output_path = os.path.join(OUTPUT_DIR, f"eval_{name}_{args.file_name}_greedy_output.json")

        print(f"\n=== Running dataset: {name} ===")
        print(f"JSON:  {json_path}")
        print(f"VIDEO: {video_base}")
        print(f"OUT:   {output_path}")
        print(f"len frames per video: {args.nframes}")

        data = load_dataset(json_path)
        print(f"Loaded {len(data)} samples from JSON.")
        
        messages = []
        for ex in data:
            if ex.get("problem_type") == "multiple choice":
                question = ex['problem'] + "Options:\n"
                for op in ex["options"]:
                    question += op + "\n"
            else:
                question = ex["problem"]

            video_path = os.path.normpath(os.path.join(video_base, ex["path"]))
            msg = [{
                "role": "user",
                "content": [
                    {
                        "type": ex["data_type"],
                        "video": video_path,
                        "nframes": int(os.environ.get("EVAL_NFRAMES", args.nframes)),
                        "max_pixels": 128 * 28 * 28,
                    },
                    {
                        "type": "text",
                        "text": QUESTION_TEMPLATE.format(Question=question) + TYPE_TEMPLATE[ex['problem_type']]
                    }
                ]
            }]
            messages.append(msg)

        # Resume from checkpoint
        final_output = []
        start_idx = 0
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    final_output = existing.get("results", [])
                    start_idx = len(final_output)
                    print(f"Resuming from sample index {start_idx}")
            except Exception as e:
                print(f"Error reading existing output file: {e}")

        mean_acc, mean_mra = [], []

        for i in tqdm(range(start_idx, len(messages), BSZ), desc=f"[{name}] Batches"):
            batch_messages = messages[i:i + BSZ]
            prompts = [processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                       for m in batch_messages]

            try:
                image_inputs, video_inputs, video_kwargs = process_vision_info(
                    batch_messages, return_video_kwargs=True
                )
                image_idx = 0
                video_idx = 0
                llm_inputs = []

                for idx, _ in enumerate(prompts):
                    mm_type = batch_messages[idx][0]["content"][0]["type"]
                    sample_mm_data = {}
                    sample_video_kw = {}
                    if mm_type == "image":
                        sample_mm_data["image"] = image_inputs[image_idx]
                        image_idx += 1
                    elif mm_type == "video":
                        sample_mm_data["video"] = video_inputs[video_idx]
                        for k, v in video_kwargs.items():
                            sample_video_kw[k] = v[video_idx]
                        video_idx += 1

                    llm_inputs.append({
                        "prompt": prompts[idx],
                        "multi_modal_data": sample_mm_data,
                        "mm_processor_kwargs": sample_video_kw,
                    })

                outputs = llm.generate(llm_inputs, sampling_params=sampling_params)
                batch_output_text = [out.outputs[0].text for out in outputs]

            except Exception as e:
                print("error:", data[i].get("path", "<no-path>"))
                print("Exception:", e)
                batch_output_text = ['<answer>error</answer>'] * len(batch_messages)

            for j, (sample, model_output) in enumerate(zip(data[i:i+BSZ], batch_output_text), start=i):
                think_chain = extract_think(model_output)
                final_ans = extract_answer(model_output) or model_output
                sample["output"] = model_output
                sample["prediction"] = final_ans
                q_type = sample.get("problem_type", "")
                sample["reward"] = reward_fn(sample, model_output, q_type)
                sample["correct"] = True if sample["reward"] == 1.0 else False
                if q_type != "regression":
                    mean_acc.append(sample["reward"])
                else:
                    mean_mra.append(sample["reward"])
                if think_chain:
                    sample["process"] = f"<think>{think_chain}</think>"
                final_output.append(sample)

            # Save intermediate results
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump({"results": final_output}, f, indent=2, ensure_ascii=False)
                print(f"Processed batch {(i - start_idx)//BSZ + 1}, saved {len(final_output)} samples.")
            except Exception as e:
                print(f"Error writing to output file: {e}")

        # Aggregate metrics
        final_acc = {"mean_acc": 0.0, "mean_mra": 0.0}
        if mean_acc:
            final_acc["mean_acc"] = torch.tensor(mean_acc).mean().item()
        if mean_mra:
            final_acc["mean_mra"] = torch.tensor(mean_mra).mean().item()

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({"results": final_output, "final_acc": [final_acc]}, f, indent=2, ensure_ascii=False)
            print(f"Final accuracy saved to {output_path}")
        except Exception as e:
            print(f"Error writing final accuracy to output file: {e}")

        print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()