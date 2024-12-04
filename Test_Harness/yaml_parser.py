import os
import yaml
import numpy as np
import matplotlib.pyplot as plt

# Directory containing the YAML files

# This is the good Cache Run
data_dirs = ['Test_Data/stream-base-1667917891', 
             'Test_Data/stream-bw-core1-1667916181', 
             'Test_Data/stream-bw-core12-1667916103', 
             'Test_Data/stream-bw-core123-1667916117']

num_test_runs = 50
wall_clock_times = [[0 for _ in range(num_test_runs)] for _ in range(len(data_dirs))]

def parse_yaml():
    global wall_clock_times

    for test_num, test_dir in enumerate(data_dirs):
        # Loop over each file in the directory
        for log_idx, filename in enumerate(os.listdir(test_dir)):
            if filename.endswith('.yaml'):
                file_path = os.path.join(test_dir, filename)
                with open(file_path) as stream:
                    try:
                        data = yaml.safe_load(stream)
                        # 'metrics' is a list itself so index 0 into
                        exec_time = data['metrics'][0]['wall-clock-time']
                        wall_clock_times[test_num][log_idx] = exec_time
                    except yaml.YAMLError as exc:
                        print(f"Error parsing {filename}: {exc}")
                        continue  # Skip to the next file if there's an error


def main():
    global wall_clock_times
    parse_yaml()

    # desired metrics:
    WCET = [max(wall_clock_times[i]) for i in range(len(data_dirs))]
    Average = [sum(wall_clock_times[i]) / num_test_runs for i in range(len(data_dirs))]
    Standard_Deviation = [sum([(wall_clock_times[i][j] - Average[i])**2 for j in range(num_test_runs)]) / num_test_runs for i in range(len(data_dirs))]

    print(f"WCET: {WCET}")
    print(f"Average: {Average}")
    print(f"Standard Deviation: {Standard_Deviation}")

    plt.figure()
    plt.title("Histogram of Cache Wall Clock Times")
    for idx, runs in enumerate(data_dirs):
        counts, bins = np.histogram(wall_clock_times[idx])
        bin_size = 0.1  # Set the desired bin size
        bins = np.arange(min(wall_clock_times[idx]), max(wall_clock_times[idx]) + bin_size, bin_size)
        counts, _ = np.histogram(wall_clock_times[idx], bins)
        plt.hist(bins[:-1], bins, weights=counts, alpha=0.5, label=f"Run {idx}")
    plt.xlabel("Wall Clock Time (s)")
    plt.ylabel("Number of Occurences")
    plt.legend([f"Cache Interference on {idx} Cores" for idx in range(len(data_dirs))])

    plt.figure()
    plt.title(f"Cache Interference Over {num_test_runs} Runs")
    plt.xlabel("Number of Runs")
    plt.ylabel("Wall Clock Time (s)")
    plt.axis([0, num_test_runs, 0, max(wall_clock_times[len(data_dirs)-1]) + 1])
    
    for idx, runs in enumerate(data_dirs):
        plt.plot(wall_clock_times[idx], label=f"Cache Interference on {idx} Cores")

    plt.legend()
    plt.show()
    return

if __name__ == "__main__":
    main()