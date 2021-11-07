import os
import pandas as pd
import torch
import torch.nn as nn
import torchvision.transforms as T
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision.transforms import ToTensor
from torchvision.io import read_image
import matplotlib.pyplot as plt


# Creating a Custom Dataset for your files
class CustomImageDataset(Dataset):
    def __init__(self, annotations_file, img_dir, transform=None, target_transform=None):
        self.img_labels = pd.read_csv(annotations_file)
        self.img_dir = img_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = read_image(img_path)
        label = self.img_labels.iloc[idx, 1]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label


train_csvdir = '.\\train.csv'
train_imgdir = '.\\TrainSet'
img_transform = nn.Sequential(
            T.Resize([224,224]),
            T.ConvertImageDtype(torch.float)
        )
training_data = CustomImageDataset(train_csvdir,train_imgdir, transform=img_transform)

# Preparing your data for training with DataLoaders
from torch.utils.data import DataLoader
train_dataloader = DataLoader(training_data, batch_size=8, shuffle=True)

# Iterate through the DataLoader
train_features, train_labels = next(iter(train_dataloader))
print(f"Feature batch shape: {train_features.size()}")
print(f"Labels batch shape: {train_labels.size()}")
img = train_features[0].squeeze()
label = train_labels[0]
plt.imshow(img.permute((1,2,0)), cmap="gray")
plt.show()
print(f"Label: {label}")

print(img.dtype)