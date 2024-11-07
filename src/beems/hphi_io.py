"""
Parameter Parallelization tools for HPhi.

This module provides classes for interfacing with HPhi quantum many-body solver,
including input/output handling and parameter management.

Classes
-------
hphi_io_base : Base class for HPhi I/O
hphi_io_spingc : Class for SpinGC model
hphi_io_spin : Class for Spin model  
hphi_io_hubbardgc : Class for HubbardGC model
hphi_io_hubbard : Class for Hubbard model
"""

import numpy as np
import os
import subprocess

class hphi_io_base(object):
    """
    Base class for HPhi input/output handling.

    Provides common functionality for reading/writing input files,
    running HPhi calculations, and extracting results.

    Parameters
    ----------
    _hphi_cond : dict
        Dictionary containing HPhi configuration with keys:
        - path_hphi : str
            Path to HPhi executable
        - path_input_file : str 
            Path to input file
        - path_output_file : str
            Path to output file
    """

    def __init__(self, _hphi_cond):
        """Initialize base HPhi I/O class."""
        self.input_param = {}
        self.path_hphi = _hphi_cond["path_hphi"]
        self.input_path = _hphi_cond["path_input_file"]
        self.energy_path = "./output/zvo_energy.dat"
        self.energy_list = []
        self.sz_list = []

    def _read_data(file_name):
        """
        Read data from file and parse into dictionary.

        Parameters
        ----------
        file_name : str
            Path to input file

        Returns
        -------
        dict
            Parsed data dictionary
        """
        import re
        dict_info = {}
        with open(file_name, "r") as fr:
            lines = fr.readlines()
            for line in lines:
                line = line.strip().replace(" ", "")
                # Get list
                list_re = re.search("\[.+\]", line)
                if list_re is not None:
                    modify_list = list_re.group()
                    List = re.split("[\(\)]", modify_list[1:-1])
                    List = filter(lambda str: str != "", List)
                    List = filter(lambda str: str != ",", List)
                    tmp_modify_info = {}
                    for idx, list_info in enumerate(List):
                        info = list_info.split(",")
                        tmp_modify_info[idx] = [float(info[0]), float(info[1])]
                    const_info = line[:list_re.start() - 1].split(",")[:-1]
                    dict_info[tuple(const_info)] = tmp_modify_info
        return dict_info

    def _make_input_file(self):
        """Make input file for HPhi using input_param dictionary."""
        with open(self.input_path, "w") as f:
            for key, item in self.input_param.items():
                f.write("{} = {}\n".format(key, item))

    def _change_input(self, input_dict):
        """
        Update input parameters with new values.

        Parameters
        ----------
        input_dict : dict
            Dictionary of parameters to update
        """
        for key, value in input_dict.items():
            self.input_param[key] = value

    def _get_energy_sz_from_hphi(self):
        """
        Get energy and Sz values from HPhi output.

        Returns
        -------
        tuple
            (energy_list, sz_list) containing energy and Sz values
        """
        energy_list = []
        sz_list = []
        if os.path.exists(self.energy_path):
            with open(self.energy_path, "r") as f:
                lines = f.readlines()
            for line in lines:
                line1 = line.split()
                if (line.find("Energy") != -1):
                    energy_list.append(float(line1[1]))
                elif (line.find("Sz") != -1):
                    sz_list.append(float(line1[1]))
        else:
            print("Error: {} is not existed.".format(self.energy_path))
            return None
        return energy_list, sz_list

    def make_input_file(self, input_dict):
        """
        Update parameters and create input file.

        Parameters
        ----------
        input_dict : dict
            Dictionary of parameters to update
        """
        self._change_input(input_dict)
        self._make_input_file()

    def run_dry(self, input_dict, path_to_file=None):
        """
        Run HPhi in dry mode to generate base input file.

        Parameters
        ----------
        input_dict : dict
            Dictionary of input parameters
        path_to_file : str, optional
            Path to input file, defaults to self.input_path
        """
        if path_to_file is None:
            path_to_file = self.input_path
        self._change_input(input_dict)
        self._make_input_file()
        cmd = "{} -sdry {} > std.out".format(self.path_hphi, path_to_file)
        subprocess.call(cmd, shell=True)

    def run_standard(self, path_to_file=None):
        """
        Run HPhi in standard mode.

        Parameters
        ----------
        path_to_file : str, optional
            Path to input file, defaults to self.input_path
        """
        if path_to_file is None:
            path_to_file = self.input_path
        cmd = "{} -s {} > std.out".format(self.path_hphi, path_to_file)
        subprocess.call(cmd, shell=True)

    def run_expert(self, path_to_file=None):
        """
        Run HPhi in expert mode.

        Parameters
        ----------
        path_to_file : str, optional
            Path to input file, defaults to self.input_path
        """
        if path_to_file is None:
            path_to_file = self.input_path
        cmd = "{} -e {} > std.out".format(self.path_hphi, path_to_file)
        subprocess.call(cmd, shell=True)

    def get_energy_sz_by_hphi(self, input_dict, ex_state=0):
        """
        Calculate and return energy and Sz for given state.

        Parameters
        ----------
        input_dict : dict
            Dictionary of input parameters
        ex_state : int, optional
            Excited state index (default: 0 for ground state)

        Returns
        -------
        tuple
            (energy, sz) for specified state
        """
        self._change_input(input_dict)
        self._make_input_file()
        cmd = "{} -s {} > std.out".format(self.path_hphi, self.input_path)
        subprocess.call(cmd, shell=True)
        values = self._get_energy_sz_from_hphi()
        if values is not None:
            energy, sz = values
            return (energy[ex_state], sz[ex_state])
        else:
            return None

    def get_input(self):
        """
        Get current input parameters.

        Returns
        -------
        dict
            Current input parameter dictionary
        """
        return self.input_param

    def delete_input(self, delete_keys_list):
        """
        Delete specified parameters from input.

        Parameters
        ----------
        delete_keys_list : list
            List of parameter keys to delete
        """
        for key in delete_keys_list:
            if key in self.input_param:
                del self.input_param[key]
            else:
                print("key {} is not included in input_param.".format(key))


