import os
import pickle
import tomli
from subprocess import Popen

import Aft_mag
from SolverHPhiStdGC import SolverHPhiStdGC
from func_kitaev import *


class SolverKitaev(SolverHPhiStdGC):

    def _run_hphi(self, i):
        # get magnetic field and convert kitaev params to HPhi params
        H = get_h("stan.in")
        dict_mag = tomli.load(self.toml_file)["mag"]
        convert_stanin_kitaev("stan.in")
        # HPhi dry run
        cmd = "{}/HPhi -sdry stan.in > std.out".format(self.hphi_path)
        popen = Popen(cmd, shell=True)
        popen.wait()
        Nsites = get_site_number()
        # mod trans.def using H and dict_mag
        make_one_body_G_site0()
        mod_trans(H, Nsites, dict_mag)
        # run HPhi
        cmd = "sh ../run_hphi.sh {}".format(self.hphi_path)
        print("start running HPhi {}".format(i), datetime.now())
        popen = Popen(cmd, shell=True)
        popen.wait()
        print("end running HPhi {}".format(i), datetime.now())

    def calcvalues(self):
        with open("mag_field.pkl", "rb") as f:
            mag_fields = pickle.load(f)
        csv = open("all_mag.csv", "w")
        for i in range(self.num_param):
            os.chdir("./h{}".format(i))
            input_dict = tomli.load("../" + self.toml_file)
            Aft_mag.kitaev(input_dict)
            os.chdir("../")
            with open("h{}/resul_mag.dat".format(i)) as fr:
                result = fr.read().rstrip().lstrip("[").rstrip("]")
            csv.write("{},{}\n".format(mag_fields[i], result))
        csv.close()
