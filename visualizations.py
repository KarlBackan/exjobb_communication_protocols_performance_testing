from collectedData import data
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import os

# Define specific colors and markers for the lines
colors = ['#800080', '#008000', '#0000FF']  # purple, green, blue
markers = ['o', 's', '^']  # circle, square, triangle

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

        # Plot data as line graph with different markers
        for i, protocol in enumerate(pivot_df[metric].columns):
            plt.plot(pivot_df[metric].index, pivot_df[metric][protocol], label=protocol, color=colors[i], marker=markers[i], linewidth=2, markersize=8)

        # Customize plot appearance
        plt.xlabel('Payload Size (Bytes)', color='black', fontsize=14, fontweight='bold')
        plt.ylabel(metric, color='black', fontsize=14, fontweight='bold')
        plt.title(metric, color='black', fontsize=16, fontweight='bold')
        plt.legend(title='Protocol', facecolor='white', edgecolor='black', fontsize=12, title_fontsize=14)
        plt.xticks(color='black', fontsize=12, fontweight='bold')
        plt.yticks(color='black', fontsize=12, fontweight='bold')

        # Increase the thickness of the spines (borders)
        plt.gca().spines['bottom'].set_color('black')
        plt.gca().spines['left'].set_color('black')
        plt.gca().spines['top'].set_color('black')
        plt.gca().spines['right'].set_color('black')
        plt.gca().spines['bottom'].set_linewidth(2)
        plt.gca().spines['left'].set_linewidth(2)
        plt.gca().spines['top'].set_linewidth(2)
        plt.gca().spines['right'].set_linewidth(2)

        # Convert x-axis tick labels to integers
        plt.gca().set_xticklabels([str(int(float(label.get_text()))) for label in plt.gca().get_xticklabels()])

        # Adjust layout to make elements more compact
        plt.tight_layout()

        # Save plot with transparent background
        plot_file_path = os.path.join(plots_dir, f"{metric.replace(' ', '_').replace('(', '').replace(')', '').lower()}.png")
        plt.savefig(plot_file_path, transparent=True)
        plt.close()

# Call the function to generate plots
plot_performance_data()
