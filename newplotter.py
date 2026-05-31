import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

file_name = '.\\data\\robot_7_2026-02-17.csv'


#CONSTANTS MANAGEMENT
WINDOW = 5 # Convolution average
DOWNSAMPLE = 20   # change to 5–50 depending on density
LEN_DATA = 10000000000


# must come from the same file or you get errors!
def train_additional_function(file_name, index, color, plot: plt.Axes, multiplier = 1):
    print(f"Plotting index {index}")
    x, y = [], []
    with open(file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            try:
                t = float(row[0])      # time (µs or ms)
                current = float(row[index]) * multiplier  # convert to C

                x.append(t)
                y.append(current)

            except:
                pass
    len_data = min(len(x), LEN_DATA)

    x = np.array(x)
    x = (x - x[0]) / 1000.0  # µs → ms

    print(f"Almost done index {index}")
    y = np.array(y)
    x = x[:len_data]
    x = x[::DOWNSAMPLE]
    y = y[:len_data]
    y = y[::DOWNSAMPLE]
    y_smothered = np.convolve(y, np.ones(WINDOW)/WINDOW, mode='same') 
    plot.plot(x, y_smothered, color=color, linewidth=1)
    print(f"Finished index {index}")


def create_figure(x_label, y_label):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f"{y_label} vs. {x_label}")

    return fig, ax

def print_figure(ax: plt.Axes, file_name = 'MotorStallTestSetup/plots/plot.png', show = False):

    ax.xaxis.set_major_locator(ticker.MaxNLocator(8))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(8))

    ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(file_name)
    if show:
        plt.show()

fig1, ax1 = create_figure("Time (s)", "Current (A)")
train_additional_function(file_name, 19, 'green', ax1)
print_figure(ax1)
