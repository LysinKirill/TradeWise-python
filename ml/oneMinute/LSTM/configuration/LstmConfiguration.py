import json
from dataclasses import dataclass

@dataclass(frozen=True)
class LstmConfiguration:
    input_size: int
    hidden_layer_size: int
    num_layers: int
    output_size: int = 1
    dropout: float = 0.0

    @classmethod
    def from_json(cls, json_str: str):
        if json_str is None:
            return None
        config_dict = json.loads(json_str)
        return cls(**config_dict)

