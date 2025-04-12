from app.configuration.Settings import Settings


class SupportedInstrumentsOptions:
    def __init__(self, settings: Settings):
        self.shares = settings.get('SupportedInstruments')['Shares']