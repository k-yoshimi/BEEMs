import tomli
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

def main():
    """Plot and compare target vs estimated magnetization curves.

    This script reads target magnetization data and estimated magnetization data from 
    Bayesian optimization results, then creates a comparison plot saved as a PDF.

    Parameters
    ----------
    file_name : str
        Path to TOML configuration file containing target CSV path
    plot_BO_no : str, optional
        Specific Bayesian optimization iteration number to plot. If not provided,
        the best iteration will be determined from best.csv

    Returns
    -------
    None
        Saves plot as mag.pdf in current directory

    Notes
    -----
    The script expects:
    - A TOML config file with target CSV path
    - Target magnetization data CSV
    - BO results in Sum/BO_NoX/all_mag.csv format
    - best.csv in org/ directory if no specific BO iteration provided
    """
    # Parse command line arguments
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

    # Verify TOML config file exists
    if not os.path.exists(file_name):
        print("File not found: {}".format(file_name))
        exit(1)

    # Load TOML configuration
    with open(file_name, "rb") as f:
        toml_dict = tomli.load(f)

    # Get and validate target CSV path from TOML
    target_file_name = toml_dict["path"]["target_csv"]
    if target_file_name is None:
        print("params.toml is invalid.")
        print("target_csv is not found.")
        exit(1)

    # Verify target CSV exists
    if not os.path.exists(target_file_name):
        print("File not found: {}".format(target_file_name))
        exit(1)

    # Load target magnetization data
    target_data = np.loadtxt(target_file_name, delimiter=',', dtype=np.float64)

    # If no specific BO iteration provided, find the best one from best.csv
    if plot_BO_no is None:
        path_to_best_csv = os.path.join("org", "best.csv")
        if not os.path.exists(path_to_best_csv):
            print("File not found: {}".format(path_to_best_csv))
            exit(1)
        best_csv = np.loadtxt(path_to_best_csv, delimiter=',', dtype="unicode")
        plot_BO_no = np.argmax(best_csv[:, 1])  # Get iteration with best score

    # Load estimated magnetization data from specified BO iteration
    BO_data = np.loadtxt(os.path.join("Sum", "BO_No{}".format(plot_BO_no), "all_mag.csv"), 
                         delimiter=',', dtype=np.float64)

    # Create comparison plot
    fig, ax = plt.subplots()
    ax.set_xlabel("H")  # Magnetic field strength
    ax.set_ylabel("Sz")  # Z-component of magnetization
    ax.set_title("Target vs Estimated magnetization curve")
    ax.grid()
    
    # Plot target data points in red
    ax.plot(target_data[:, 0], target_data[:, 1], 
            label="Target", marker="o", linestyle="None", color="red")
    
    # Plot estimated magnetization curve in blue
    ax.plot(BO_data[:, 0], BO_data[:, 1], 
            label="Estimated (BO_NO{})".format(plot_BO_no), color="blue")
    
    plt.legend()
    plt.savefig("mag.pdf")
    plt.close()

if __name__ == "__main__":
    main()