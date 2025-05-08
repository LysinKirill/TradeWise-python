import torch.nn as nn

from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration


class StockPriceLstm(nn.Module):
    def __init__(
            self,
            configuration: LstmConfiguration,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=configuration.input_size,
            hidden_size=configuration.hidden_layer_size,
            num_layers=configuration.num_layers,
            dropout=configuration.dropout,
            batch_first=True
        )
        self.fc = nn.Linear(configuration.hidden_layer_size, configuration.output_size)

        for name, param in self.lstm.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0.0)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out.view(-1)