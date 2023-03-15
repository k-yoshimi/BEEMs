import glob
import os
import pandas as pd
import shutil
import tomli
import numpy as np

from . import BEEMs
from .solver.SolverHPhiStdGC import SolverHPhiStdGC


def get_best_delta(csv_file):
    """
    get the best delta from the csv file
    :param csv_file: csv file name
    :return: best delta, best parameters
    """
    df = pd.read_csv(csv_file)
    i_best = df["delta"].idxmax()
    best_delta = df["delta"][i_best]
    params_list = df.columns.values
    best_parameters = {}
    for param in params_list:
        if param != "delta":
            best_parameters[param.split("_")[0]] = df[param][i_best]
    return best_delta, best_parameters

def get_num_spin(param_toml):
    """
    get the number of spins from the toml file
    :param param_toml: toml file name
    :return: number of spins
    """
    with open(param_toml, "rb") as f:
        input_dict = tomli.load(f)
    if input_dict["hphi_params"]["lattice"].lower() == "chain":
        num_spin = input_dict["hphi_params"]["L"]
    else:
        num_spin = input_dict["hphi_params"]["L"] * input_dict["hphi_params"]["W"]
    return num_spin

def run_beems(max_itr, target_data, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic,
              hdf5, restart):
    """
    run BEEMs
    :param max_itr: maximum number of iterations
    :param num_h: number of magnetic fields
    :param target_csv: target csv file
    :param hphi_dir: directory of HPhi
    :param orig_dir: directory of original files
    :param summary_dir: directory of summary
    :param param_toml: toml file name
    :param input_toml: toml file name
    :param bo_dic: dictionary of BO
    :param hdf5: hdf5 file name
    :param restart: restart flag
    :return: None
    """
    # prepare classes
    Nspin = get_num_spin(param_toml)
    propose = BEEMs.Propose(target_data, param_toml, input_toml, bo_dic)
    solver = BEEMs.CallSolver(hphi_dir, input_toml, target_data, summary_dir, hdf5, solver=SolverHPhiStdGC)
    sh5 = None
    if hdf5 != None:
        sh5 = BEEMs.SearchHDF5(hdf5)

    cwd = os.getcwd()
    max_num = 0

    with open(param_toml, "rb") as f:
        dic_toml = tomli.load(f)
        num_random = dic_toml["physbo"].get("num_random", 3)
        logfile = dic_toml["physbo"].get("log", "log")

    if restart is True:
        l = glob.glob(os.path.join(summary_dir, "BO_No*"))
        nums = []
        if l == []:
            restart = False
        else:
            for bo_dir in l:
                nums.append(int(bo_dir.split("/")[-1].replace("BO_No", "")))
            max_num = max(nums)
            print("Restart from BO_No{} ...".format(max_num+1))

    if restart is False:
        os.chdir(orig_dir)
        # initialize
        propose.propose()
        os.chdir(cwd)
        os.mkdir(summary_dir)

    for i in range(max_num+1, max_itr+1):
        run_type = "Bayesian Optimization"
        if i <= num_random:
            run_type = "Random"
        print("Iteration Number {} ({})".format(i , run_type))
        shutil.copytree(orig_dir, "BO_No{}".format(i), ignore=shutil.ignore_patterns("param.csv"))
        # delete stan files
        for file in glob.glob(os.path.join(orig_dir, "stan*.in")):
            os.remove(file)
        os.chdir("BO_No{}".format(i))
        # preprocess
        print("Make input files.")
        proposed_param = propose.makeinput()
        shutil.move(input_toml, os.path.join(cwd,"BO_No{}".format(i)))
        print("Proposed parameters: {}".format(proposed_param))
        # runner
        print("Calculate observables.")
        solver.run(logfile, sh5)
        solver.calcvalues(Nspin)
        os.chdir(cwd)
        # postprocess
        diff = solver.cost(i)
        print("Current score: {}".format(diff))
        # output best_delta
        get_best_diff, get_best_parameters = get_best_delta(os.path.join(orig_dir, "param.csv"))
        with open(os.path.join(orig_dir, "best.csv"), "a") as f:
            f.write("{},{}\n".format(i, get_best_diff))
        shutil.copyfile(os.path.join(orig_dir, "best.csv"), os.path.join(summary_dir, "BO_No{}".format(i), "best.csv"))
        print("Current best score: {}".format(get_best_diff))
        print("Current best parameters: {}".format(get_best_parameters))
        print("End Iteration Number {}\n".format(i))


