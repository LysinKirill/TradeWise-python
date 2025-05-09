from dataclasses import dataclass

@dataclass(frozen=True)
class LstmConfiguration:
    input_size: int
    hidden_layer_size: int
    num_layers: int
    output_size: int = 1
    dropout: float = 0.0

