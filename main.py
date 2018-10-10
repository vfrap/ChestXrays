from dataset import MyDataLoader
import torch
import os
from torch.optim import Adam
from model import myDenseNet, averageCrossEntropy
from tensorboardX import SummaryWriter


def initWriter(savemodeldir, logdir):
    """
    Initialize tensorboard logs
    :param savemodeldir: directory wher model weights will be saved
    :param logdir: directory where training logs will be saved
    :return: tensorboard writer
    """
    if not os.path.exists(savemodeldir):
        os.makedirs(savemodeldir)

    if not os.path.exists(logdir):
        os.makedirs(logdir)
    else:
        if os.listdir(logdir):
            print("You have to empty " + logdir)

    writer = SummaryWriter(logdir)

    return writer


if __name__=="__main__":

    ####################################################################################################################
    # Parameters
    ####################################################################################################################
    """
    # Local Dataloader
    datadir = "/home/user1/Documents/Data/ChestXray/images"
    train_csvpath = "/home/user1/Documents/Data/ChestXray/DataTrain.csv"
    val_csvpath = "/home/user1/Documents/Data/ChestXray/DataVal.csv"

    # Local Writer
    savemodeldir = "/home/user1/PycharmProjects/ChestXrays/Logs/model_1"
    logdir = "/home/user1/PycharmProjects/ChestXrays/Logs/training_1"
    """

    # Server Dataloader
    datadir = "/data/lisa/data/ChestXray-NIHCC-2/images"
    train_csvpath = "/u/bertinpa/Documents/ChestXrays/Data/DataTrain.csv"
    val_csvpath = "/u/bertinpa/Documents/ChestXrays/Data/DataVal.csv"

    # Server Writer
    savemodeldir = "/u/bertinpa/Documents/ChestXrays/Logs/model_1"
    logdir = "/u/bertinpa/Documents/ChestXrays/Logs/training_1"

    # Image Size fed to the network
    inputsize = [224, 224]

    # Optimizer
    learning_rate = 0.001

    # Training
    num_epochs = 100
    val_every_n_iter = 200
    batch_per_val_session = 10

    ####################################################################################################################
    # Initialization
    ####################################################################################################################

    print("Initializing...")

    # Dataloaders
    train_dataloader = MyDataLoader(datadir, train_csvpath, inputsize, batch_size=16)
    val_dataloader = MyDataLoader(datadir, val_csvpath, inputsize, batch_size=16)

    # Model
    if torch.cuda.is_available():
        densenet = myDenseNet().cuda()
    else:
        densenet = myDenseNet()

    # Writer
    writer = initWriter(savemodeldir, logdir)

    # Loss
    criterion = averageCrossEntropy

    # Optimizer
    optimizer = Adam(densenet.parameters(), lr=learning_rate)

    ####################################################################################################################
    # Training
    ####################################################################################################################

    print("Training...")

    num_iteration = 0  # Number of iterations

    for epoch in range(num_epochs):
        # Training
        for data, label in train_dataloader:

            if torch.cuda.is_available():
                data = data.cuda()
                label = label.cuda()

            # Forward
            output = densenet(data)
            optimizer.zero_grad()
            loss = criterion(output, label)

            # Save loss
            writer.add_scalar('Train_Loss', loss, num_iteration)

            # Backward
            loss.backward()
            optimizer.step()
            num_iteration += 1

            # Validation
            if num_iteration % val_every_n_iter == 0:
                n_val = 0
                test_loss = 0.

                for data, label in val_dataloader:
                    output = densenet(data)
                    test_loss += criterion(output, label).data

                    n_val +=1
                    if n_val == batch_per_val_session:
                        test_loss /= batch_per_val_session
                        break

                writer.add_scalar('Test_Loss', test_loss, num_iteration)

                # Save model
                torch.save(densenet.state_dict(),
                           os.path.join(savemodeldir, 'model_' + str(num_iteration) + '.pth'))
                    

