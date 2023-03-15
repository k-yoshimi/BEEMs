import h5py
import numpy as np
import os
import shutil
import tomli
import itertools
from copy import copy
from datetime import datetime
from subprocess import Popen

from . import BO_single
from . import makeall

def CallSolver(hphi_path, toml_file, target_data, dir_summary, hdf5, solver):
    solver_class = solver(hphi_path, toml_file, target_data, dir_summary, hdf5)
    return solver_class


class ProposeBase:

    def __init__(self, target_data, param_toml, input_toml, bo_dic):
        self.target_data = target_data
        self.param_toml = param_toml
        self.input_toml = input_toml
        self.bo_dic = bo_dic

    def _bo_single(self):
        print("_bo_single is not implemented.")
        return None

    def _make_all(self):
        print("_make_all is not implemented.")
        return None

    def _prep_data(self):
        print("_prep_data is not implemented.")
        return None

    def propose(self):
        self._prep_data()
        proposed_param = self._bo_single()
        self._make_all()
        return proposed_param

    def makeinput(self):
        proposed_param = self._bo_single()
        self._make_all()
        return proposed_param

class Propose(ProposeBase):

    def _preparation_data(self, param_toml):
        with open(param_toml, "rb") as f:
            dict_toml = tomli.load(f)["physbo"]

        param_cands = []
        for i, x in enumerate(dict_toml["params"]):
            param_cands.append(np.linspace(dict_toml[x][0], dict_toml[x][1], int(dict_toml[x][2])))

        X = np.array(list(itertools.product(*param_cands)))

        f = open("param.csv", "w")

        header = "delta,"
        for x in dict_toml["params"]:
            header += x + "_cand,"
        f.write(header[:-1] + "\n")

        for i in range(len(X)):
            for j in range(len(X[0])):
                f.write(",%f" % (X[i][j]))
            if i != len(X): f.write('\n')
        f.close()

    def _bo_single(self):
        proposed_param = BO_single.main(**self.bo_dic)
        return proposed_param

    def _make_all(self):
        makeall.main(self.input_toml, self.target_data)

    def _prep_data(self):
        self._preparation_data(self.param_toml)

class SearchHDF5Base:
    def __init__(self, h5):
        # h5: file object of hdf5.
        # param_keys: list of parameter names. ex) ["J", "J\'", "J\'\'"]
        # field_keys: list of field names. ex) ["H"]
        self.h5 = h5
        param_nums = list(h5["data/param"].keys())
        temp_li = list(h5["data/param"][param_nums[0]].keys())
        self.param_keys = [x for x in temp_li if x != "field"]
        temp_li = list(h5["data/param"][param_nums[0]]["field/keys"])
        self.field_keys = [x.decode("utf-8") for x in temp_li]


class SearchHDF5(SearchHDF5Base):
    def search(self, param_vals, field_vals):
        # param_vals: list of parameter values.
        # field_vals: list of field values.
        if len(param_vals) != len(self.param_keys):
            print("Error (SearchHDF5): len(param_vals) != len(self.param_keys)")
            exit(1)
        if len(field_vals) != len(self.field_keys):
            print("Error (SearchHDF5): len(field_vals) != len(self.field_keys)")
            exit(1)
        param_idx, field_idx = -1, -1

        for k, v in self.h5["data"]["param"].items():
            l = [v[param_key][()] for param_key in self.param_keys]

            if self.is_params_close(l, param_vals):
                param_idx = int(k)

                for i, value in enumerate(v["field"]["value"]):
                    if self.is_close(value, field_vals[0]):
                        field_idx = i

        return param_idx, field_idx

    def is_params_close(self, l_1, l_2, eps=1e-8):
        # Determine whether the lists are close or not.
        # eps: infinitesimal value (float)
        # Return False if the lengths of the lists do not match
        if len(l_1) != len(l_2):
            return False

        else:
            n = len(l_1)
            return all([self.is_close(l_1[i], l_2[i], eps) for i in range(n)])

    def is_close(self, x, y, eps=1e-8):
        # Determine whether the values are close or not.
        # eps: infinitesimal value (float)
        return abs(x - y) < eps


class WriteHDF5Base:
    def __init__(self, h5, index, param_keys, field_keys):
        # h5: file object of HDF5.
        # index: index of a chosen parameter.
        # param_keys: list of parameter names. ex) ["J", "J\'", "J\'\'"]
        # field_keys: list of field names. ex) ["H"]
        self.h5 = h5
        self.index = index
        self.param_keys = param_keys
        self.field_keys = field_keys
        self.index_param = index


