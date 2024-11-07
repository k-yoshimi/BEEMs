# Copyright Ryo Tamura
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 

# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 

# You should have received a copy of the GNU General Public License 
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 
# -------------------------------------------------------------

import itertools
import numpy as np
import pickle
import sys
import tomli
import os
from . import hphi_io as hphi

def output_def(toml_dic):
    """
    Generate default HPhi input file from TOML configuration.

    Parameters
    ----------
    toml_dic : dict
        Dictionary containing HPhi configuration parameters from TOML file

    Returns
    -------
    None
        Writes HPhi input file to disk
    """
    input_dict = {}
    hphi_cond = {}
    input_dict.update(toml_dic)
    # Set HPhi executable path
    hphi_cond["path_hphi"] = os.path.join(toml_dic["path"]["hphi_dir"], "HPhi")
    # Set input/output file paths
    hphi_cond["path_input_file"] = toml_dic["path"].get("stan", "stan.in")
    hphi_cond["path_energy_file"] = toml_dic["path"].get("energy", os.path.join(".","output","energy.dat"))
    HPhi_calc = hphi.hphi_io_spingc(hphi_cond)
    HPhi_calc.delete_input(["L"])
    HPhi_calc.run_dry(input_dict)

def output_stanin(toml_dic, mag_field):
    """
    Generate HPhi input files with magnetic field values.

    Parameters
    ----------
    toml_dic : dict
        Dictionary containing HPhi configuration parameters from TOML file
    mag_field : array_like
        Array of magnetic field values to use

    Returns
    -------
    None
        Writes multiple HPhi input files to disk, one for each magnetic field value
    """
    input_dict = {}
    hphi_cond = {}
    input_dict.update(toml_dic)
    # Set HPhi executable path
    hphi_cond["path_hphi"] = os.path.join(toml_dic["path"]["hphi_dir"], "HPhi")
    # Set input/output file paths
    hphi_cond["path_input_file"] = toml_dic["path"].get("stan", "stan.in")
    hphi_cond["path_energy_file"] = toml_dic["path"].get("energy", os.path.join(".","output","energy.dat"))
    
    # Initialize HPhi calculator
    HPhi_calc = hphi.hphi_io_spingc(hphi_cond)
    # Remove existing J parameters
    HPhi_calc.delete_input(["J0x", "J0y", "J0z", "J0'x", "J0'y", "J0'z", "J0''x", "J0''y", "J0''z", ])

    # Generate base stan.in file
    HPhi_calc.make_input_file(input_dict["hphi_params"])

    # Create modified input files for each magnetic field value
    stanin_file = hphi_cond["path_input_file"]
    with open(stanin_file) as f:
        stan_str = f.read()
    for i, H in enumerate(mag_field):
        outstr = stan_str + "\nH = {}".format(H)
        with open("stan{}.in".format(i), "w") as f:
            f.write(outstr)

def func_readmag(file_name):
    """
    Read magnetic field and magnetization data from file.

    Parameters
    ----------
    file_name : str
        Path to input file containing field and magnetization data

    Returns
    -------
    tuple
        field : ndarray
            Array of magnetic field values
        mag : ndarray
            Array of magnetization values
    """
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")
    cnt_max = len(data) - 1
    field = np.zeros([cnt_max], dtype=np.float64)
    mag = np.zeros([cnt_max], dtype=np.float64)
    for i in range(0, cnt_max):
        if data[i]:  # if data[i] is not empty
            tmp = data[i].split(",")
            field[i] = float(tmp[0])
            mag[i] = float(tmp[1])
    return field, mag


def main(input_toml, target_data):
    """
    Main function to generate HPhi input files.

    Parameters
    ----------
    input_toml : str
        Path to input TOML configuration file
    target_data : ndarray
        Array containing target magnetic field values

    Returns
    -------
    None
        Generates HPhi input files
    """
    input_file = input_toml
    with open(input_file, "rb") as f:
        input_dict = tomli.load(f)
    mag_field = target_data[:,0]
    # Generate input files with magnetic field values
    output_stanin(input_dict, mag_field)

if __name__ == "__main__":
    main(sys.argv)
