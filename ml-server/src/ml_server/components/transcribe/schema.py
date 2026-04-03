from pydantic import BaseModel
from typing import Literal

class StartMetadata(BaseModel):
    type: Literal["start"]
    sample_rate: Literal[16000]
    channels: Literal[1]
    encoding: Literal["pcm_s16le"]
    
class EndMetadata(BaseModel):
    type: Literal["end"]