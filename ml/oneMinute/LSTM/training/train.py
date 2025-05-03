import torch
import numpy as np

from logging import Logger
from torch.utils.data import DataLoader
from ml.oneMinute.LSTM.training.evaluate import evaluate_model
from ml.dataAugmentation.Normalizer import Normalizer
from ml.oneMinute.LSTM.configuration.LstmConfiguration import LstmConfiguration
from ml.oneMinute.LSTM.configuration.TrainingConfiguration import TrainingConfiguration


def train_model(
    model: torch.nn.Module,
    training_configuration: TrainingConfiguration,
    lstm_configuration: LstmConfiguration,
    train_loader: DataLoader,
    test_loader: DataLoader,
    scaler: Normalizer,
    device: str,
    logger: Logger,
    model_name: str,
    save_best_model: bool = True,
) -> None:
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    best_val_loss = float('inf')
    for epoch in range(training_configuration.epochs):
        model.train()
        train_losses = []

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)

            optimizer.zero_grad()
            predictions = model(xb)
            loss = lstm_configuration.criterion(predictions, yb)
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())

        avg_loss = np.mean(train_losses)
        logger.info(f"Epoch {epoch + 1}/{training_configuration.epochs} --> Train Loss: {avg_loss:.6f}")

        val_metrics = evaluate_model(model, test_loader, scaler, lstm_configuration.criterion, device)

        logger.info(f"\nEpoch {epoch + 1}/{training_configuration.epochs}")
        logger.info(f"Train Loss: {np.mean(train_losses):.6f}")
        logger.info("Validation Metrics:")
        logger.info(f"- Loss: {val_metrics['test_loss']:.6f}")
        logger.info(f"- MAE: ${val_metrics['mae']:.4f}")
        logger.info(f"- RMSE: ${val_metrics['rmse']:.4f}")
        logger.info(f"- R²: {val_metrics['r2']:.4f}")
        logger.info(f"- Direction Accuracy: {val_metrics['direction_accuracy']:.2%}")

        if save_best_model and val_metrics['test_loss'] < best_val_loss:
            best_val_loss = val_metrics['test_loss']

            torch.save(model.state_dict(), f'../savedModels/{model_name}.pth')
            with open(f'../savedModels/{model_name}_normalizer.txt', 'w') as f:
                f.write(f"{scaler.min} {scaler.max}")
            logger.info(f"Saved new best model! Model saved in ../savedModels/{model_name}.pth")