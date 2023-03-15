import math


def get_h(stanin):
    with open(stanin) as f:
        lines = f.readlines()
    for line in lines:
        if "=" in line:
            vals = line.split("=")
            vals = [x.strip() for x in vals]
            if vals[0] == "H":
                H = float(vals[1])
                break
    return H


def convert_stanin_kitaev(stanin):
    keys = ["K", "G", "GP", "G2", "GP2", "J", "J2", "J3"]
    with open(stanin) as f:
        lines = f.readlines()
    dic_param = {}
    lines_out = []
    for line in lines:
        if "=" in line:
            vals = line.split("=")
            vals = [x.strip() for x in vals]
            if vals[0] in keys:
                dic_param[vals[0]] = float(vals[1])
            else:
                if vals[0] != "L":
                    if line[-1] != "\n":
                        line += "\n"
                    lines_out.append(line)
    dic_kitaev = get_dic_kitaev(dic_param)
    for key in dic_kitaev.keys():
        lines_out.append("{} = {}\n".format(key, dic_kitaev[key]))
    with open(stanin, "w") as f:
        for line in lines_out:
            f.write(line)


def get_dic_kitaev(dic_param):
    kitaev_params = {"K": 0.0, "G": 0.0, "GP": 0.0, "G2": 0.0, "GP2": 0.0, "J": 0.0, "J2": 0.0, "J3": 0.0}
    kitaev_params.update(dic_param)

    K = kitaev_params["K"]
    G = kitaev_params["G"]
    GP = kitaev_params["GP"]
    G2 = kitaev_params["G2"]
    GP2 = kitaev_params["GP2"]
    J = kitaev_params["J"]
    J2 = kitaev_params["J2"]
    J3 = kitaev_params["J3"]

    dic_kitaev = {}
    # J0 x-bond
    dic_kitaev["J0x"] = J + K
    dic_kitaev["J0y"] = J
    dic_kitaev["J0z"] = J
    dic_kitaev["J0yz"] = G
    dic_kitaev["J0zy"] = G
    dic_kitaev["J0xy"] = GP
    dic_kitaev["J0yx"] = GP
    dic_kitaev["J0zx"] = GP
    dic_kitaev["J0xz"] = GP
    dic_kitaev["J0'x"] = J2
    dic_kitaev["J0'y"] = J2
    dic_kitaev["J0'z"] = J2
    dic_kitaev["J0'yz"] = G2
    dic_kitaev["J0'zy"] = G2
    dic_kitaev["J0'xy"] = GP2
    dic_kitaev["J0'yx"] = GP2
    dic_kitaev["J0'zx"] = GP2
    dic_kitaev["J0'xz"] = GP2
    dic_kitaev["J0''x"] = J3
    dic_kitaev["J0''y"] = J3
    dic_kitaev["J0''z"] = J3
    # J1 y-bond
    dic_kitaev["J1x"] = J
    dic_kitaev["J1y"] = J + K
    dic_kitaev["J1z"] = J
    dic_kitaev["J1yz"] = GP
    dic_kitaev["J1zy"] = GP
    dic_kitaev["J1xy"] = GP
    dic_kitaev["J1yx"] = GP
    dic_kitaev["J1zx"] = G
    dic_kitaev["J1xz"] = G
    dic_kitaev["J1'x"] = J2
    dic_kitaev["J1'y"] = J2
    dic_kitaev["J1'z"] = J2
    dic_kitaev["J1'yz"] = GP2
    dic_kitaev["J1'zy"] = GP2
    dic_kitaev["J1'xy"] = GP2
    dic_kitaev["J1'yx"] = GP2
    dic_kitaev["J1'zx"] = G2
    dic_kitaev["J1'xz"] = G2
    dic_kitaev["J1''x"] = J3
    dic_kitaev["J1''y"] = J3
    dic_kitaev["J1''z"] = J3
    # J2 z-bond
    dic_kitaev["J2x"] = J
    dic_kitaev["J2y"] = J
    dic_kitaev["J2z"] = J + K
    dic_kitaev["J2yz"] = GP
    dic_kitaev["J2zy"] = GP
    dic_kitaev["J2xy"] = G
    dic_kitaev["J2yx"] = G
    dic_kitaev["J2zx"] = GP
    dic_kitaev["J2xz"] = GP
    dic_kitaev["J2'x"] = J2
    dic_kitaev["J2'y"] = J2
    dic_kitaev["J2'z"] = J2
    dic_kitaev["J2'yz"] = GP2
    dic_kitaev["J2'zy"] = GP2
    dic_kitaev["J2'xy"] = G2
    dic_kitaev["J2'yx"] = G2
    dic_kitaev["J2'zx"] = GP2
    dic_kitaev["J2'xz"] = GP2
    dic_kitaev["J2''x"] = J3
    dic_kitaev["J2''y"] = J3
    dic_kitaev["J2''z"] = J3
    return dic_kitaev


