import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torchvision import transforms
import torchvision.transforms as T
from torch.utils.data import Dataset
import torchvision
from torchvision import datasets
from torchvision.transforms import ToTensor
from torchvision.io import read_image
import time

from optparse import OptionParser

def args_train():
    # Training Parameters
    parser = OptionParser()
    # Name of the Project
    parser.add_option('--model', dest='model', default='CNN_vgg', type=str, help='type of the model')
    parser.add_option('--mode', type=str, default='dummy')
    parser.add_option('--port', type=str, default='dummy')
    (options, args) = parser.parse_args()
    return options

def print_num_of_parameters(net):
    model_parameters = filter(lambda p: p.requires_grad, net.parameters())
    print('Number of parameters: ' + str(sum([np.prod(p.size()) for p in model_parameters])))


def classification_accuracy(test_loader, model):
    with torch.no_grad():
        correct = 0
        total = 0

        for images, labels in test_loader:
            outputs = model(images)

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum()
        accuracy = correct.numpy() / total
        return accuracy

# Creating a Custom Dataset for your files
class CustomImageDataset(Dataset):
    def __init__(self, annotations_file, img_dir, transform, target_transform=None):
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

class CNN_vgg(nn.Module):
    def __init__(self, pretrained):
        super(CNN_vgg, self).__init__()
        self.features = torchvision.models.vgg16(pretrained=pretrained).features
        classifier = torchvision.models.vgg16(pretrained=pretrained).classifier
        classifier[-1] = nn.Linear(4096, 2, bias=True)
        self.classifier = classifier

        for par in list(self.features.parameters()):
            par.requires_grad = False

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.shape[0], -1)
        x = self.classifier(x)
        return x

def train(model, args, train_loader, test_loader, loss_function, optimizer):
    """
    model: model you are using
    args: arguments of training
    train_loader: dataloader for training data
    test_loader: dataloader of test data
    loss_function: loss function
    optimizer: optimizer used for the training
    """
    # Train the model
    total_step = len(train_loader)
    for epoch in range(args['num_epochs']):
        # TRAINING
        tini = time.time()
        # We start to count training loss from 0
        train_loss = []
        # We load the tuple of (images, labels) from train_loader by each batch
        # images have the shape (B, 1, 28, 28)
        # labels have the shape (B)
        for i, (images, labels) in enumerate(train_loader):
            # Forward pass
            # Outputs have the shape (B, 10) because of 10 possible classes
            outputs = model(images)
            # calculate the loss
            loss = loss_function(outputs, labels)
            # Backward and optimize
            optimizer.zero_grad()  # set the gradient of the network to be zero
            loss.backward()  # calculate the new gradient by backward propagation
            optimizer.step()  # optimizer move a step forward
            # add the loss in this batch to the total loss
            train_loss.append(loss.item())

        # TESTING
        # We start to count testing loss from 0
        test_loss = []
        # We don't calculate gradient during testing
        with torch.no_grad():
            for i, (images, labels) in enumerate(test_loader):
                # Forward pass
                outputs = model(images)
                # calculate the loss
                loss = loss_function(outputs, labels)
                # and the loss in this batch to the total loss
                test_loss.append(loss.item())
        # calculate the accuracy
        acccuracy_test = classification_accuracy(test_loader, model)

        # PRINT THE RESULTS
        print('Epoch {}, Time {:.2f}, Train Loss: {:.4f}, Test Loss: {:.4f}, Test Accuracy: {:.4f}'
              .format(epoch + 1, time.time() - tini,
                      sum(train_loss) / len(train_loss), sum(test_loss) / len(test_loss), acccuracy_test))

if __name__ == '__main__':
    # Hyper-parameters
    args = {'num_epochs': 1,
            'batch_size': 16,
            'learning_rate': 0.001}

    args.update(vars(args_train()))

    # MNIST dataset (images and labels)
    img_transform = nn.Sequential(
            T.Resize([224,224]),
            T.ConvertImageDtype(torch.float),
        )
    train_dataset = CustomImageDataset('.\\train.csv', '.\\TrainSet', transform=img_transform)
    test_dataset = CustomImageDataset('.\\test.csv', '.\\TestSet', transform=img_transform)

    # Data loader (input pipeline)
    train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=args['batch_size'], shuffle=True)
    test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=args['batch_size'], shuffle=False)

    # Logistic regression model
    import torch.nn as nn
    model = CNN_vgg(pretrained=True)

    # Loss and optimizer
    loss_function = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=args['learning_rate'])
    print_num_of_parameters(model)
    train(model, args, train_loader, test_loader, loss_function, optimizer)

    # Test the model
    # In test phase, we don't need to compute gradients (for memory efficiency)

    torch.save(model, args['model'] + '.pth')