class hphi_io_spingc(hphi_io_base):
    """
    Class for SpinGC model calculations.

    Inherits from hphi_io_base and adds SpinGC-specific functionality.

    Parameters
    ----------
    _hphi_cond : dict
        HPhi configuration dictionary
    """

    def __init__(self, _hphi_cond):
        """Initialize SpinGC model parameters."""
        super(hphi_io_spingc, self).__init__(_hphi_cond)
        self.input_param["model"] = "SpinGC"
        self.input_param["method"] = "CG"
        self.input_param["lattice"] = "chain"
        self.input_param["L"] = 16
        self.input_param["J0z"] = 1.0
        self.input_param["J0x"] = 1.0
        self.input_param["J0y"] = 1.0
        self.input_param["J0'z"] = 1.0
        self.input_param["J0'x"] = 1.0
        self.input_param["J0'y"] = 1.0
        self.input_param["J0''z"] = 1.0
        self.input_param["J0''x"] = 1.0
        self.input_param["J0''y"] = 1.0
        self.input_param["exct"] = 2

    def get_mag_from_file(self, file_name, parameter_list):
        """
        Get magnetization from file for given parameters.

        Parameters
        ----------
        file_name : str
            Path to input file
        parameter_list : list
            List of parameters to extract magnetization for

        Returns
        -------
        float
            Magnetization value
        """
        data = _read_data(file_name)
        data_parameter = {}
        mag = None
        for parameter in parameter_list:
            if parameter in data.keys():
                h = parameter[0]
                value = data[parameter]
                mag = self._modify_mag(h, value)
                data_parameter[parameter] = mag
        return mag

    def _modify_mag(self, h, data):
        """
        Calculate modified magnetization.

        Parameters
        ----------
        h : float
            Field strength
        data : dict
            Dictionary of eigenstate data

        Returns
        -------
        float
            Modified magnetization value
        """
        if np.isclose(data[0][0], data[1][0]):
            if h == 0.0:
                mag = 0.0
            else:
                mag = 0.5 * (data[0][1] + data[1][1])
        else:
            mag = data[0][1]
        return mag


