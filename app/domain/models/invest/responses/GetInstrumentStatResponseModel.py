from dataclasses import dataclass


@dataclass(frozen=True)
class GetInstrumentStatResponseModel:
    stat_value: float