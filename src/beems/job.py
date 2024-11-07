"""
Main module for running BEEMs (Bayesian Experimental Ensemble Method) optimization.

This module provides functions for running BEEMs optimization using PHYSBO and HPhi,
including parameter loading, optimization execution, and result analysis.
"""

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
    Get the best delta value and corresponding parameters from CSV file.

    Parameters
    ----------
    csv_file : str
        Path to CSV file containing optimization results

    Returns
    -------
    float
        Best delta value found
    dict
        Dictionary of parameters corresponding to best delta
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
    Get number of spins from TOML configuration file.

    Parameters
    ----------
    param_toml : str
        Path to TOML parameter file

    Returns
    -------
    int
        Number of spins in the system
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
    Run BEEMs optimization procedure.

    Parameters
    ----------
    max_itr : int
        Maximum number of iterations
    target_data : ndarray
        Target data to optimize against
    hphi_dir : str
        Directory containing HPhi executable
    orig_dir : str
        Directory for original input files
    summary_dir : str
        Directory for optimization results
    param_toml : str
        Path to parameter TOML file
    input_toml : str
        Path to input TOML file
    bo_dic : dict
        Dictionary of Bayesian optimization parameters
    hdf5 : h5py.File or None
        HDF5 file for storing results
    restart : bool
        Whether to restart from previous optimization

    Returns
    -------
    None
    """
    # Prepare classes
    Nspin = get_num_spin(param_toml)
    propose = BEEMs.Propose(target_data, param_toml, input_toml, bo_dic)
    solver = BEEMs.CallSolver(hphi_dir, input_toml, target_data, summary_dir, hdf5, solver=SolverHPhiStdGC)
    sh5 = None
    if hdf5 != None:
        sh5 = BEEMs.SearchHDF5(hdf5)

    cwd = os.getcwd()
    max_num = 0

    # Load configuration
    with open(param_toml, "rb") as f:
        dic_toml = tomli.load(f)
        num_random = dic_toml["physbo"].get("num_random", 3)
        logfile = dic_toml["physbo"].get("log", "log")

    # Handle restart case
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

    # Initialize if not restarting
    if restart is False:
        os.chdir(orig_dir)
        propose.propose()
        os.chdir(cwd)
        os.mkdir(summary_dir)

    # Main optimization loop
    for i in range(max_num+1, max_itr+1):
        run_type = "Bayesian Optimization"
        if i <= num_random:
            run_type = "Random"
        print("Iteration Number {} ({})".format(i , run_type))
        shutil.copytree(orig_dir, "BO_No{}".format(i), ignore=shutil.ignore_patterns("param.csv"))
        # Delete stan files
        for file in glob.glob(os.path.join(orig_dir, "stan*.in")):
            os.remove(file)
        os.chdir("BO_No{}".format(i))
        
        # Preprocess
        print("Make input files.")
        proposed_param = propose.makeinput()
        shutil.move(input_toml, os.path.join(cwd,"BO_No{}".format(i)))
        print("Proposed parameters: {}".format(proposed_param))
        
        # Run solver
        print("Calculate observables.")
        solver.run(logfile, sh5)
        solver.calcvalues(Nspin)
        os.chdir(cwd)
        
        # Postprocess
        diff = solver.cost(i)
        print("Current score: {}".format(diff))
        
        # Output best results
        get_best_diff, get_best_parameters = get_best_delta(os.path.join(orig_dir, "param.csv"))
        with open(os.path.join(orig_dir, "best.csv"), "a") as f:
            f.write("{},{}\n".format(i, get_best_diff))
        shutil.copyfile(os.path.join(orig_dir, "best.csv"), os.path.join(summary_dir, "BO_No{}".format(i), "best.csv"))
        print("Current best score: {}".format(get_best_diff))
        print("Current best parameters: {}".format(get_best_parameters))
        print("End Iteration Number {}\n".format(i))


def main():
    """
    Main function to run BEEMs optimization from command line.

    Parses command line arguments, sets up optimization parameters,
    and executes the BEEMs optimization procedure.
    """
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
        """
        Check consistency between HDF5 and TOML parameters.

        Parameters
        ----------
        hdf5 : h5py.File
            HDF5 file to check
        param_toml : dict
            TOML parameters to check against

        Returns
        -------
        int
            Error code (0 if no errors)
        list
            List of parameters with errors
        """
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

    # Check HDF5 file if provided
    hdf5 = None
    if args.hdf != "":
        hdf5 = h5py.File(args.hdf, 'a')
        print("Check HDF5 file {} and TOML file {} ...".format(args.hdf, args.toml))
        error_code, error_param_list = _check_hdf5(hdf5, dic)
        if error_code != 0:
            print("Error in parameter {}".format(error_param_list))
            exit()
        print("OK.")

    # Handle UUID generation if requested
    if args.uuid:
        def _add_uuid_to_h5(h5, replace=False):
            """
            Add UUID to HDF5 file.

            Parameters
            ----------
            h5 : h5py.File
                HDF5 file to add UUID to
            replace : bool
                Whether to replace existing UUID
            """
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

    # Handle restart mode
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

    # Create original directory if it doesn't exist
    os.makedirs(orig_dir, exist_ok=True)

    # Run BEEMs optimization
    print("Start BEEMs (max_itr={}, num_h={}, target_csv={}, hphi_dir={}, orig_dir={}, summary_dir={}, param_toml={}, input_toml={}, bo_dic={}, hdf5={}, restart={})".format(
        max_itr, num_h, target_csv, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic, hdf5, restart_flag))
    run_beems(max_itr, target_data, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic,
              hdf5, restart_flag)
    print("Finish BEEMs (max_itr={}, num_h={}, target_csv={}, hphi_dir={}, orig_dir={}, summary_dir={}, param_toml={}, input_toml={}, bo_dic={}, hdf5={}, restart={})".format(
        max_itr, num_h, target_csv, hphi_dir, orig_dir, summary_dir, param_toml, input_toml, bo_dic, hdf5, restart_flag))

    # Generate output figure if requested
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
