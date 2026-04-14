import os
import json
import random
import requests
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForVision2Seq,
    AutoProcessor,
    BitsAndBytesConfig,
    Qwen2VLProcessor,
    Qwen2VLForConditionalGeneration,
    Qwen2_5_VLForConditionalGeneration
)
from trl import (
    ModelConfig,
    ScriptArguments,
    SFTConfig,
    SFTTrainer,
    TrlParser,
    get_kbit_device_map,
    get_peft_config,
)
from accelerate import Accelerator
from qwen_vl_utils import process_vision_info

from datasets import Dataset, DatasetDict

import wandb

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SFTScriptArguments(ScriptArguments):
    video_path: Optional[str] = field(
        default='{}',
        metadata={"help": "Video path config: JSON string for multiple data sources, e.g., '{\"STAR\": \"/path/\"}'"}
    )


def parse_video_path_config(video_path_arg):
    if not video_path_arg or video_path_arg == '{}':
        return {}
    if video_path_arg.startswith('{') and video_path_arg.endswith('}'):
        try:
            return json.loads(video_path_arg)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse video_path as JSON: {video_path_arg}")
            return {}
    return {}


def get_video_path(video_path_config, data_source):
    if isinstance(video_path_config, dict) and data_source in video_path_config:
        return video_path_config[data_source]
    return ""


def get_current_device():
    """Get the current device. For GPU we return the local process index to enable multiple GPU train."""
    return Accelerator().local_process_index if torch.cuda.is_available() else "cpu"


def download_video(url: str, folder: str = '/tmp/videos/') -> str:
    """Download video if not already present locally."""
    filename = url.split("/")[-1]
    local_path = os.path.join(folder, filename)

    if os.path.exists(local_path):
        return local_path

    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return local_path
    except requests.RequestException as e:
        raise Exception(f"Failed to download video: {e}")


def prepare_dataset(example: Dict[str, Any], video_path_config: dict) -> Dict[str, List[Dict[str, Any]]]:
    """Prepare dataset example for train."""

    system_message = (
        "You are an expert video analyst tasked with solving problems based on video content. "
        "When answering a question about a video, you should carefully observe and analyze important visual clues from the videos to answer. "
        "For each important segment you notice, first observe the key visual elements, then analyze their significance using the following format: "
        "specify the time range with `<time>start_time-end_time</time>`, "
        "describe the key visual clues with `<caption>Description of key visual clues</caption>`, "
        "and provide your analysis about what this means with `<think>Your analysis and thoughts about this segment</think>`. "
        "Throughout your analysis, think about the question as if you were a human pondering deeply, "
        "engaging in an internal dialogue using natural thought expressions such as such as 'let me think', 'wait', 'Hmm', 'oh, I see', 'let's break it down', etc, or other natural language thought expressions. "
        "After examining the key visual clues, continue with deeper reasoning that connects your observations to the answer. "
        "Self-reflection or verification in your reasoning process is encouraged when necessary, "
        "though if the answer is straightforward, you may proceed directly to the conclusion. "
        "Finally, conclude by placing your final answer in `<answer> </answer>` tags."
    )

    QUESTION_TEMPLATE = (
        "{Question}\n\n"
        "Please analyze the video carefully by identifying key segments and their important visual clues within "
        "`<time> </time>`, `<caption> </caption>`, `<think> </think>` tags "
        "then conduct deep analysis and reasoning to arrive at your answer to the question, "
        "finally provide only the single option letter (e.g., A, B, C, D, E, F etc.) within the `<answer> </answer>` tags."
        "Follow the format specified in the instructions."
    )

    if example["problem_type"] == 'multiple choice':
        question = example['problem'] + "Options:\n"
        for op in example["options"]:
            question += op + "\n"
    else:
        question = example['problem']

    video_base_path = get_video_path(video_path_config, example['data_source'])
    video_path = os.path.join(video_base_path, example["path"]) if video_base_path else example["path"]

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_message}]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": example['data_type'],
                    "video": video_path,
                    "nframes": 16,
                    "max_pixels": 128 * 28 * 28,
                },
                {
                    "type": "text",
                    "text": QUESTION_TEMPLATE.format(Question=question)
                }
            ]
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": example['process'] + "\n" + example['solution']}]
        }
    ]

    return {"messages": messages}


