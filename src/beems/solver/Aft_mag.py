import cmath
import copy
import math
import numpy as np
import os
import sys


def main(Nspin, file_name="zvo_energy.dat", resul_mag="resul_mag.dat", debug_file="debug.txt"):
    fd = open(debug_file, "a")
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")
    tot_mag = -float(data[3].split()[1]) / Nspin
    print("tot_mag", tot_mag, file=fd)
    with open(resul_mag, 'wt') as f:
        f.write(" {0:.16f} ".format(tot_mag) + "\n")
    # print("Sz:", tot_mag)
    fd.close()


def kitaev(input_dict, file_name="zvo_cisajs_eigen0.dat", resul_mag="resul_mag.dat"):
    gab = input_dict["mag"]["gab"]
    gc = input_dict["mag"]["gc"]
    with open(file_name) as f:
        data = f.read()
        data = data.split("\n")
        print(len(data))
        # [s] count not empty elements
    cnt = 0
    Sx = 0.0
    Sy = 0.0
    Sz = 0.0
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
    Sx = 0.5 * Sx
    Sy = 0.5 * Sy
    Sz = 0.5 * Sz
    tot_mag = math.sqrt((gab * Sx) ** 2 + (gab * Sy) ** 2 + (gc * Sz) ** 2)
    print(Sx, Sy, Sz, tot_mag)
    f = open(resul_mag, 'wt')
    f.write(" {0:.16f} ".format(tot_mag) + "\n")
    f.close()


if __name__ == "__main__":
    main(12)
