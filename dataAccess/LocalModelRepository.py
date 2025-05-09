import json
from typing import Any
import torch
from pathlib import Path
from datetime import datetime
import numpy as np
from dataAccess.interfaces.IModelRepository import IModelRepository
from dataAccess.models.model.GetAllModelsInfo import GetAllModelsInfo
from dataAccess.models.model.GetModelResponse import GetModelResponse
from dataAccess.models.model.ShortModelInfo import ShortModelInfo


class LocalModelRepository(IModelRepository):
    def __init__(self, base_dir: str = "./ml/savedModels"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def get_all_models_info(self) -> GetAllModelsInfo:
        models = []
        for config_file in self.base_dir.glob("*_config.json"):
            model_name = config_file.name.replace("_config.json", "")

            with open(config_file, "r") as f:
                config = json.load(f)

            models.append(ShortModelInfo(
                id=config.get("id"),
                instrument_id=config.get("instrument_id", ""),
                name=model_name,
                model_type=config.get("model_type", "UNKNOWN"),
                created_at=datetime.fromisoformat(config["created_at"])
            ))

        return GetAllModelsInfo(models=models)

    async def get_model(
            self,
            model_id: str,
            model_for_init: torch.nn.Module
    ) -> GetModelResponse | None:
        all_model_infos = await self.get_all_models_info()
        models_with_id = list(filter(lambda m: m.id == model_id, all_model_infos.models))
        if len(models_with_id) != 0:
            return None

        model_name = models_with_id[0].name

        model_path = self.base_dir / f"{model_name}_LAST.pth"
        config_path = self.base_dir / f"{model_name}_config.json"

        if not model_path.exists() or not config_path.exists():
            return None

        model = model_for_init
        model.load_state_dict(torch.load(model_path))

        with open(config_path, "r") as f:
            config = json.load(f)


        if "created_at" in config:
            config["created_at"] = datetime.fromisoformat(config["created_at"])

        return GetModelResponse(
            id=config.get("id"),
            instrument_id=config.get("instrument_id", ""),
            name=model_name,
            model_type=config.get("model_type", "LSTM"),
            created_at=config.get("created_at", datetime.now()),
            model=model,
            config=config
        )

    async def add_model(
            self,
            instrument_id: str,
            name: str,
            model_type: str,
            model: torch.nn.Module,
            configuration: Any | None = None
    ) -> int:
        torch.save(model.state_dict(), self.base_dir / f"{name}_LAST.pth")

        config = {
            "instrument_id": instrument_id,
            "model_type": model_type,
            "created_at": datetime.now().isoformat(),
            **(configuration or {})
        }

        with open(self.base_dir / f"{name}_config.json", "w") as f:
            json.dump(config, f, indent=4)

        return hash(name)

    @staticmethod
    def _convert_config_types(config: dict) -> dict:
        if "normalizer_mins" in config:
            config["normalizer_mins"] = np.array(config["normalizer_mins"])
        if "normalizer_maxs" in config:
            config["normalizer_maxs"] = np.array(config["normalizer_maxs"])
        return config