def collate_fn(examples: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    """Collate batch of examples for train."""
    texts = []
    # video_inputs = []
    # image_inputs = []

    for i, example in enumerate(examples):
        try:
            video_path = None
            for message in example["messages"]:
                if message["role"] == "user":
                    for content in message["content"]:
                        if content.get("type") == "video":
                            video_path = content.get("video")
                            print(f"Processing video: {video_path}")
                            break
            texts.append(processor.apply_chat_template(example["messages"], tokenize=False))
            image_inputs, video_inputs, video_kwargs = process_vision_info(example["messages"],
                                                                           return_video_kwargs=True)

        except Exception as e:
            raise ValueError(f"Failed to process example {i}: {e}")

    inputs = processor(
        text=texts,
        images=image_inputs,
        videos=video_inputs,
        return_tensors="pt",
        padding=True
    )

    labels = inputs["input_ids"].clone()
    labels[labels == processor.tokenizer.pad_token_id] = -100

    # Handle visual tokens based on processor type
    visual_tokens = [151652, 151653, 151656] if isinstance(processor, Qwen2VLProcessor) else [
        processor.tokenizer.convert_tokens_to_ids(processor.image_token)
    ]

    for visual_token_id in visual_tokens:
        labels[labels == visual_token_id] = -100

    inputs["labels"] = labels
    return inputs


if __name__ == "__main__":
    # Parse arguments
    parser = TrlParser((SFTScriptArguments, SFTConfig, ModelConfig))
    script_args, training_args, model_config = parser.parse_args_and_config()
    
    # Parse video path config
    video_path_config = parse_video_path_config(script_args.video_path)

    # Configure train args
    training_args.gradient_checkpointing_kwargs = dict(use_reentrant=False)
    training_args.remove_unused_columns = False
    training_args.dataset_kwargs = {"skip_prepare_dataset": True}

    # Load dataset
    if script_args.dataset_name.endswith('.json') or script_args.dataset_name.endswith('.jsonl'):
        dataset = DatasetDict({"train": Dataset.from_json(script_args.dataset_name)})
    else:
        # Load the dataset
        dataset = load_dataset(script_args.dataset_name, name=script_args.dataset_config)

    # Setup model
    torch_dtype = (
        model_config.torch_dtype
        if model_config.torch_dtype in ["auto", None]
        else getattr(torch, model_config.torch_dtype)
    )

    # Model initialization
    model_kwargs = dict(
        revision=model_config.model_revision,
        trust_remote_code=model_config.trust_remote_code,
        torch_dtype=torch_dtype,
        device_map=get_kbit_device_map(),
    )

    if "Qwen2-VL" in model_config.model_name_or_path:
        model = Qwen2VLForConditionalGeneration.from_pretrained(model_config.model_name_or_path, **model_kwargs)
    elif "Qwen2.5-VL" in model_config.model_name_or_path:
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_config.model_name_or_path, **model_kwargs)
    else:
        model = AutoModelForVision2Seq.from_pretrained(model_config.model_name_or_path, **model_kwargs)

    processor = AutoProcessor.from_pretrained(
        model_config.model_name_or_path,
        trust_remote_code=model_config.trust_remote_code
    )

    # Prepare dataset
    prepared_dataset = [prepare_dataset(example, video_path_config) for example in dataset['train']]

    # Initialize wandb if specified
    if training_args.report_to == "wandb":
        wandb.init(project="video-llm-train")

    # Initialize trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=prepared_dataset,
        data_collator=collate_fn,
        peft_config=get_peft_config(model_config),
        # tokenizer=processor.tokenizer
    )

    # Train model
    trainer.train()

    # Save final model
    trainer.save_model(training_args.output_dir)
    processor.save_pretrained(training_args.output_dir)

    if trainer.accelerator.is_main_process:
        # Restore k,v cache for fast inference
        trainer.model.config.use_cache = True
        trainer.model.config.save_pretrained(training_args.output_dir)

        # Copy missing processor config files to all checkpoints
        import shutil
        import glob
        src_dir = model_config.model_name_or_path
        processor_files = ['preprocessor_config.json', 'chat_template.json']
        checkpoint_dirs = glob.glob(os.path.join(training_args.output_dir, 'checkpoint-*'))
        checkpoint_dirs.append(training_args.output_dir)
        for ckpt_dir in checkpoint_dirs:
            for fname in processor_files:
                src_file = os.path.join(src_dir, fname)
                dst_file = os.path.join(ckpt_dir, fname)
                if os.path.exists(src_file) and not os.path.exists(dst_file):
                    shutil.copy(src_file, dst_file)

    # Cleanup
    del model
    del trainer
    torch.cuda.empty_cache()
    wandb.finish()