class WriteHDF5(WriteHDF5Base):
    def write_param(self, param):
        if self.index < 0:
            g_param = self.h5["data/param/"]
            self.index_param = len(g_param)
            new_group = g_param.create_group("{}".format(self.index_param))
            for i, key in enumerate(self.param_keys):
                new_group[key] = param[i]
            new_group.create_group("field")

    def write_field(self, field_vals, output_path="output"):
        green1_list = []
        green1_idx_list = []
        green2_list = []
        green2_idx_list = []
        exct = self.h5["basic_info/exct"][()]
        for i in range(exct):
            green1_path = os.path.join(output_path, "zvo_cisajs_eigen{}.dat".format(i))
            green2_path = os.path.join(output_path, "zvo_cisajscktalt_eigen{}.dat".format(i))
            array1 = np.loadtxt(green1_path)
            array2 = np.loadtxt(green2_path)
            green1_idx_list.append(array1[:, :4].astype(np.int64))
            green2_idx_list.append(array2[:, :8].astype(np.int64))
            green1_list.append(array1[:, 4:])
            green2_list.append(array2[:, 8:])
        E = []
        E2 = []
        Sz = []
        energy_path = os.path.join(output_path, "zvo_energy.dat")
        with open(energy_path) as f:
            lines = f.readlines()
        for i in range(exct):
            energy_line = lines[6 * i + 1]
            sz_line = lines[6 * i + 2]
            E_tmp = float(energy_line.split()[1])
            E.append(E_tmp)
            E2.append(E_tmp ** 2)
            Sz.append(float(sz_line.split()[1]))
        # print(green1_idx_list, green2_idx_list, green1_list, green2_list)
        field = self.h5["data/param/{}/field".format(self.index_param)]

        if "keys" not in self.h5["data/param/{}/field".format(self.index_param)].keys():
            self.h5["data/param/{}/field/keys".format(self.index_param)] = self.field_keys
            calc_phys = field.create_group("calc_phys")
            sz2 = calc_phys.create_group("Sz2")
            info = calc_phys.create_group("info")
            field_vals_list = []
            e_list = []
            e2_list = []
            sz_list = []
            green1_list_list = []
            green2_list_list = []
            green1_idx_list_list = []
            green2_idx_list_list = []
            info_datetime = []
            info_degeneration = []
            info_env = []
            info_ver = []
        else:
            calc_phys = field["calc_phys"]
            sz2 = calc_phys["Sz2"]
            info = calc_phys["info"]
            field_vals_list = copy(list(field["value"]))
            del field["value"]
            e_list = copy(list(calc_phys["E"]))
            del calc_phys["E"]
            e2_list = copy(list(calc_phys["E2"]))
            del calc_phys["E2"]
            sz_list = copy(list(calc_phys["Sz"]))
            del calc_phys["Sz"]
            green1_list_list = copy(list(sz2["green1"]))
            del sz2["green1"]
            try:
                green2_list_list = copy(list(sz2["green2"]))
                del sz2["green2"]
            except:
                print("Warning: Error in deleting green2")
            green1_idx_list_list = copy(list(sz2["green1_idx"]))
            del sz2["green1_idx"]
            try:
                green2_idx_list_list = copy(list(sz2["green2_idx"]))
                del sz2["green2_idx"]
            except:
                print("Warning: Error in deleting green2_idx")
            info_datetime = copy(list(info["datetime"]))
            del info["datetime"]
            info_degeneration = copy(list(info["degeneration"]))
            del info["degeneration"]
            info_env = copy(list(info["env"]))
            del info["env"]
            info_ver = copy(list(info["ver"]))
            del info["ver"]
        field_vals_list.append(field_vals)
        e_list.append(E)
        e2_list.append(E2)
        sz_list.append(Sz)
        green1_list_list.append(green1_list)
        try:
            green2_list_list.append(green2_list)
        except:
            pass
        # print(green1_idx_list)
        green1_idx_list_list.append(green1_idx_list)
        # print(green1_idx_list_list)
        try:
            green2_idx_list_list.append(green2_idx_list)
        except:
            pass
        info_datetime.append("2022/08/29")
        info_degeneration.append(False)
        info_env.append("ohtaka")
        info_ver.append("3.4.3")
        # write HDF5
        field["value"] = field_vals_list
        calc_phys["E"] = e_list
        calc_phys["E2"] = e2_list
        calc_phys["Sz"] = sz_list
        sz2["green1"] = green1_list_list
        sz2["green1_idx"] = green1_idx_list_list
        try:
            sz2["green2"] = green2_list_list
            sz2["green2_idx"] = green2_idx_list_list
        except:
            print("Warning: Error occured for inserting green2 value")
        str_dtype = h5py.special_dtype(vlen=str)
        info.create_dataset("datetime", data=info_datetime, dtype=str_dtype)
        info["degeneration"] = info_degeneration
        info.create_dataset("env", data=info_env, dtype=str_dtype)
        info.create_dataset("ver", data=info_ver, dtype=str_dtype)
