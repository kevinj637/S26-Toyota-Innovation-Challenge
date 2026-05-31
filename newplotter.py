import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

file_name = '.\\data\\robot_7_2026-02-17.csv'


#CONSTANTS MANAGEMENT
WINDOW = 5 # Convolution average
DOWNSAMPLE = 20   # change to 5–50 depending on density
LEN_DATA = 10000000000 # limit for now


# must come from the same file or you get errors!
def train_additional_function(file_name, index: str | int, color, plot: plt.Axes, multiplier = 1, offset = 0, label = ""):
    if isinstance(index, str):
        index = index.lower()
        if(len(index) > 2):
            return TypeError("index not valid")
        if(len(index) == 2):
            index = (ord(index[0]) - (ord('a') - 1)) * 26 + ord(index[1]) - ord('a')
        else:
            index = (ord(index) - ord('a'))
    print(f"Plotting index {index}")
    x, y = [], []
    with open(file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            try:
                t = float(row[0])      # time (µs or ms)
                current = float(row[index]) * multiplier + offset  # convert to C

                x.append(t)
                y.append(current)

            except:
                pass
    len_data = min(len(x), LEN_DATA)

    x = np.array(x)
    x = (x - x[0]) # µs → ms

    print(f"Almost done index {index}")
    y = np.array(y)
    x = x[:len_data]
    x = x[::DOWNSAMPLE]
    y = y[:len_data]
    y = y[::DOWNSAMPLE]
    y_smothered = np.convolve(y, np.ones(WINDOW)/WINDOW, mode='same') 
    if len(label):
        plot.plot(x, y_smothered, color=color, linewidth=1, label=label)
    else:
        plot.plot(x, y_smothered, color=color, linewidth=1)
    print(f"Finished index {index}")


def train_additional_function_lims(file_name, loc, around, index: str | int, color, plot: plt.Axes, multiplier = 1, offset = 0, label = ""):
    if isinstance(index, str):
        index = index.lower()
        if(len(index) > 2):
            return TypeError("index not valid")
        if(len(index) == 2):
            index = (ord(index[0]) - (ord('a') - 1)) * 26 + ord(index[1]) - ord('a')
        else:
            index = (ord(index) - ord('a'))
    print(f"Plotting index {index}")
    x, y = [], []
    with open(file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            try:
                t = float(row[0])      # time (µs or ms)
                current = float(row[index]) * multiplier + offset # convert to C

                x.append(t)
                y.append(current)

            except:
                pass
    len_data = min(len(x), LEN_DATA)
    lowest = max(0, loc - around)
    highest = min(len_data, loc + around)

    x = np.array(x)
    x = (x - x[0]) # µs → ms

    print(f"Almost done index {index}")
    y = np.array(y)
    x = x[lowest:highest]
    x = x[::DOWNSAMPLE]
    y = y[lowest:highest]
    y = y[::DOWNSAMPLE]
    y_smothered = np.convolve(y, np.ones(WINDOW)/WINDOW, mode='same') 
    if len(label):
        plot.plot(x, y_smothered, color=color, linewidth=1, label=label)
    else:
        plot.plot(x, y_smothered, color=color, linewidth=1)
    print(f"Finished index {index}")

def create_figure(x_label, y_label):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(f"{y_label} vs. {x_label}")

    return fig, ax

def print_figure(ax: plt.Axes, file_name = 'MotorStallTestSetup/plots/plot.png', show = False):

    ax.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(file_name)
    if show:
        plt.show()

type colour = str
#               Col Name, Col index, color, multiplier, offset
type YCol = tuple[str, int|str, colour, float, float]
def graphMultiple(file_name, yCols: list[YCol], export_file_name  = 'MotorStallTestSetup/plots/plot.png'):
    names = [name for name, _, _, _, _ in yCols]
    title_name = ", ".join(names)
    fig, ax = create_figure("Time (s)", title_name)
    for col in yCols:
        train_additional_function(file_name, col[1], col[2], ax, col[3], label = col[0])
    ax.legend()
    print_figure(ax, export_file_name)

def graphMultiple_AroundLimits(file_name, loc, around, yCols: list[YCol], export_file_name  = 'MotorStallTestSetup/plots/plot.png'):
    names = [name for name, _, _, _, _ in yCols]
    title_name = ", ".join(names)
    fig, ax = create_figure("Time (s)", title_name)
    for col in yCols:
        train_additional_function_lims(file_name, loc, around, col[1], col[2], ax, col[3], label = col[0])
    ax.legend()
    print_figure(ax, export_file_name)



fig1, ax1 = create_figure("Time (s)", "Current (A)")
train_additional_function(file_name, 'AB', 'green', ax1)
print_figure(ax1)

# graphMultiple(file_name, [
#     ('Current (A)', 'T', 'green', 1),
#     ('Torque (Nm)', 'AJ', 'blue', 1),
#     ],
#     'MotorStallTestSetup/plots/multiple.png')

graphMultiple_AroundLimits(file_name, 180000, 10000, [
    ('Current (A)', 'T', 'green', 1, 0),
    ('Torque (Nm)', 'AJ', 'blue', 1, 0),
    ('Temperature (C)', 'AB', 'blue', 1, -25),
    ],
    'MotorStallTestSetup/plots/multiple_180000.png')

