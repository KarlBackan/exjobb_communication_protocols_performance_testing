from collectedData import data
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import os
def plot_performance_data():
    df = pd.read_csv(StringIO(data))

    # Ensure the 'plots' directory exists
    plots_dir = 'plots'
    os.makedirs(plots_dir, exist_ok=True)

    # Pivot data for easier plotting
    pivot_df = df.pivot(index='Parameter', columns='Protocol')

    # Metrics for plotting
    metrics = [
        "Average CPU Usage (%)", "Total Memory Usage (Bytes)", "Total Disk Read (Bytes)",
        "Total Disk Write (Bytes)", "Network Bytes Sent", "Network Bytes Received",
        "Thread Count", "Resource Handles", "Duration (Seconds)"
    ]

    # Plot each metric in its own figure and save it
    for metric in metrics:
        plt.figure(figsize=(10, 6))
        pivot_df[metric].plot(kind='bar', title=metric)
        plt.xlabel('Payload Size (Bytes)')
        plt.ylabel(metric)
        plt.legend(title='Protocol')
        plt.tight_layout()
        plot_file_path = os.path.join(plots_dir, f"{metric.replace(' ', '_').replace('(', '').replace(')', '').lower()}.png")
        plt.savefig(plot_file_path)
        plt.close()

# Call the function to generate plots
plot_performance_data()
