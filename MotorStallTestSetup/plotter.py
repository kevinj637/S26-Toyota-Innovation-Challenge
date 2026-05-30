import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

stalled_filename = '.\\data\\Stalled\\rpm_400.csv'
normal_filename = '.\\data\\Normal\\rpm_400.csv'

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
            current = float(row[2]) * 1000  # convert to current

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
y_smooth = np.convolve(stalled_data, np.ones(WINDOW)/WINDOW, mode='same')
y2_smooth = np.convolve(normal_data, np.ones(WINDOW)/WINDOW, mode='same')

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(x_data, y_smooth, color='blue', linewidth=1)
ax.plot(x_data, y2_smooth, color='green', linewidth=1)


ax.set_xlabel("Time (ms)")
ax.set_ylabel("Current (mA)")
ax.set_title("Motor Current vs Time")

ax.xaxis.set_major_locator(ticker.MaxNLocator(8))
ax.yaxis.set_major_locator(ticker.MaxNLocator(8))

ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('plots/plot.png')
plt.show()
