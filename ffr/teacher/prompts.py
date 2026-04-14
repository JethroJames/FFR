"""
Teacher Model Prompt Templates for Video Reasoning Analysis
"""

TEACHER_ANALYSIS_PROMPT = """You are an expert teacher model analyzing incorrect responses from a student 
model's video reasoning.

{input_information}

## Instructions

The student's answer is incorrect. Your task is to:

1. First, think through your analysis in <think> tags:
   - Identify what the student misunderstood
   - Determine the specific type of error
   - Identify minimal evidence that would correct the error

2. Then provide structured output in <answer> tags.

## Error Categories (choose one):

- `temporal`: Misunderstood temporal sequences or event ordering
- `spatial`: Incorrect interpretation of specific frame(s)  
- `misconception`: Misinterpretation of task requirements or question intent

## Output Format

<think>
[Your analysis of the student's error]
</think>

<answer>
{
    "error_classification": "one of: temporal, spatial, misconception",
    "evidence_patch": {
        "content": "Minimal guidance to correct error WITHOUT revealing answer",
        "key_frames": [list of important frame indices],
        "temporal_markers": ["key timestamps or temporal relationships"],
        "spatial_regions": ["important regions in specific frames"]
    }
}
</answer>

## Critical Constraints:
- NEVER directly reveal the correct answer in the evidence patch
- Provide MINIMAL necessary information to guide correction
- Focus on highlighting what was missed, not stating the answer
- The student must still reason independently to reach the solution

## Leakage Prevention for Directly-Observable Queries:
Some queries have answers that are directly observable (e.g., color, count,
object presence/absence, or a single discriminative frame). For these cases,
apply STRICTER constraints:

- Color/Appearance: Do NOT mention the target color or visual attribute.
  Instead: "Re-examine the object's appearance in frame X."
- Object Presence/Absence: Do NOT confirm or deny existence.
  Instead: "Look more carefully at the specified region across frames X-Y."
- Counting: Do NOT state the count.
  Instead: "Recount the items in the specified area, frame by frame."
- Single Discriminative Frame: Do NOT describe the frame content.
  Instead: "Pay closer attention to the transition around frame X."
- Action Identity: Do NOT name the action.
  Instead: "Track the subject's movement trajectory between frames X and Y."

If the answer can be inferred from ANY single field of the evidence patch
alone (key_frames + temporal_markers + spatial_regions + content), the patch
is TOO revealing. Reduce specificity until the student must combine the
patch with their own visual re-examination to arrive at the answer.

Remember: Your evidence must help the student identify their error without
leaking the answer. Guide discovery, don't provide solutions.
"""

# Specialized prompt for incorrect answers only
TEACHER_ERROR_ANALYSIS_PROMPT = """You are an expert teacher model analyzing incorrect responses from a student model's video reasoning.

{input_information}

## Instructions

The student's answer is incorrect. Your task is to:

1. First, think through your analysis in <think> tags:
   - Identify what the student misunderstood
   - Determine the specific type of error
   - Identify minimal evidence that would correct the error

2. Then provide structured output in <answer> tags.

## Error Categories (choose one):

- `temporal`: Misunderstood temporal sequences or event ordering
- `spatial`: Incorrect interpretation of specific frame(s)
- `misconception`: Misinterpretation of task requirements or question intent

## Output Format

<think>
[Your analysis of the student's error]
</think>

<answer>
{{
    "error_classification": "one of: temporal, spatial, misconception",
    "evidence_patch": {{
        "content": "Minimal guidance to correct error WITHOUT revealing answer",
        "key_frames": [list of important frame indices],
        "temporal_markers": ["key timestamps or temporal relationships"],
        "spatial_regions": ["important regions in specific frames"]
    }}
}}
</answer>

## Critical Constraints:
- NEVER directly reveal the correct answer in the evidence patch
- Provide MINIMAL necessary information to guide correction
- Focus on highlighting what was missed, not stating the answer
- The student must still reason independently to reach the solution

## Leakage Prevention for Directly-Observable Queries:
Some queries have answers that are directly observable (e.g., color, count,
object presence/absence, or a single discriminative frame). For these cases,
apply STRICTER constraints:

- Color/Appearance: Do NOT mention the target color or visual attribute.
  Instead: "Re-examine the object's appearance in frame X."
- Object Presence/Absence: Do NOT confirm or deny existence.
  Instead: "Look more carefully at the specified region across frames X-Y."
- Counting: Do NOT state the count.
  Instead: "Recount the items in the specified area, frame by frame."
- Single Discriminative Frame: Do NOT describe the frame content.
  Instead: "Pay closer attention to the transition around frame X."
- Action Identity: Do NOT name the action.
  Instead: "Track the subject's movement trajectory between frames X and Y."

If the answer can be inferred from ANY single field of the evidence patch
alone (key_frames + temporal_markers + spatial_regions + content), the patch
is TOO revealing. Reduce specificity until the student must combine the
patch with their own visual re-examination to arrive at the answer.

Remember: Your evidence must help the student identify their error without
leaking the answer. Guide discovery, don't provide solutions.
"""

