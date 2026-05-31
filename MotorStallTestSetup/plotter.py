import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

stalled_filename = '.\\MotorStallTestSetup\\data\\Normal\\rpm_400.csv'
normal_filename = '.\\data\\robot_7_2026-02-17.csv'

x_data, stalled_data, normal_data = [], [], []


with open(stalled_filename, 'r', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # skip header

    for row in reader:
        try:
            t = float(row[0])      # time (µs or ms)
            current = float(row[2]) * 1000  # convert to C

            x_data.append(t)
            stalled_data.append(current)

        except:
            pass

with open(normal_filename, 'r', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # skip header

    for row in reader:
        try:
            t = float(row[0])      # time (µs or ms)
            current = float(row[19]) * 1000  # convert to current

            normal_data.append(current)

        except:
            pass


    


# --- Normalize time (start from 0, convert to ms if needed) ---
x_data = np.array(x_data)
x_data = (x_data - x_data[0]) / 1000.0  # µs → ms

len_data = min(len(stalled_data), len(normal_data))
print(len_data, len(stalled_data), len(normal_data))

x_data = x_data[:len_data]
stalled_data = np.array(stalled_data)
stalled_data = stalled_data[:len_data]
normal_data = np.array(normal_data)
normal_data = normal_data[:len_data]

# --- Downsample (VERY IMPORTANT for readability) ---
DOWNSAMPLE = 20   # change to 5–50 depending on density
x_data = x_data[::DOWNSAMPLE]
stalled_data = stalled_data[::DOWNSAMPLE]
normal_data = normal_data[::DOWNSAMPLE]
print(len_data, len(stalled_data), len(normal_data))


# --- smooth signal (moving average) ---
WINDOW = 5
y_smooth = np.convolve(stalled_data, np.ones(WINDOW)/WINDOW, mode='same') # --- stalled current
y2_smooth = np.convolve(normal_data, np.ones(WINDOW)/WINDOW, mode='same') # --- normal current



# must come from the same file or you get errors!
def train_additional_function(file_name, index, color, plot, multiplier = 1):
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

    x = np.array(x)
    x = (x - x[0]) / 1000.0  # µs → ms

    y = np.array(y)
    x = x[:len_data]
    x = x[::DOWNSAMPLE]
    y = y[:len_data]
    y = y[::DOWNSAMPLE]
    y_smothered = np.convolve(y, np.ones(WINDOW)/WINDOW, mode='same') 
    print("Plotting")
    plot.plot(x, y_smothered, color=color, linewidth=1)




# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(x_data, y_smooth, color='black', linewidth=1)
ax.plot(x_data, y2_smooth, color='red', linewidth=1)
train_additional_function(normal_filename, 20, 'orange', ax)
train_additional_function(normal_filename, 21, 'yellow', ax)
train_additional_function(normal_filename, 22, 'green', ax)
train_additional_function(normal_filename, 23, 'teal', ax)
train_additional_function(normal_filename, 24, 'blue', ax)
train_additional_function(normal_filename, 25, 'indigo', ax)
train_additional_function(normal_filename, 26, 'purple', ax)



ax.set_xlabel("Time (ms)")
ax.set_ylabel("Current (mA)")
ax.set_title("Motor Current vs Time")

ax.xaxis.set_major_locator(ticker.MaxNLocator(8))
ax.yaxis.set_major_locator(ticker.MaxNLocator(8))

ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('MotorStallTestSetup/plots/plot.png')
plt.show()
