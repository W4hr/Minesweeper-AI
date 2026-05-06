import torch
import torch.nn as nn
import torch.optim as optim
from torch import flatten, tensor, float32
import numpy as np
from minesweeper.interactive import MinesweeperAPI

class MinesweeperCNN(nn.Module):
	def __init__(self, radius, in_channels = 1):
		"""
		Parameters
		----------
		`in_channels` : int 
		1 for raw; len(ENCODE_VALUES) for one-hot
		"""
		super().__init__()
		input_side = 2 * radius + 1

		conv1_kernel_size = radius
		conv2_kernel_size = max(radius - 1, 3)
		conv3_kernel_size = max(radius - 2, 3)

		def conv_out(side: int, kernel: int) -> int:
			return side - kernel + 1

		s1 = conv_out(input_side, conv1_kernel_size)
		s2 = conv_out(s1, conv2_kernel_size)
		s3 = conv_out(s2, conv3_kernel_size)
		if s3 <= 0:
			raise ValueError(
				f"Invalid CNN geometry for radius={radius}: final side is {s3}. "
				"Adjust kernel sizes or radius."
			)

		self.conv1 = nn.Conv2d(in_channels=in_channels, out_channels=16, kernel_size=conv1_kernel_size)
		self.relu1 = nn.ReLU()
		self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=conv2_kernel_size)
		self.relu2 = nn.ReLU()
		self.conv3 = nn.Conv2d(in_channels=32, out_channels=8, kernel_size=conv3_kernel_size)
		self.relu3 = nn.ReLU()
		self.fc = nn.Linear(in_features=8 * s3 * s3, out_features=1)
			
	def forward(self, x):
		x = self.conv1(x)
		x = self.relu1(x)

		x = self.conv2(x)
		x = self.relu2(x)

		x = self.conv3(x)
		x = self.relu3(x)

		x = flatten(x, 1)
		x = self.fc(x)
		
		return x

class MinesweeperCNNClassifier:
	def __init__(self, radius, in_channels, epochs, lr = 0.001, batch_size = 1):
		self.radius = radius
		self.in_channels = in_channels
		self._net = MinesweeperCNN(radius, in_channels)
		self._bce = nn.BCEWithLogitsLoss()
		self._epochs = epochs
		self._lr = lr
		self._batch_size = batch_size

	def _to_tensor(self, X):
		if self.in_channels == 1:
			arr = np.asarray(X, dtype=np.float32)
			return torch.from_numpy(arr).unsqueeze(1)
		else:
			arr = np.asarray(X, dtype=np.float32)
			if arr.ndim == 2:
				arr = self._reshape_flat_to_matrix(arr)
			transposed = arr.transpose(0, 3, 1, 2)
			return torch.from_numpy(transposed)

	def _reshape_flat_to_matrix(self, X):
		"""Reshape flat one-hot features (N, features) to matrix (N, H, W, C).
		Strips any trailing additional_data features beyond the spatial neighborhood."""
		neighborhood_size = 2 * self.radius + 1
		spatial_features = neighborhood_size * neighborhood_size * self.in_channels
		N = X.shape[0]
		C = self.in_channels
		# Extract only spatial features, discard additional_data like bomb_count
		X_spatial = X[:, :spatial_features]
		return X_spatial.reshape(N, neighborhood_size, neighborhood_size, C)

	def fit(self, X, y):
		X_t = self._to_tensor(X)
		y_t = torch.tensor(y, dtype=torch.float32)

		optimizer = optim.Adam(self._net.parameters(), lr=self._lr)
		dataset = torch.utils.data.TensorDataset(X_t, y_t)
		loader = torch.utils.data.DataLoader(dataset, batch_size=self._batch_size, shuffle=True)

		self._net.train()
		for _ in range(self._epochs):
			for xb, yb in loader:
				optimizer.zero_grad()
				logits = self._net(xb).squeeze(-1)
				loss = self._bce(logits, yb)
				loss.backward()
				optimizer.step()

	def predict_proba(self, X):
		self._net.eval()
		with torch.no_grad():
			logits = self._net(self._to_tensor(X)).squeeze(-1).cpu().numpy()
			logits = np.atleast_1d(logits)
			probs = 1 / (1 + np.exp(-logits))
			return np.stack([1 - probs, probs], axis=1)
		
	def predict(self, X):
		return (self.predict_proba(X)[:,1] >= 0.5).astype(int)

