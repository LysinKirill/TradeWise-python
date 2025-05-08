import torch
import numpy as np

class SequenceDataset(torch.utils.data.Dataset):
    def __init__(self, df, seq_length=16):
        self.data = torch.tensor(np.stack(df['normalized_features'].values), dtype=torch.float32)
        self.seq_length = seq_length

    def __len__(self):
        return len(self.data) - self.seq_length

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length, 0]  # Close price is at index 3
        return x, y