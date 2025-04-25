import pandas as pd
import numpy as np


class FeatureEngineer:
    def __init__(self, lookback_window=60):
        self.lookback = lookback_window
        self.scaler = None

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich raw OHLCV data with predictive features without pandas_ta"""
        df = df.copy()

        # 1. Price Transformations (unchanged)
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['close_5ma'] = df['close'].rolling(5).mean()
        df['close_20ma'] = df['close'].rolling(20).mean()

        # 2. Volume Features (unchanged)
        df['volume_ma'] = df['volume'].rolling(5).mean()
        df['volume_change'] = df['volume'].pct_change()

        # 3. Technical Indicators (replacing pandas_ta)
        # RSI implementation
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD implementation
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26  # Just the MACD line (not signal line)

        # Bollinger Bands
        rolling_mean = df['close'].rolling(20).mean()
        rolling_std = df['close'].rolling(20).std()
        df['bollinger_upper'] = rolling_mean + (rolling_std * 2)
        df['bollinger_mid'] = rolling_mean
        df['bollinger_lower'] = rolling_mean - (rolling_std * 2)

        # ATR implementation
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(14).mean()

        # OBV implementation
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

        # VWAP implementation
        cum_vol = df['volume'].cumsum()
        cum_pv = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum()
        df['vwap'] = cum_pv / cum_vol

        # 4. Statistical Features (unchanged)
        df['returns_std_10'] = df['returns'].rolling(10).std()
        df['returns_std_20'] = df['returns'].rolling(20).std()
        df['z_score_20'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std()

        # 5. Target Variables (unchanged)
        df['target_return'] = df['close'].shift(-1) / df['close'] - 1
        df['target_direction'] = np.where(df['target_return'] > 0, 1, 0)

        # Drop NA values created by rolling windows
        df.dropna(inplace=True)

        return df

    def prepare_realtime(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare real-time data with same features as training"""
        return self.add_features(df).iloc[-1:]  # Return only the latest row