import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import csv
import os

stalled_filename = '.\\data\\Stalled\\rpm_400.csv'
normal_filename = '.\\data\\Normal\\rpm_400.csv'

x_data, y_data, y_data2 = [], [], []

with open(stalled_filename, 'r', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # skip header

    for row in reader:
        try:
            t = float(row[0])      # time (µs or ms)
            current = float(row[2]) * 1000  # convert to C

            x_data.append(t)
            y_data.append(current)

        except:
            pass

with open(normal_filename, 'r', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # skip header

    for row in reader:
        try:
            t = float(row[0])      # time (µs or ms)
            current = float(row[2]) * 1000  # convert to C

            y_data2.append(current)

        except:
            pass

# --- Normalize time (start from 0, convert to ms if needed) ---
x_data = np.array(x_data)
x_data = (x_data - x_data[0]) / 1000.0  # µs → ms

len_data = min(len(y_data), len(y_data2))
print(len_data, len(y_data), len(y_data2))

x_data = x_data[:len_data]
y_data = np.array(y_data)
y_data = y_data[:len_data]
y_data2 = np.array(y_data2)
y_data2 = y_data2[:len_data]

# --- Downsample (VERY IMPORTANT for readability) ---
DOWNSAMPLE = 20   # change to 5–50 depending on density
x_data = x_data[::DOWNSAMPLE]
y_data = y_data[::DOWNSAMPLE]
y_data2 = y_data2[::DOWNSAMPLE]
print(len_data, len(y_data), len(y_data2))


# --- smooth signal (moving average) ---
WINDOW = 5
y_smooth = np.convolve(y_data, np.ones(WINDOW)/WINDOW, mode='same')
y2_smooth = np.convolve(y_data2, np.ones(WINDOW)/WINDOW, mode='same')

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(x_data, y_smooth, linewidth=1)
ax.plot(x_data, y2_smooth, linewidth=1)


ax.set_xlabel("Time (ms)")
ax.set_ylabel("Current (mA)")
ax.set_title("Motor Current vs Time")

ax.xaxis.set_major_locator(ticker.MaxNLocator(8))
ax.yaxis.set_major_locator(ticker.MaxNLocator(8))

ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('plots/plot.png')
plt.show()
