import os
import pickle
from datetime import datetime
from subprocess import Popen

from . import Aft_mag
from . import diff
from ..BEEMs import WriteHDF5
from .SolverBase import SolverBase


class SolverHPhiStdGC(SolverBase):

    def _read_param_file(self):
        with open("stan.in") as f:
            input_str = f.read()
        lines = input_str.split("\n")
        dic_param = {}
        for line in lines:
            if "=" in line:
                vals = line.split("=")
                if "J" in vals[0] or "H" in vals[0]:
                    dic_param[vals[0].strip()] = float(vals[1])
        return dic_param

    def _run_hphi(self, logfile, sh5=None):
        flag_run_hphi = True
        dic_param = self._read_param_file()

        if sh5 != None:
            param_vals = [dic_param[key] for key in sh5.param_keys]
            field_vals = [dic_param[key] for key in sh5.field_keys]
            index_param, index_field = sh5.search(param_vals, field_vals)
            flag_run_hphi = (index_field < 0)
            out_index = index_param

        if flag_run_hphi:
            # HPhi dry run
            cmd = "{}/HPhi -sdry stan.in > std.out".format(self.hphi_path)
            popen = Popen(cmd, shell=True)
            popen.wait()
            # run HPhi
            cmd = "sh ../run_hphi.sh {}".format(self.hphi_path)
            popen = Popen(cmd, shell=True)
            popen.wait()
            # add data to HDF5 file
            if sh5 != None:
                wh5 = WriteHDF5(sh5.h5, index_param, sh5.param_keys, sh5.field_keys)
                if index_param < 0:
                    wh5.write_param(param_vals)
                    out_index = wh5.index_param
                wh5.write_field(field_vals)
                path_to_data = " (/data/param/{})".format(out_index)
                logfile="log"
                with open(logfile, "a") as f:
                    f.write("{}: Save data to HDF5{}.\n".format(datetime.now(), path_to_data))
        else:
            os.mkdir("output")
            with open("output/resul_mag.dat", "w") as f:
                Sz = sh5.h5["data/param/{}/field/calc_phys/Sz".format(index_param)][index_field][0]
                print("Sz:", Sz, file=fd)
                L = sh5.h5["basic_info/L"][()]
                print("L:", L, file=fd)
                f.write("{}".format(Sz / L))

    def _diff(self, num_bo):
        diff_mag = diff.main("BO_No{}".format(num_bo), self.target_data)
        return diff_mag

    def calcvalues(self, Nspin):
        mag_fields = self.target_data[:,0]
        csv = open("all_mag.csv", "w")
        for i in range(self.target_data.shape[0]):
            os.chdir("./h{}".format(i))
            if not os.path.isfile("resul_mag.dat"):
                Aft_mag.main(Nspin)
            os.chdir("../")
            with open("h{}/resul_mag.dat".format(i)) as fr:
                result = fr.read().rstrip()
            csv.write("{},{}\n".format(mag_fields[i], result))
        csv.close()
