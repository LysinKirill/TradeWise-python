class AssetAllocation:
    def __init__(
            self,
            asset_allocation: dict[str, float]
    ):
        if sum(asset_allocation.values()) > 1:
            raise ValueError("Sum of asset allocations cannot exceed 1!")
        self.asset_allocation = asset_allocation

    def get_asset_allocation(
            self,
            instrument_id: str
    ) -> float | None:
        return self.asset_allocation.get(instrument_id)