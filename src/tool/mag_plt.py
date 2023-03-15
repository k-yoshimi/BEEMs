import tomli
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

def main():
    args = sys.argv
    if len(args) == 2:
        file_name = args[1]
        plot_BO_no = None
    elif len(args) == 3:
        file_name = args[1]
        plot_BO_no = args[2]
    else:
        print("Usage: python mag_plt.py [file_name] [plot_BO_no]")
        exit(1)

    if not os.path.exists(file_name):
        print("File not found: {}".format(file_name))
        exit(1)

    with open(file_name, "rb") as f:
        toml_dict = tomli.load(f)

    target_file_name = toml_dict["path"]["target_csv"]
    if target_file_name is None:
        print("params.toml is invalid.")
        print("target_csv is not found.")
        exit(1)

    if not os.path.exists(target_file_name):
        print("File not found: {}".format(target_file_name))
        exit(1)

    target_data = np.loadtxt(target_file_name, delimiter=',', dtype=np.float64)

    if plot_BO_no is None:
        #get best BO_No
        path_to_best_csv = os.path.join("org", "best.csv")
        if not os.path.exists(path_to_best_csv):
            print("File not found: {}".format(path_to_best_csv))
            exit(1)
        best_csv = np.loadtxt(path_to_best_csv, delimiter=',', dtype="unicode")
        plot_BO_no = np.argmax(best_csv[:, 1])

    BO_data = np.loadtxt(os.path.join("Sum", "BO_No{}".format(plot_BO_no), "all_mag.csv"), delimiter=',',dtype=np.float64)
    fig, ax = plt.subplots()
    ax.set_xlabel("H")
    ax.set_ylabel("Sz")
    ax.set_title("Target vs Estimated magnetization curve")
    ax.grid()
    ax.plot(target_data[:, 0], target_data[:, 1], label="Target", marker="o", linestyle="None",color="red")
    ax.plot(BO_data[:, 0], BO_data[:, 1], label="Estimated (BO_NO{})".format(plot_BO_no), color="blue")
    plt.legend()
    plt.savefig("mag.pdf")
    plt.close()

if __name__ == "__main__":
    main()