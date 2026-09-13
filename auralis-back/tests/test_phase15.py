"""Check sample-weighted epoch metrics and their failure behavior."""

import sys
import unittest
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from models.train_model import WeightedHuberLoss, validate_epoch, train_epoch


class Constant(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.bias = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        return self.bias.expand(x.shape[0], 1)


class Phase15Tests(unittest.TestCase):
    def test_partial_batch_is_weighted_by_samples_train_and_validation(self):
        loader = DataLoader(TensorDataset(torch.zeros(3, 1), torch.tensor([[0.], [0.], [3.]])), batch_size=2)
        model = Constant()
        criterion = WeightedHuberLoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
        train = train_epoch(model, loader, criterion, torch.nn.L1Loss(), optimizer, torch.device("cpu"))
        val = validate_epoch(model, loader, criterion, torch.nn.L1Loss(), torch.device("cpu"), mc_passes=1)
        for whl, mae in (train, val):
            self.assertAlmostEqual(mae, 1.0)
            self.assertAlmostEqual(whl, 17.5 / 3)

    def test_nonfinite_epoch_stops(self):
        loader = DataLoader(TensorDataset(torch.zeros(1, 1), torch.tensor([[float("nan")]])))
        with self.assertRaises(FloatingPointError):
            validate_epoch(Constant(), loader, WeightedHuberLoss(), torch.nn.L1Loss(), torch.device("cpu"), mc_passes=1)


if __name__ == "__main__":
    unittest.main()
