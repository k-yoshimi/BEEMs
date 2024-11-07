import cmath
import copy
import math
import numpy as np
import os
import sys


def main(Nspin, file_name="zvo_energy.dat", resul_mag="resul_mag.dat", debug_file="debug.txt"):
    """
    Calculate total magnetization per site from energy file.

    Parameters
    ----------
    Nspin : int
        Number of spins in the system
    file_name : str, optional
        Input energy file name, by default "zvo_energy.dat"
    resul_mag : str, optional
        Output magnetization file name, by default "resul_mag.dat"
    debug_file : str, optional
        Debug output file name, by default "debug.txt"

    Returns
    -------
    None
        Writes total magnetization per site to output file
    """
    # Open debug file in append mode
    fd = open(debug_file, "a")

    # Read energy file
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")

    # Calculate total magnetization per site (negative of energy value divided by Nspin)
    tot_mag = -float(data[3].split()[1]) / Nspin
    print("tot_mag", tot_mag, file=fd)

    # Write result to output file
    with open(resul_mag, 'wt') as f:
        f.write(" {0:.16f} ".format(tot_mag) + "\n")

    fd.close()


def kitaev(input_dict, file_name="zvo_cisajs_eigen0.dat", resul_mag="resul_mag.dat"):
    """
    Calculate total magnetization for Kitaev model from correlation functions.

    Parameters
    ----------
    input_dict : dict
        Dictionary containing magnetic parameters:
        - mag.gab : float
            Coupling constant for x,y components
        - mag.gc : float
            Coupling constant for z component
    file_name : str, optional
        Input correlation file name, by default "zvo_cisajs_eigen0.dat"
    resul_mag : str, optional
        Output magnetization file name, by default "resul_mag.dat"

    Returns
    -------
    None
        Writes total magnetization to output file
    """
    # Extract coupling constants
    gab = input_dict["mag"]["gab"]
    gc = input_dict["mag"]["gc"]

    # Read correlation file
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")

    # Initialize spin components
    Sx = 0.0
    Sy = 0.0
    Sz = 0.0

    # Calculate spin components from correlations
    for i in range(0, len(data)):
        if data[i]:  # if data[i] is not empty
            tmp = data[i].split()
            if tmp[0] == tmp[2] and tmp[0] == '0':
                if tmp[1] == '0' and tmp[3] == '1':
                    Sx += float(tmp[4])
                    Sy += float(tmp[5])
                if tmp[1] == '1' and tmp[3] == '0':
                    Sx += float(tmp[4])
                    Sy += -1.0 * float(tmp[5])
                if tmp[1] == '0' and tmp[3] == '0':
                    Sz += float(tmp[4])
                if tmp[1] == '1' and tmp[3] == '1':
                    Sz += -1.0 * float(tmp[4])

    # Apply normalization factors
    Sx = 0.5 * Sx
    Sy = 0.5 * Sy
    Sz = 0.5 * Sz

    # Calculate total magnetization with coupling constants
    tot_mag = math.sqrt((gab * Sx) ** 2 + (gab * Sy) ** 2 + (gc * Sz) ** 2)
    print(Sx, Sy, Sz, tot_mag)

    # Write result to output file
    f = open(resul_mag, 'wt')
    f.write(" {0:.16f} ".format(tot_mag) + "\n")
    f.close()


if __name__ == "__main__":
    main(12)
