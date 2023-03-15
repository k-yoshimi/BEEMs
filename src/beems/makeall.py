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
    input_dict = {}
    hphi_cond = {}
    input_dict.update(toml_dic)
    hphi_cond["path_hphi"] = os.path.join(toml_dic["path"]["hphi_dir"], "HPhi")
    hphi_cond["path_input_file"] = toml_dic["path"].get("stan", "stan.in")
    hphi_cond["path_energy_file"] = toml_dic["path"].get("energy", os.path.join(".","output","energy.dat"))
    HPhi_calc = hphi.hphi_io_spingc(hphi_cond)
    HPhi_calc.delete_input(["L"])
    HPhi_calc.run_dry(input_dict)

def output_stanin(toml_dic, mag_field):
    input_dict = {}
    hphi_cond = {}
    input_dict.update(toml_dic)
    hphi_cond["path_hphi"] = os.path.join(toml_dic["path"]["hphi_dir"], "HPhi")
    hphi_cond["path_input_file"] = toml_dic["path"].get("stan", "stan.in")
    hphi_cond["path_energy_file"] = toml_dic["path"].get("energy", os.path.join(".","output","energy.dat"))
    #[s]Comment: Is it better to replace the following function to hphi_io_base?
    HPhi_calc = hphi.hphi_io_spingc(hphi_cond)
    HPhi_calc.delete_input(["J0x", "J0y", "J0z", "J0'x", "J0'y", "J0'z", "J0''x", "J0''y", "J0''z", ])
    #[e]Comment: Is it better to replace the following function to hphi_io_base?

    #Genearate stan.in as a base file
    HPhi_calc.make_input_file(input_dict["hphi_params"])

    #Modify stan.in
    stanin_file = hphi_cond["path_input_file"]
    with open(stanin_file) as f:
        stan_str = f.read()
    for i, H in enumerate(mag_field):
        outstr = stan_str + "\nH = {}".format(H)
        with open("stan{}.in".format(i), "w") as f:
            f.write(outstr)

def func_readmag(file_name):
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
    input_file = input_toml
    with open(input_file, "rb") as f:
        input_dict = tomli.load(f)
    mag_field = target_data[:,0]
    # update stan.in
    output_stanin(input_dict, mag_field)

if __name__ == "__main__":
    main(sys.argv)
