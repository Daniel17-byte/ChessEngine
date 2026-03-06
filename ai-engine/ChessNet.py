import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """Standard residual block: conv → BN → ReLU → conv → BN + skip"""
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = out + residual
        return F.relu(out)


class ChessNet(nn.Module):
    def __init__(self, n_moves, in_channels=18, n_filters=128, n_res_blocks=4):
        super().__init__()
        # Initial conv to expand channels
        self.conv_in = nn.Conv2d(in_channels, n_filters, kernel_size=3, padding=1)
        self.bn_in = nn.BatchNorm2d(n_filters)

        # Residual tower
        self.res_blocks = nn.Sequential(
            *[ResidualBlock(n_filters) for _ in range(n_res_blocks)]
        )

        # Policy head
        self.policy_conv = nn.Conv2d(n_filters, 32, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(32)
        self.policy_fc = nn.Linear(32 * 8 * 8, n_moves)

    def forward(self, x):
        # x: [B, 18, 8, 8]
        x = F.relu(self.bn_in(self.conv_in(x)))
        x = self.res_blocks(x)
        # Policy head
        p = F.relu(self.policy_bn(self.policy_conv(x)))
        p = p.view(p.size(0), -1)
        return self.policy_fc(p)