def main():
    import argparse
    import tomli
    import pathlib
    import h5py

    parser = argparse.ArgumentParser()
    parser.add_argument('toml')
    parser.add_argument('-hd', '--hdf', default="")
    parser.add_argument('--outfig', action='store_true')
    parser.add_argument('--uuid', action='store_true')
    args = parser.parse_args()

    print("Read TOML file {} ...".format(args.toml))
    with open(args.toml, "rb") as f:
        dic = tomli.load(f)
    
    param_toml = pathlib.Path(args.toml).resolve()
    max_itr = dic["physbo"]["max_itr"]
    restart_flag = eval(dic["physbo"].get("restart", "True"))
    target_csv = pathlib.Path(dic["path"]["target_csv"]).resolve()
    hphi_dir = pathlib.Path(dic["path"]["hphi_dir"]).resolve()
    orig_dir = "org"
    input_toml = dic["path"].get("input_toml", "input.toml")
    input_toml = pathlib.Path(input_toml).resolve()
    summary_dir = dic["path"].get("summary_dir", "Sum")
    summary_dir = pathlib.Path(summary_dir).resolve()

    def _check_hdf5(hdf5, param_toml):
        error_code = 0
        error_param_list = []
        for key in hdf5["basic_info"].keys():
            dat_hdf5 = hdf5["basic_info"][key][()]
            if type(dat_hdf5) == type(b""):
                dat_hdf5 = dat_hdf5.decode("utf-8")
            if key != "uuid" and not dat_hdf5 == param_toml["hphi_params"][key]:
                print("Error: parameter '{}' in HDF5 file does not equal to '{}' in TOML file".format(key, key))
                print("    in HDF5: {}, in TOML: {}".format(dat_hdf5, param_toml["hphi_params"][key]))
                error_code = 1
                error_param_list.append(key)
        return error_code, error_param_list

    # check
    hdf5 = None
    if args.hdf != "":
        hdf5 = h5py.File(args.hdf, 'a')
        print("Check HDF5 file {} and TOML file {} ...".format(args.hdf, args.toml))
        error_code, error_param_list = _check_hdf5(hdf5, dic)
        if error_code != 0:
            print("Error in parameter {}".format(error_param_list))
            exit()
        print("OK.")

    if args.uuid:
        def _add_uuid_to_h5(h5, replace=False):
            import uuid
            binfo = h5["basic_info"]
            str_dtype = h5py.special_dtype(vlen=str)
            if "uuid" in binfo.keys():
                if replace:
                    del binfo["uuid"]
                    id = str(uuid.uuid4())
                    print("UUID: {}".format(id))
                    binfo.create_dataset("uuid", data=id, dtype=str_dtype)
                else:
                    print("Warning: uuid already exists. Skip making uuid.")
            else:
                id = str(uuid.uuid4())
                print("UUID: {}".format(id))
                binfo.create_dataset("uuid", data=id, dtype=str_dtype)

        if hdf5:
            print("Add UUID to HDF5 file...")
            _add_uuid_to_h5(hdf5, replace=False)
            print("OK.")
        else:
            print("Warning: No input HDF5 file. Cannot add UUID.")

    print("Read target csv file {} ...".format(target_csv))
    if target_csv is None:
        print("params.toml is invalid.")
        print("target_csv is not found.")
        exit(1)

    if not os.path.exists(target_csv):
        print("File not found: {}".format(target_csv))
        exit(1)
        
    target_data = np.loadtxt(target_csv, delimiter=',', dtype=np.float64)
    num_h = target_data.shape[0]

    # restart mode
    BO_dir = glob.glob("BO_No*")[0] if len(glob.glob("BO_No*")) != 0 else "BO_None"
    if restart_flag is True:
        if os.path.isdir(summary_dir):
            if BO_dir in ["BO_No1"]:
                #To make org directory, restart_flag changes to False
                restart_flag = False
            else:
                print("Restart mode.")
                if os.path.isdir(BO_dir):
                    print("Warning: {} already exists. It will be deleted.".format(BO_dir))
                    shutil.rmtree(BO_dir)
        else:
            print("Warning: Summary directory does not exist. Restart flag changes to False.")
            restart_flag = False

    if restart_flag is False:
        print("New mode.")
        for d in [orig_dir, summary_dir, BO_dir]:
            if os.path.isdir(d):
                print("Warning: {} already exists. It will be deleted.".format(d))
                shutil.rmtree(d)

    bo_dic = {"param_toml": param_toml,
              "input_toml": input_toml}

    if not os.path.exists(orig_dir):
        os.mkdir(orig_dir)

    print("Start BEEMs (max_itr={}, num_h={}, target_csv={}, hphi_dir={}, orig_dir={}, summary_dir={}, param_toml={}, input_toml={}, bo_dic={}, hdf5={}, restart={})".format(
        max_itr, num_h, target_csv, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic, hdf5, restart_flag))
    run_beems(max_itr, target_data, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic,
              hdf5, restart_flag)
    print("Finish BEEMs (max_itr={}, num_h={}, target_csv={}, hphi_dir={}, orig_dir={}, summary_dir={}, param_toml={}, input_toml={}, bo_dic={}, hdf5={}, restart={})".format(
        max_itr, num_h, target_csv, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic, hdf5, restart_flag))

    if args.outfig:
        print("Output best results to best.png")
        import matplotlib.pyplot as plt
        import pandas as pd
        csvfile = os.path.join(orig_dir, "best.csv")
        df = pd.read_csv(csvfile, names=["steps", "delta"])
        fig, ax = plt.subplots()
        ax.set_xlabel("steps")
        ax.set_ylabel("delta")
        ax.plot(df["steps"], df["delta"])
        fig.savefig(os.path.join(orig_dir, "best.png"))

    if hdf5 != None:
        hdf5.close()


if __name__ == "__main__":
    main()
