import re
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd

# Function to filter data between two timestamps and calculate elapsed time in minutes
def filter_data_between_timestamps(df, start_time, end_time):
    mask = (df['时间'] >= start_time) & (df['时间'] <= end_time)
    filtered_df = df.loc[mask].copy()
    filtered_df['Elapsed Minutes'] = (filtered_df['时间'] - start_time).dt.total_seconds() / 60
    return filtered_df

# Initialize lists to store timestamps, attention scores, and reminder timestamps
timestamps = []
attention_scores = []
reminder_timestamps = []

# Define the regex patterns for extracting attention scores and reminder timestamps
attention_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Attention: (\d+\.\d+)")
reminder_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Reminder window triggered\.")

# Read the file with UTF-8 encoding
with open('./extract_log.txt', 'r', encoding='utf-8') as file:
    for line in file:
        attention_match = attention_pattern.search(line)
        reminder_match = reminder_pattern.search(line)

        if attention_match:
            timestamp_str, attention_score = attention_match.groups()
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            timestamps.append(timestamp)
            attention_scores.append(float(attention_score))

        if reminder_match:
            reminder_timestamp_str = reminder_match.group(1)
            reminder_timestamp = datetime.strptime(reminder_timestamp_str, '%Y-%m-%d %H:%M:%S')
            reminder_timestamps.append(reminder_timestamp)

# Calculate elapsed time in minutes from the start
start_time = timestamps[0]
elapsed_minutes = [(ts - start_time).total_seconds() / 60 for ts in timestamps]
reminder_elapsed_minutes = [(ts - start_time).total_seconds() / 60 for ts in reminder_timestamps]

# Read the Excel file
file_path = './experiment_data/2024-06-26-21-29-21/eegdata_2024-06-26-21-45-23.xls'
df = pd.read_excel(file_path)

# Convert '时间' column to datetime format
df['时间'] = pd.to_datetime(df['时间'], format='%H:%M:%S')

# Input timestamps
start_time_str = '21:29:46'
end_time_str = '21:44:10'

# Convert input timestamps to datetime format
start_time_dt = datetime.strptime(start_time_str, '%H:%M:%S')
end_time_dt = datetime.strptime(end_time_str, '%H:%M:%S')

# Filter data between the specified timestamps
filtered_df = filter_data_between_timestamps(df, start_time_dt, end_time_dt)

alpha = 0.05
attention_average = 50
attentioooon = np.array([])
times = np.array([])
for index, value in enumerate(filtered_df['专注度']):
    attention_average = alpha * value + (1 - alpha) * attention_average
    if index % 4 == 0:
        attentioooon = np.append(attentioooon, attention_average)
for index, value in enumerate(filtered_df['Elapsed Minutes']):
    if index % 4 == 0:
        times = np.append(times, value)

# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))

# Plot the first attention scores over elapsed time in minutes
ax1.plot(elapsed_minutes, np.array(attention_scores) / 100, marker='o', linestyle='-', color='b')
for rem_time in reminder_elapsed_minutes:
    ax1.axvline(x=rem_time, color='r', linestyle='--', label='Alert Triggered' if rem_time == reminder_elapsed_minutes[0] else "")
ax1.set_xlabel('Elapsed Time (Minutes)')
ax1.set_ylabel('Attention Level')
ax1.set_ylim([0, 1])
ax1.set_title('Attention Level Over Time (GoodFocus)')
ax1.legend()
ax1.grid(True)

# Plot the second attention scores over elapsed time in minutes
ax2.plot(times, attentioooon / 100, marker='o', linestyle='-', color='b')
ax2.set_xlabel('Elapsed Time (Minutes)')
ax2.set_ylabel('Attention Level')
ax2.set_ylim([0, 1])
ax2.set_title('Attention Level Over Time (No Intervention)')
ax2.grid(True)

plt.tight_layout()

# Save the combined plot to a PDF file
plt.savefig("combined_attention_plot.pdf")

# Display the combined plot
plt.show()
