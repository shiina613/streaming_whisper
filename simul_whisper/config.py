# This code was originally in simul_whisper/transcriber/simul_whisper.py . It is adapted a lot for SimulStreaming.

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class SimulWhisperConfig:
    '''Options that are common for all simul policies that could be implemented in SimulWhisper.'''
    model_path: str
    language: str = field(default="zh")
    nonspeech_prob: float = field(default=0.6, metadata={"help": "Threshold for no_speech probability. If exceeded, skip output. Lower = more aggressive filtering."})
    audio_min_len: float = 1.0
    decoder_type: Literal["greedy","beam"] = "greedy"
    beam_size: int = 5
    task: Literal["transcribe","translate"] = "transcribe"
    init_prompt: str = field(default=None)
    static_init_prompt: str = field(default=None)
    max_context_tokens: int = field(default=None)

    # Anti-hallucination settings
    max_repeat_tokens: int = field(default=3, metadata={"help": "Max consecutive repeated tokens before stopping. 0 to disable."})
    max_repeat_ngram: int = field(default=4, metadata={"help": "Max repeated n-gram length to detect. 0 to disable."})
    compression_ratio_threshold: float = field(default=2.4, metadata={"help": "If compression ratio exceeds this, likely hallucination. 0 to disable."})
    logprob_threshold: float = field(default=-1.0, metadata={"help": "If avg logprob is below this, likely hallucination. Very negative to disable."})

    logdir: str = field(default="logdir", metadata={"help": "Directory to save audio segments and tokens for debugging purposes."})

@dataclass
class AlignAttConfig(SimulWhisperConfig):
    '''Options specific to the AlignAtt policy.'''
    eval_data_path: str = "tmp"
    segment_length: float = field(default=1.0, metadata = {"help": "in second"})
    frame_threshold: int = 4
    rewind_threshold: int = 200 # in frames. Max value is 1500. Higher value turns rewinds off.
    audio_max_len: float = 5.0
    cif_ckpt_path: str = ""
    never_fire: bool = False
    max_tokens_per_segment: int = field(default=100, metadata={"help": "Max tokens per audio segment. Prevents runaway generation."})