def get_site_number(file_name="locspn.def"):
    with open(file_name, "r") as fw:
        lines = fw.readlines()
        Nsites = int(lines[1].split()[1])

    return Nsites


def mod_trans(H, Nsites, dict_mag):
    amp_z = dict_mag["amp_z"]
    amp_tot = dict_mag["amp_tot"]
    theta = dict_mag["theta"]
    phi = dict_mag["phi"]
    gab = dict_mag["gab"]
    gc = dict_mag["gc"]
    bohr = dict_mag["bohr"]

    h = amp_tot * H

    hx = gab * bohr * h * math.sin(math.pi * theta) * math.cos(math.pi * phi)
    hy = gab * bohr * h * math.sin(math.pi * theta) * math.sin(math.pi * phi)
    hz = gc * bohr * h * amp_z * math.cos(math.pi * theta)
    num_param = 4 * Nsites
    f = open("trans.def", "w")
    f.write("===================" + "\n")
    f.write("num " + "{0:8d}".format(num_param) + "\n")
    f.write("===================" + "\n")
    f.write("===================" + "\n")
    f.write("===================" + "\n")
    for cnt in range(0, Nsites):
        all_i = cnt
        #
        f.write(" {0:8d} ".format(all_i) \
                + " {0:8d}   ".format(0) \
                + " {0:8d}   ".format(all_i) \
                + " {0:8d}   ".format(1) \
                + " {0:8f}   ".format(-0.5 * hx) \
                + " {0:8f}   ".format(0.5 * hy) \
                + "\n")
        #
        f.write(" {0:8d} ".format(all_i) \
                + " {0:8d}   ".format(1) \
                + " {0:8d}   ".format(all_i) \
                + " {0:8d}   ".format(0) \
                + " {0:8f}   ".format(-0.5 * hx) \
                + " {0:8f}   ".format(-0.5 * hy) \
                + "\n")
        #
        f.write(" {0:8d} ".format(all_i) \
                + " {0:8d}   ".format(0) \
                + " {0:8d}   ".format(all_i) \
                + " {0:8d}   ".format(0) \
                + " {0:8f}   ".format(-0.5 * hz) \
                + " {0:8f}   ".format(0.0) \
                + "\n")
        #
        f.write(" {0:8d} ".format(all_i) \
                + " {0:8d}   ".format(1) \
                + " {0:8d}   ".format(all_i) \
                + " {0:8d}   ".format(1) \
                + " {0:8f}   ".format(0.5 * hz) \
                + " {0:8f}   ".format(0.0) \
                + "\n")
        #
    f.close()


def make_one_body_G_site0(file_name="greenone.def"):
    with open(file_name, "w") as fw:
        fw.write("===================" + "\n")
        fw.write("num 8 \n")
        fw.write("===================" + "\n")
        fw.write("===================" + "\n")
        fw.write("===================" + "\n")
        fw.write("  0     0     0     1\n")
        fw.write("  0     1     0     0\n")
        fw.write("  0     0     0     0\n")
        fw.write("  0     1     0     1\n")
        fw.write("  1     0     1     1\n")
        fw.write("  1     1     1     0\n")
        fw.write("  1     0     0     0\n")
        fw.write("  1     1     1     1\n")


if __name__ == "__main__":
    stanin = "stan_kitaev.in"
    convert_stanin_kitaev(stanin)
