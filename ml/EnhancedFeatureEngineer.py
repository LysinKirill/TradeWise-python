from ml.FeatureEngineer import FeatureEngineer
import numpy as np


def create_better_target(df, future_minutes=30, thresholds=(0.002, 0.0025)):
    """
    Creates multi-class target based on future price movement
    thresholds: (small_change_threshold, significant_change_threshold)
    Returns: DataFrame with new target column
    """
    future_pct_change = (df['close'].shift(-future_minutes) / df['close'] - 1)

    conditions = [
        (future_pct_change < -thresholds[1]),  # Significant decrease
        (future_pct_change < -thresholds[0]),  # Decrease
        (abs(future_pct_change) <= thresholds[0]),  # No change
        (future_pct_change > thresholds[0]),  # Increase
        (future_pct_change > thresholds[1])  # Significant increase
    ]

    df['target_class'] = np.select(conditions, [0, 1, 2, 3, 4], default=2)
    return df.dropna()

class EnhancedFeatureEngineer(FeatureEngineer):
    def add_features(self, df):
        df = super().add_features(df)

        # Add momentum features
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_15'] = df['close'] / df['close'].shift(15) - 1

        # Add volatility features
        df['volatility_30'] = df['returns'].rolling(30).std()

        # Add liquidity features
        df['spread_pct'] = (df['high'] - df['low']) / df['close']

        return create_better_target(df)