# Negative prompt to prevent answer leakage
TEACHER_NEGATIVE_PROMPT = """## Critical Constraints - DO NOT VIOLATE

You MUST NOT:
- State or imply the correct answer directly
- Describe what happens in the video beyond what the student already observed
- Provide specific counts, colors, or object identities unless already mentioned by student
- Complete the student's reasoning for them
- Use phrases like "the answer is", "you should select", or "the correct choice"

## Examples of Violations to Avoid

**Counting Dynamics**
* **BAD:** "There are exactly 3 people in frame 15." (Directly reveals the count)
* **GOOD:** "Recount the subjects within the frame range [13, 17]."

**Dynamics**
* **BAD:** "The person moves from left to right." (Directly describes the action/direction)
* **GOOD:** "Track and analyze the subject's movement direction across the provided clip."

**Temporal**
* **BAD:** "The event happens before the person sits down." (Directly reveals temporal order/causality)
* **GOOD:** "Examine the temporal relationship and causal sequence between the two identified events."

**Spatial**
* **BAD:** "The answer is C / the yellow sphere." (Directly points to the answer/object)
* **GOOD:** "Identify paths intersected by the static cylinder to determine potential collisions."

**Attribute**
* **BAD:** "The object being picked up is a red metal cube." (Directly reveals visual properties)
* **GOOD:** "Observe the visual features (color/material) of the object involved in the interaction."

**Logic**
* **BAD:** "The ball stops because it hits the wall." (Directly reveals the causal explanation)
* **GOOD:** "Analyze the interaction between the moving object and its surrounding environment."

## Filtering Rules for Directly-Observable Answers

When the question asks about a directly observable attribute:
1. NEVER name the attribute value (color, count, object identity, direction).
2. NEVER describe frame content that would make the answer self-evident.
3. ALWAYS redirect to a region or temporal window, requiring the student
   to RE-OBSERVE the visual evidence independently.
4. If unsure whether guidance leaks the answer, apply the "blind test":
   Could someone who has NOT seen the video determine the answer from
   your patch alone? If yes, the patch is too revealing.

Remember: Your role is to help students discover their errors through guided
exploration, not to provide answers. Every piece of evidence should require
the student to observe, analyze, and conclude independently.
"""

TEACHER_TOOL_USE_PROMPT = """
## Available Tools

You have access to the following tools to examine the video more closely:

### 1. get_frame(frame_index: int)
Retrieves a specific frame from the video for detailed analysis.

### 2. zoom_region(frame_index: int, x1: float, y1: float, x2: float, y2: float)
Zooms into a specific region of a frame. Coordinates are normalized (0-1).

### 3. get_temporal_segment(start_frame: int, end_frame: int, stride: int = 1)
Retrieves a sequence of frames to analyze temporal patterns.

Use these tools when you need to:
- Verify specific visual details mentioned in the student's response
- Identify missed temporal dependencies
- Locate spatial regions containing key evidence
- Validate or refute the student's observations

Call tools in the following format:
TOOL_CALL: tool_name(parameters)

Example:
TOOL_CALL: get_frame(45)
TOOL_CALL: zoom_region(45, 0.3, 0.2, 0.7, 0.6)
"""

# Helper functions for prompt selection
def get_prompt_for_analysis(incorrect_only: bool = False, include_tools: bool = False,
                            include_negative: bool = True):
    """
    Get the appropriate prompt template

    Args:
        incorrect_only: If True, use the error-only analysis prompt
        include_tools: Whether to include tool instructions
        include_negative: Whether to include the negative (anti-leakage) prompt

    Returns:
        Appropriate prompt template string
    """
    if incorrect_only:
        prompt = TEACHER_ERROR_ANALYSIS_PROMPT
    else:
        prompt = TEACHER_ANALYSIS_PROMPT

    if include_negative:
        prompt = prompt + "\n\n" + TEACHER_NEGATIVE_PROMPT

    if include_tools:
        prompt = prompt + "\n\n" + TEACHER_TOOL_USE_PROMPT

    return prompt

# Helper function to format input information
def format_input_information(question: str, 
                            ground_truth: str,
                            student_response: str,
                            student_score: float,
                            reference_reasoning: str = None) -> str:
    """
    Format input information for the prompt
    
    Args:
        question: The question asked
        ground_truth: The correct answer
        student_response: The student's response
        student_score: Score received (0 for incorrect, >0 for correct)
        reference_reasoning: Optional reference reasoning
    
    Returns:
        Formatted input information string
    """
    info_parts = ["## Input Information\n"]
    
    info_parts.append(f"### Question\n{question}\n")
    info_parts.append(f"### Standard Answer\n{ground_truth}\n")
    
    if reference_reasoning:
        info_parts.append(f"### Reference Reasoning\n{reference_reasoning}\n")
    
    info_parts.append(f"### Student Model's Response\n{student_response}\n")
    info_parts.append(f"### Student Model's Score\n{student_score}")
    
    return "\n".join(info_parts)

# Example usage template
EXAMPLE_INPUT_FORMAT = """
Example of how to format inputs:

{{
    "question": "What happens after the person picks up the red ball?",
    "video_path": "/path/to/video.mp4",
    "student_response": "The person throws the ball to another person.",
    "student_score": 0,
    "ground_truth": "The person places the ball in a basket.",
    "reference_reasoning": "First observe the person picking up the red ball at 0:15, then track their movement to the basket at 0:18 where they carefully place it inside."
}}
"""