window.FFR_PROJECT = {
  meta: {
    title: "Find, Fix, Reason",
    subtitle: "Context Repair for Video Reasoning",
    venue: "ICML 2026 project page",
    authors: ["Anonymous Authors"],
    summary:
      "FFR repairs failed video-reasoning rollouts with a frozen teacher that supplies minimal evidence patches. The policy stays on-policy, revisits the right spatiotemporal context, and improves without being handed the answer.",
    heroStats: [
      {
        value: "8",
        label: "benchmarks",
        note: "Evaluated across reasoning and general video understanding."
      },
      {
        value: "+8.7",
        label: "average points",
        note: "56.5 vs 47.8 when FFR (GLM-4.5V) is compared with the Video-R1-SFT baseline."
      },
      {
        value: "0%",
        label: "answer leakage",
        note: "Final prompt design eliminates direct and partial leakage in the manual study."
      },
      {
        value: "kappa=0.3",
        label: "best trade-off",
        note: "Best overall average in the patch-tax sensitivity analysis."
      }
    ],
    links: [
      { label: "Paper PDF", url: "./assets/papers/ffr-paper.pdf", style: "primary" },
      { label: "Supplement", url: "./assets/papers/ffr-supplement.pdf", style: "secondary" },
      { label: "Project Page", url: "https://jethrojames.github.io/FFR/", style: "ghost" },
      { label: "GitHub", url: "https://github.com/JethroJames/FFR", style: "ghost" }
    ]
  },
  abstract:
    "Reinforcement learning has improved video reasoning, but existing pipelines either depend on self-exploration that saturates at the model's own capability ceiling, or mix off-policy guidance in ways that complicate optimization. FFR introduces an observation-level intervention: when a rollout fails, a frozen tool-integrated teacher identifies the missing spatiotemporal dependency and returns a minimal evidence patch from the original video. The student then answers again with the added context, and GRPO updates are applied to the repaired trajectory through a robust improvement reward. Across multiple video reasoning and general video benchmarks, this produces consistent accuracy gains while preserving the benefits of on-policy exploration.",
  insights: [
    {
      title: "Intervene only on failure",
      body:
        "The teacher is not used to replace the student trajectory. It is only activated when a rollout is wrong, which keeps the learning signal focused and data-efficient."
    },
    {
      title: "Patch the context, not the answer",
      body:
        "Evidence patches point to frames, temporal markers, or spatial regions. The student still has to look again and reason independently."
    },
    {
      title: "Stay close to GRPO",
      body:
        "FFR plugs into the normal GRPO loop with minimal surgery. The chosen rollout is either the original correct one or the repaired one."
    },
    {
      title: "Optimize for valid outcomes and valid dependencies",
      body:
        "The reward does not just care about the final answer. It also encourages the model to recover the reasoning dependency that the patch was meant to expose."
    }
  ],
  regimes: [
    {
      title: "On-policy only",
      body: "Stable and simple, but eventually limited by the student's own search horizon."
    },
    {
      title: "Hybrid replay",
      body: "Can inject stronger guidance, but replay management and policy mismatch become central concerns."
    },
    {
      title: "Tool-use loops",
      body: "Retrieve more evidence through multi-round search, yet still stay bounded by the smaller model's capability."
    },
    {
      title: "FFR",
      body: "Diagnose the failure once, add a minimal patch, and let the same policy reason again on the repaired context.",
      active: true
    }
  ],
  methodSteps: [
    {
      step: "01",
      title: "Find the missing dependency",
      body:
        "A frozen teacher inspects the failed rollout and determines whether the error is temporal, spatial, or a misconception about the task."
    },
    {
      step: "02",
      title: "Fix with a minimal evidence patch",
      body:
        "The patch can include key frames, temporal markers, and spatial hints, but it is explicitly constrained not to reveal the answer."
    },
    {
      step: "03",
      title: "Reason again under the same question",
      body:
        "The student re-answers using the original prompt plus the patch. GRPO then updates on the chosen rollout, with patch tax controlling over-reliance."
    }
  ],
  metrics: [
    { key: "mmvu", label: "MMVU" },
    { key: "vsibench", label: "VSI-Bench" },
    { key: "videommmu", label: "VideoMMMU" },
    { key: "videoholmes", label: "Video-Holmes" },
    { key: "longvideobench", label: "LongVideoBench" },
    { key: "lvbench", label: "LVBench" },
    { key: "mvbench", label: "MVBench" },
    { key: "tempcompass", label: "TempCompass" }
  ],
  results: {
    comparison: [
      {
        label: "GPT-4o",
        tone: "gold",
        values: { mmvu: 75.4, vsibench: 34.0, videommmu: 61.2, videoholmes: 42.0, longvideobench: 58.5, lvbench: 48.9, mvbench: 64.6, tempcompass: 73.75 }
      },
      {
        label: "GLM-4.5V",
        tone: "accent",
        values: { mmvu: 68.7, vsibench: null, videommmu: 72.4, videoholmes: null, longvideobench: null, lvbench: 53.8, mvbench: 73.0, tempcompass: null }
      },
      {
        label: "Video-R1-SFT",
        tone: "muted",
        values: { mmvu: 61.3, vsibench: 31.8, videommmu: 47.4, videoholmes: 34.6, longvideobench: 47.6, lvbench: 30.7, mvbench: 59.4, tempcompass: 69.2 }
      },
      {
        label: "Video-R1",
        tone: "muted",
        values: { mmvu: 63.8, vsibench: 35.8, videommmu: 52.3, videoholmes: 36.5, longvideobench: 52.7, lvbench: 35.3, mvbench: 63.9, tempcompass: 73.2 }
      },
      {
        label: "FFR (Video-R1)",
        tone: "brand",
        values: { mmvu: 68.5, vsibench: 38.9, videommmu: 54.6, videoholmes: 52.3, longvideobench: 55.3, lvbench: 38.1, mvbench: 68.8, tempcompass: 75.6 }
      },
      {
        label: "VideoRFT-SFT",
        tone: "muted",
        values: { mmvu: 60.5, vsibench: 31.7, videommmu: 48.5, videoholmes: 27.1, longvideobench: 47.3, lvbench: 26.9, mvbench: 57.0, tempcompass: 68.4 }
      },
      {
        label: "VideoRFT",
        tone: "muted",
        values: { mmvu: 68.5, vsibench: 36.8, videommmu: 51.1, videoholmes: 40.0, longvideobench: 52.5, lvbench: 33.9, mvbench: 62.1, tempcompass: 73.7 }
      },
      {
        label: "FFR (VideoRFT)",
        tone: "plum",
        values: { mmvu: 70.1, vsibench: 38.6, videommmu: 54.9, videoholmes: 48.0, longvideobench: 54.9, lvbench: 37.8, mvbench: 68.2, tempcompass: 75.4 }
      }
    ],
    ablation: [
      { label: "Qwen2.5-VL", tone: "muted", values: { mmvu: 59.2, vsibench: 27.7, videommmu: 47.8, videoholmes: 27.8, longvideobench: 43.2, lvbench: 31.6, mvbench: 57.4, tempcompass: 72.2 } },
      { label: "w./ SFT", tone: "muted", values: { mmvu: 61.3, vsibench: 31.8, videommmu: 47.4, videoholmes: 34.6, longvideobench: 47.6, lvbench: 30.7, mvbench: 59.4, tempcompass: 69.2 } },
      { label: "Only w./ vanilla GRPO", tone: "muted", values: { mmvu: 60.3, vsibench: 28.4, videommmu: 42.9, videoholmes: 45.6, longvideobench: 51.9, lvbench: 33.9, mvbench: 60.0, tempcompass: 69.7 } },
      { label: "w./ SFT + w./ vanilla GRPO", tone: "muted", values: { mmvu: 61.3, vsibench: 32.8, videommmu: 43.4, videoholmes: 46.2, longvideobench: 51.2, lvbench: 36.7, mvbench: 61.0, tempcompass: 70.5 } },
      { label: "w./ SFT + w./ T-GRPO", tone: "gold", values: { mmvu: 63.8, vsibench: 35.8, videommmu: 52.3, videoholmes: 36.5, longvideobench: 52.7, lvbench: 35.3, mvbench: 63.9, tempcompass: 73.2 } },
      { label: "w./ FFR (no visual context)", tone: "accent", values: { mmvu: 64.4, vsibench: 36.6, videommmu: 54.0, videoholmes: 42.3, longvideobench: 51.6, lvbench: 36.7, mvbench: 60.8, tempcompass: 73.4 } },
      { label: "w./ FFR (no GT reference)", tone: "accent", values: { mmvu: 63.7, vsibench: 38.4, videommmu: 51.3, videoholmes: 44.7, longvideobench: 54.4, lvbench: 38.0, mvbench: 62.6, tempcompass: 75.4 } },
      { label: "Full model", tone: "brand", values: { mmvu: 68.5, vsibench: 38.9, videommmu: 54.6, videoholmes: 52.3, longvideobench: 55.3, lvbench: 38.1, mvbench: 68.8, tempcompass: 75.6 } }
    ],
    teacher: [
      { label: "Video-R1-SFT", tone: "muted", values: { mmvu: 61.3, vsibench: 31.8, videommmu: 47.4, videoholmes: 34.6, longvideobench: 47.6, lvbench: 30.7, mvbench: 59.4, tempcompass: 69.2, avg: 47.8 } },
      { label: "FFR-Qwen3-32B", tone: "gold", values: { mmvu: 67.9, vsibench: 38.5, videommmu: 50.5, videoholmes: 47.8, longvideobench: 52.6, lvbench: 34.2, mvbench: 68.3, tempcompass: 72.2, avg: 54.0 } },
      { label: "FFR-Qwen3-235B", tone: "plum", values: { mmvu: 68.2, vsibench: 38.1, videommmu: 56.5, videoholmes: 51.6, longvideobench: 54.2, lvbench: 33.9, mvbench: 68.8, tempcompass: 75.2, avg: 55.8 } },
      { label: "FFR-GPT-4o", tone: "accent", values: { mmvu: 69.0, vsibench: 38.5, videommmu: 55.4, videoholmes: 49.2, longvideobench: 53.9, lvbench: 36.3, mvbench: 70.0, tempcompass: 74.9, avg: 55.9 } },
      { label: "FFR-GLM-4.5V", tone: "brand", values: { mmvu: 68.5, vsibench: 38.9, videommmu: 54.6, videoholmes: 52.3, longvideobench: 55.3, lvbench: 38.1, mvbench: 68.8, tempcompass: 75.6, avg: 56.5 } }
    ],
    sensitivity: [
      { label: "kappa=0.1", kappa: 0.1, tone: "gold", values: { mmvu: 72.7, vsibench: 38.7, videommmu: 49.0, videoholmes: 44.3, longvideobench: 53.6, lvbench: 42.0, mvbench: 61.2, tempcompass: 73.6, avg: 54.4 } },
      { label: "kappa=0.3", kappa: 0.3, tone: "brand", values: { mmvu: 68.5, vsibench: 38.9, videommmu: 54.6, videoholmes: 52.3, longvideobench: 55.3, lvbench: 38.1, mvbench: 68.8, tempcompass: 75.6, avg: 56.5 } },
      { label: "kappa=0.5", kappa: 0.5, tone: "accent", values: { mmvu: 69.3, vsibench: 42.8, videommmu: 47.3, videoholmes: 44.2, longvideobench: 52.4, lvbench: 37.6, mvbench: 60.6, tempcompass: 73.8, avg: 53.5 } },
      { label: "kappa=0.7", kappa: 0.7, tone: "plum", values: { mmvu: 68.5, vsibench: 39.3, videommmu: 47.0, videoholmes: 45.2, longvideobench: 54.8, lvbench: 37.2, mvbench: 61.8, tempcompass: 73.5, avg: 53.4 } },
      { label: "kappa=1.0", kappa: 1.0, tone: "muted", values: { mmvu: 70.6, vsibench: 40.4, videommmu: 47.9, videoholmes: 43.0, longvideobench: 57.8, lvbench: 35.8, mvbench: 60.8, tempcompass: 75.4, avg: 54.0 } }
    ],
    leakage: [
      { label: "No constraints", direct: 15.5, partial: 24.0, total: 39.5 },
      { label: "+ output format constraints", direct: 6.0, partial: 13.5, total: 19.5 },
      { label: "+ negative prompt", direct: 1.5, partial: 4.0, total: 5.5 },
      { label: "+ both (final design)", direct: 0.0, partial: 0.0, total: 0.0 }
    ],
    stages: [
      { label: "Early", intervention: 26.3, accuracy: 77.5 },
      { label: "Mid", intervention: 27.0, accuracy: 79.8 },
      { label: "Late", intervention: 13.7, accuracy: 80.2 }
    ]
  },
  cases: [
    {
      id: "star-book",
      kind: "pipeline",
      tag: "STAR dataset",
      title: "Put-down object: from visible clutter to the actual release event",
      principle: "The patch does not say 'the answer is B'. It redirects attention to the hand-release moment and the relevant frame window.",
      image: "./assets/figures/figure-3-case-study.png",
      question: "Which object was put down by the person?",
      options: ["A. The clothes", "B. The book", "C. The shoe", "D. The dish"],
      original: {
        title: "Student's original rollout",
        answer: "A. The clothes",
        text: "The model over-focused on clothes that stay visible across many frames and treated salience as evidence for the put-down action."
      },
      evidence: {
        title: "Teacher evidence patch",
        error: ["temporal error", "spatial error"],
        keyFrames: ["13", "14", "15"],
        temporalMarkers: ["when the person's hand releases the object", "moment of placement on surface"],
        guidance: "Track hand movements and determine which object transitions from being held to being placed down."
      },
      corrected: {
        title: "Corrected rollout",
        answer: "B. The book",
        text: "After revisiting the key frames, the student identifies that the book, not the clothes, is the object whose state actually changes from held to placed."
      }
    },
    {
      id: "guardrail-counting",
      kind: "guardrail",
      tag: "Leakage-safe guidance",
      title: "Counting case: point to evidence, do not encode the answer",
      principle: "A good patch sends the student back to the right frames. A bad patch turns the patch itself into the answer.",
      question: "How many subjects appear in the relevant frame range?",
      bad: "There are exactly 3 people in frame 15.",
      good: "Recount the subjects within the frame range [13, 17].",
      takeaway: "The safe version preserves the need for observation. The student still has to inspect the video and count."
    },
    {
      id: "guardrail-temporal",
      kind: "guardrail",
      tag: "Leakage-safe guidance",
      title: "Temporal case: specify the relation, not the solution",
      principle: "Temporal hints should expose the relevant dependency without narrating the event sequence for the student.",
      question: "What is the key temporal relation that resolves the mistake?",
      bad: "The event happens before the person sits down.",
      good: "Examine the temporal relationship and causal sequence between the two identified events.",
      takeaway: "The safe prompt names the type of dependency to re-check, but avoids stating the ordering itself."
    },
    {
      id: "guardrail-attribute",
      kind: "guardrail",
      tag: "Leakage-safe guidance",
      title: "Attribute case: redirect attention without naming the attribute",
      principle: "Directly observable attributes are especially risky because a single leaked detail can collapse the whole learning problem.",
      question: "Which visual attribute should the student revisit?",
      bad: "The object being picked up is a red metal cube.",
      good: "Observe the visual features (color/material) of the object involved in the interaction.",
      takeaway: "The patch says what kind of evidence matters, but not which attribute value wins."
    }
  ],
  bibtex: [
    "@inproceedings{ffr2026,",
    "  title={Find, Fix, Reason: Context Repair for Video Reasoning},",
    "  booktitle={ICML},",
    "  year={2026}",
    "}"
  ].join("\n")
};
