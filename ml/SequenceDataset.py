import torch


class SequenceDataset(torch.utils.data.Dataset):
    def __init__(self, df, seq_length=16):
        self.data = torch.tensor(df['close_normalized'].values, dtype=torch.float32)
        self.seq_length = seq_length

    def __len__(self):
        return len(self.data) - self.seq_length

    def __getitem__(self, idx):
        x = self.data[idx:idx+self.seq_length].unsqueeze(-1)
        y = self.data[idx+self.seq_length]
        return x, y