class hphi_io_spin(hphi_io_base):
    """
    Class for Spin model calculations.

    Inherits from hphi_io_base and adds Spin-specific functionality.

    Parameters
    ----------
    _hphi_cond : dict
        HPhi configuration dictionary
    """

    def __init__(self, _hphi_cond):
        """Initialize Spin model parameters."""
        super(hphi_io_spin, self).__init__(_hphi_cond)
        self.input_param["model"] = "Spin"
        self.input_param["method"] = "CG"
        self.input_param["lattice"] = "chain"
        self.input_param["L"] = 12
        self.input_param["J0"] = 1.0
        self.input_param["exct"] = 2
        self.input_param["2Sz"] = 0

    def get_mag(self, sz_energy_list, H):
        """
        Calculate magnetization for given field strength.

        Parameters
        ----------
        sz_energy_list : list
            List of (Sz, energy) tuples
        H : float
            Field strength

        Returns
        -------
        float
            Magnetization value
        """
        energy_mag = []
        for sz_energy in sz_energy_list:
            energy_mag.append(sz_energy[1] - sz_energy[0] * H)
        min_index = energy_mag.index(min(energy_mag))
        return sz_energy_list[min_index][0]

    def _get_energy_from_hphi(self):
        """
        Extract energy values from HPhi output.

        Returns
        -------
        list
            List of energy values
        """
        energy_list = []
        if os.path.exists("./output/zvo_energy.dat"):
            str_output = "./output/zvo_energy.dat"
            with open(str_output, "r") as f:
                lines = f.readlines()
            for line in lines:
                line1 = line.split()
                if (line.find("Energy") != -1):
                    energy_list.append(float(line1[1]))
        return energy_list

    def get_energy_by_hphi(self, input_dict):
        """
        Calculate energies for all possible Sz values.

        Parameters
        ----------
        input_dict : dict
            Dictionary of input parameters

        Returns
        -------
        list
            List of (Sz, energy) tuples
        """
        self._change_input(input_dict)
        # update 2Sz
        L = self.input_param["L"]
        energy_list = []
        for sz in range(L // 2 + 1):
            self.input_param["2Sz"] = 2 * sz
            self._make_input_file()
            cmd = "{} -s {}".format(self.path_hphi, self.input_path)
            subprocess.call(cmd.split())
            energy = self._get_energy_from_hphi()
            energy_list.append((sz, energy[0]))
        self.energy_list = energy_list
        return energy_list


class hphi_io_hubbardgc(hphi_io_base):
    """
    Class for HubbardGC model calculations.

    Inherits from hphi_io_base and adds HubbardGC-specific functionality.

    Parameters
    ----------
    _hphi_cond : dict
        HPhi configuration dictionary
    """

    def __init__(self, _hphi_cond):
        """Initialize HubbardGC model parameters."""
        super(hphi_io_hubbardgc, self).__init__(_hphi_cond)
        self.input_param["model"] = "HubbardGC"
        self.input_param["method"] = "CG"
        self.input_param["lattice"] = "chain"
        self.input_param["L"] = 8
        self.input_param["t"] = 1.0
        self.input_param["U"] = 4.0
        self.input_param["exct"] = 2


class hphi_io_hubbard(hphi_io_base):
    """
    Class for Hubbard model calculations.

    Inherits from hphi_io_base and adds Hubbard-specific functionality.

    Parameters
    ----------
    _hphi_cond : dict
        HPhi configuration dictionary
    """

    def __init__(self, _hphi_cond):
        """Initialize Hubbard model parameters."""
        super(hphi_io_spingc, self).__init__(_hphi_cond)
        self.input_param["model"] = "Hubbard"
        self.input_param["method"] = "CG"
        self.input_param["lattice"] = "chain"
        self.input_param["L"] = 8
        self.input_param["nelec"] = 8.0
        self.input_param["t"] = 1.0
        self.input_param["U"] = 4.0
        self.input_param["exct"] = 2


if __name__ == '__main__':
    hphi_cond = {}
    hphi_cond["path_hphi"] = "./HPhi"
    hphi_cond["path_input_file"] = "./stan.in"
    hphi_cond["path_energy_file"] = "./output/zvo_energy.dat"
    HPhi_calc = hphi_io_spingc(hphi_cond)
    HPhi_calc.delete_input(["J0z"])
    HPhi_calc.delete_input(["J0z`"])

    print(HPhi_calc.get_input())
    input_dict = {}
    input_dict["J0z"] = -1.0

    print(HPhi_calc.get_input())
