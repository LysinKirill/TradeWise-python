import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FullModelInfo:
    id: int | None
    instrument_id: str
    name: str
    model_type: str
    created_at: datetime
    model_configuration: dataclass
    normalizer_mins: list[float]
    normalizer_maxs: list[float]


    @classmethod
    def from_json(cls, json_str: str):
        if json_str is None:
            return None
        config_dict = json.loads(json_str)
        return cls(**config_dict)

