import torch 
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.nn.init as init
import numpy as np
import imageio

class UNetConvBlock(nn.Module):
    def __init__(self, in_size, out_size, kernel_size=3, activation=F.relu):
        super(UNetConvBlock, self).__init__()
        self.conv = nn.Conv2d(in_size, out_size, kernel_size, stride=1, padding=1)
        self.bn = nn.BatchNorm2d(out_size)
        self.conv2 = nn.Conv2d(out_size, out_size, kernel_size, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_size)
        self.activation = activation


        init.xavier_uniform_(self.conv.weight, gain = np.sqrt(2.0))
        init.constant_(self.conv.bias,0)
        init.xavier_uniform_(self.conv2.weight, gain = np.sqrt(2.0))
        init.constant_(self.conv2.bias,0)
    def forward(self, x):
        out = self.activation(self.bn(self.conv(x)))
        out = self.activation(self.bn2(self.conv2(out)))

        return out

class UNetUpBlock(nn.Module):
    def __init__(self, in_size, out_size, kernel_size=3, activation=F.relu, space_dropout=False):
        super(UNetUpBlock, self).__init__()
        self.up = nn.ConvTranspose2d(in_size, out_size, 2, stride=2)
        self.bnup = nn.BatchNorm2d(out_size)
        self.conv = nn.Conv2d(in_size, out_size, kernel_size, stride=1, padding=1)
        self.bn = nn.BatchNorm2d(out_size)
        self.conv2 = nn.Conv2d(out_size, out_size, kernel_size, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_size)
        self.activation = activation
        init.xavier_uniform_(self.up.weight, gain = np.sqrt(2.0))
        init.constant_(self.up.bias,0)
        init.xavier_uniform_(self.conv.weight, gain = np.sqrt(2.0))
        init.constant_(self.conv.bias,0)
        init.xavier_uniform_(self.conv2.weight, gain = np.sqrt(2.0))
        init.constant_(self.conv2.bias,0)

    def center_crop(self, layer, target_size):
        batch_size, n_channels, layer_width, layer_height = layer.size()
        xy1 = (layer_width - target_size) // 2
        return layer[:, :, xy1:(xy1 + target_size), xy1:(xy1 + target_size)]

    def forward(self, x, bridge):
        up = self.up(x)
        up = self.activation(self.bnup(up))
        crop1 = self.center_crop(bridge, up.size()[2])
        out = torch.cat([up, crop1], 1)

        out = self.activation(self.bn(self.conv(out)))
        out = self.activation(self.bn2(self.conv2(out)))

        return out

class UNet(nn.Module):
    def __init__(self, in_channel = 1, n_classes = 3):
        super(UNet, self).__init__()
#         self.imsize = imsize

        self.activation = F.relu
        
        self.pool1 = nn.MaxPool2d(2)
        self.pool2 = nn.MaxPool2d(2)
        self.pool3 = nn.MaxPool2d(2)
        self.pool4 = nn.MaxPool2d(2)

        self.conv_block1_64 = UNetConvBlock(in_channel, 32)
        self.conv_block64_128 = UNetConvBlock(32, 64)
        self.conv_block128_256 = UNetConvBlock(64, 128)
        self.conv_block256_512 = UNetConvBlock(128, 256)
        self.conv_block512_1024 = UNetConvBlock(256, 512)
        # this kind of symmetric design is awesome, it automatically solves the number of channels during upsamping
        self.up_block1024_512 = UNetUpBlock(512, 256)
        self.up_block512_256 = UNetUpBlock(256, 128)
        self.up_block256_128 = UNetUpBlock(128, 64)
        self.up_block128_64 = UNetUpBlock(64, 32)

        self.last = nn.Conv2d(32, n_classes, 1, stride=1)


    def forward(self, x):
#         print 'line 70 ',x.size()
        block1 = self.conv_block1_64(x)
        pool1 = self.pool1(block1)

        block2 = self.conv_block64_128(pool1)
        pool2 = self.pool2(block2)

        block3 = self.conv_block128_256(pool2)
        pool3 = self.pool3(block3)

        block4 = self.conv_block256_512(pool3)
        pool4 = self.pool4(block4)

        block5 = self.conv_block512_1024(pool4)

        up1 = self.up_block1024_512(block5, block4)

        up2 = self.up_block512_256(up1, block3)

        up3 = self.up_block256_128(up2, block2)

        up4 = self.up_block128_64(up3, block1)

        return self.last(up4)


if __name__ == "__main__":
    # model = DenseNet(num_init_features=64,growth_rate=32,block_config=(6,12,24,16))
    # print(model)
    b= UNet(in_channel=1,n_classes=3)
    # #print(b)
    #
    te = imageio.imread('1.png')
    arr = np.expand_dims(te,axis=0)
    arr = np.expand_dims(arr,axis=0)
    arr = torch.FloatTensor(arr)
    cc = b(arr)

    pass
