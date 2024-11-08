import os
import pickle
from datetime import datetime
from subprocess import Popen

from . import Aft_mag
from . import diff
from ..BEEMs import WriteHDF5
from .SolverBase import SolverBase


class SolverHPhiStdGC(SolverBase):
    """A solver class for running HPhi calculations with standard gradient correction.

    This class extends SolverBase to implement specific functionality for running HPhi
    quantum many-body simulations with gradient corrections. It handles parameter file 
    reading, HPhi execution, and magnetization calculations.
    """

    def _read_param_file(self):
        """Read and parse the HPhi parameter file 'stan.in'.

        Reads the input parameter file and extracts values for parameters starting 
        with 'J' (coupling) or 'H' (field) into a dictionary.

        Returns
        -------
        dict
            Dictionary containing parameter names as keys and their values as floats
        """
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
        """Execute HPhi calculation and handle results.

        Runs HPhi simulation with given parameters, optionally storing results in HDF5.
        If results already exist in HDF5, skips calculation and retrieves stored data.

        Parameters
        ----------
        logfile : str
            Path to the log file
        sh5 : object, optional
            HDF5 storage object for reading/writing results

        Notes
        -----
        The function performs these steps:
        1. Reads parameters from stan.in
        2. Checks if calculation exists in HDF5
        3. If needed, runs HPhi (dry run then actual)
        4. Stores results in HDF5 or retrieves existing results
        """
        flag_run_hphi = True
        dic_param = self._read_param_file()

        # Check if calculation already exists in HDF5
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
            # If calculation exists, retrieve results from HDF5
            os.mkdir("output")
            with open("output/resul_mag.dat", "w") as f:
                Sz = sh5.h5["data/param/{}/field/calc_phys/Sz".format(index_param)][index_field][0]
                print("Sz:", Sz, file=fd)
                L = sh5.h5["basic_info/L"][()]
                print("L:", L, file=fd)
                f.write("{}".format(Sz / L))

    def _diff(self, num_bo):
        """Calculate magnetization difference between calculation and target.

        Parameters
        ----------
        num_bo : int
            Bayesian optimization iteration number

        Returns
        -------
        float
            Difference in magnetization values
        """
        diff_mag = diff.main("BO_No{}".format(num_bo), self.target_data)
        return diff_mag

    def calcvalues(self, Nspin):
        """Calculate magnetization values for different magnetic fields.

        Processes results for each magnetic field value and writes results to CSV.

        Parameters
        ----------
        Nspin : int
            Number of spins in the system
        """
        # Get magnetic field values from target data
        mag_fields = self.target_data[:,0]
        
        # Open CSV file to store results
        csv = open("all_mag.csv", "w")
        
        # Process each magnetic field point
        for i in range(self.target_data.shape[0]):
            os.chdir("./h{}".format(i))
            # Calculate magnetization if not already done
            if not os.path.isfile("resul_mag.dat"):
                Aft_mag.main(Nspin)
            os.chdir("../")
            # Read and write results to CSV
            with open("h{}/resul_mag.dat".format(i)) as fr:
                result = fr.read().rstrip()
            csv.write("{},{}\n".format(mag_fields[i], result))
        csv.close()
