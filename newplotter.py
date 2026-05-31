import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

normal_filename = '.\\data\\robot_7_2026-02-17.csv'
stalled_filename = '.\\MotorStallTestSetup\\data\\Normal\\rpm_400.csv'


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


def train_joint_velocity(file_name, joint_index, color, plot: plt.Axes):
    print(f"Plotting joint velocity {joint_index}")

    x, angles = [], []

    with open(file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            try:
                t = float(row[0])
                angle = float(row[joint_index])

                x.append(t)
                angles.append(angle)

            except:
                pass

    x = np.array(x)
    angles = np.array(angles)

    # convert timestamps to seconds
    x = (x - x[0]) / 1000.0

    # derivative
    dt = np.diff(x)
    dtheta = np.diff(angles)

    velocity = np.divide(
        dtheta,
        dt,
        out=np.zeros_like(dtheta),
        where=dt != 0
    )

    x_vel = x[1:]

    # downsample
    x_vel = x_vel[::DOWNSAMPLE]
    velocity = velocity[::DOWNSAMPLE]

    # smooth
    velocity = np.convolve(
        velocity,
        np.ones(WINDOW) / WINDOW,
        mode='same'
    )

    plot.plot(x_vel, velocity, color=color, linewidth=1)

    print(f"Finished joint velocity {joint_index}")

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
train_additional_function(stalled_filename, 2, 'black', ax1)
train_additional_function(normal_filename, 19, 'green', ax1)
train_additional_function(normal_filename, 20, 'orange', ax1)
train_additional_function(normal_filename, 21, 'yellow', ax1)
train_additional_function(normal_filename, 22, 'green', ax1)
train_additional_function(normal_filename, 23, 'teal', ax1)
train_additional_function(normal_filename, 24, 'blue', ax1)
train_additional_function(normal_filename, 25, 'indigo', ax1)
train_additional_function(normal_filename, 26, 'purple', ax1)
print_figure(ax1, 'MotorStallTestSetup/plots/current_plot.png', show=False)

fig2, ax2 = create_figure("Time (s)", "Temperature (°C)")
train_additional_function(stalled_filename, 12, 'black', ax2)
train_additional_function(normal_filename, 27, 'green', ax2)
train_additional_function(normal_filename, 28, 'orange', ax2)
train_additional_function(normal_filename, 29, 'yellow', ax2)
train_additional_function(normal_filename, 30, 'green', ax2)
train_additional_function(normal_filename, 31, 'teal', ax2)
train_additional_function(normal_filename, 32, 'blue', ax2)
train_additional_function(normal_filename, 33, 'indigo', ax2)
train_additional_function(normal_filename, 34, 'purple', ax2)
print_figure(ax2, 'MotorStallTestSetup/plots/temperature_plot.png', show=False)

fig3, ax3 = create_figure("Time (s)", "Motion")
#-- train_additional_function(stalled_filename, 1,'black', ax3)
train_joint_velocity(normal_filename, 5, 'green', ax3)   # joint_1
train_joint_velocity(normal_filename, 6, 'orange', ax3)  # joint_2
train_joint_velocity(normal_filename, 7, 'yellow', ax3)  # joint_3
train_joint_velocity(normal_filename, 8, 'teal', ax3)    # joint_4
train_joint_velocity(normal_filename, 9, 'blue', ax3)    # joint_5
train_joint_velocity(normal_filename, 10, 'indigo', ax3) # joint_6
train_joint_velocity(normal_filename, 11, 'purple', ax3) # joint_7
train_joint_velocity(normal_filename, 12, 'red', ax3)    # joint_8
print_figure(ax3, 'MotorStallTestSetup/plots/motion_plot.png', show=False)

fig4, ax4 = create_figure("Time (s)", "Step Normal")
train_additional_function(normal_filename, 2, 'black', ax4)
print_figure(ax4, 'MotorStallTestSetup/plots/step_plot.png', show=False)

fig5, ax5 = create_figure("Time (s)", "Position Normal")
train_additional_function(normal_filename, 13, 'black', ax5)
train_additional_function(normal_filename, 14, 'blue', ax5)
train_additional_function(normal_filename, 15, 'red', ax5)
print_figure(ax5, 'MotorStallTestSetup/plots/position_plot.png', show=False)

fig6, ax6 = create_figure("Time (s)", "Load Normal")
train_additional_function(normal_filename, 43, 'black', ax6)
train_additional_function(normal_filename, 44, 'green', ax6)
train_additional_function(normal_filename, 45, 'orange', ax6)
train_additional_function(normal_filename, 46, 'yellow', ax6)
train_additional_function(normal_filename, 47, 'teal', ax6)
train_additional_function(normal_filename, 48, 'purple', ax6)
train_additional_function(normal_filename, 49, 'blue', ax6)
train_additional_function(normal_filename, 50, 'pink', ax6)
print_figure(ax6, 'MotorStallTestSetup/plots/load_plot.png', show=False)

