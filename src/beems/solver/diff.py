import itertools
import math
import numpy as np
import sys
import os

def func_readhphi(file_name):
    """Read magnetization data from HPhi output file.

    Parameters
    ----------
    file_name : str
        Path to the file containing magnetization data

    Returns
    -------
    ndarray
        Magnetization values from the second column of the file
    """
    mag = np.loadtxt(file_name, delimiter=",")[:,1]
    return mag

def func_readinfo(file_name):
    """Read row number from info file.

    Parameters
    ----------
    file_name : str
        Path to the info file

    Returns
    -------
    int
        Row number from first line of file
    """
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")
    tmp = data[0].split()
    row = int(tmp[0])
    return row


def func_chparam(in_file, out_file, row, diff):
    """Update parameter file with difference value.

    Parameters
    ----------
    in_file : str
        Input parameter file path
    out_file : str
        Output parameter file path 
    row : int
        Row number to update
    diff : float
        Difference value to insert

    Returns
    -------
    int
        -1 if error, None otherwise
    """
    with open(in_file) as f:
        data = f.read()
        data = data.split("\n")
    cnt_max = len(data) - 1
    tmp_data = data[row - 1].split(",")
    if len(tmp_data[0]) > 0:
        print("Error: delta already exits: please check {}.".format(in_file))
        return -1
    tmp_str = data[row - 1]
    data[row - 1] = "%12.8f  %s" % (diff, tmp_str)
    with open(out_file, 'w') as f:
        for cnt in range(0, cnt_max):
            print("%s" % (data[cnt]), file=f)

def main(dir_name, target_data):
    """Main function to calculate magnetization difference.

    Parameters
    ----------
    dir_name : str
        Directory containing HPhi output files
    target_data : ndarray
        Target magnetization data

    Returns
    -------
    float
        Negative mean squared difference between HPhi and target magnetization
    """
    # Extract target magnetization values
    target_mag = target_data[:,1]
    # Read HPhi magnetization data
    hphi_mag = func_readhphi(os.path.join(dir_name, "all_mag.csv"))
    # Get row number from info file
    row = func_readinfo(os.path.join(dir_name, "info"))
    # Calculate negative mean squared difference
    diff_mag = -np.mean((hphi_mag - target_mag) ** 2)
    # Update parameter file with difference
    func_chparam(os.path.join("org","param.csv"), os.path.join("org","param.csv"), row, diff_mag)
    return diff_mag

if __name__ == "__main__":
    dir_name = sys.argv[1]
    mag_name = sys.argv[2]
    main(dir_name, mag_name)
