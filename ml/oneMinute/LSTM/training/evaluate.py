from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import torch
import numpy as np


def denormalize(predictions, scaler):
    return scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()


def evaluate_model(
        model,
        loader,
        scaler,
        criterion,
        device):
    model.eval()
    all_predictions = []
    all_targets = []
    test_losses = []

    with torch.no_grad():
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            batch_predictions = model(xb)
            loss = criterion(batch_predictions, yb)
            test_losses.append(loss.item())

            all_predictions.append(batch_predictions.cpu().numpy())
            all_targets.append(yb.cpu().numpy())

    predictions = np.concatenate(all_predictions)
    targets = np.concatenate(all_targets)

    original_predictions = denormalize(predictions, scaler)
    original_targets = denormalize(targets, scaler)

    metrics = {
        'test_loss': np.mean(test_losses),
        'mae': mean_absolute_error(original_targets, original_predictions),
        'rmse': np.sqrt(mean_squared_error(original_targets, original_predictions)),
        'r2': r2_score(original_targets, original_predictions),
        'direction_accuracy': (np.sign(original_predictions[1:] - original_targets[:-1]) ==
                              np.sign(original_targets[1:] - original_targets[:-1])).mean()
    }
    return metrics