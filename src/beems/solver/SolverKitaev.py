import os
import pickle
import tomli
from subprocess import Popen

import Aft_mag
from SolverHPhiStdGC import SolverHPhiStdGC
from func_kitaev import *


class SolverKitaev(SolverHPhiStdGC):
    """A solver class for Kitaev model calculations using HPhi.
    
    This class extends SolverHPhiStdGC to handle Kitaev model specific calculations,
    including magnetic field interactions and parameter conversions.
    """

    def _run_hphi(self, i):
        """Run HPhi calculation for a given parameter set.
        
        Parameters
        ----------
        i : int
            Index of the current parameter set being calculated
            
        Notes
        -----
        This method performs the following steps:
        1. Reads magnetic field from stan.in and converts Kitaev parameters
        2. Performs HPhi dry run to get system information
        3. Modifies transfer integrals based on magnetic field
        4. Executes main HPhi calculation
        """
        # Read magnetic field from standard input file
        H = get_h("stan.in")
        # Load magnetic field parameters from TOML configuration
        dict_mag = tomli.load(self.toml_file)["mag"]
        # Convert standard input parameters to Kitaev format
        convert_stanin_kitaev("stan.in")
        
        # Execute HPhi dry run to generate necessary files
        cmd = "{}/HPhi -sdry stan.in > std.out".format(self.hphi_path)
        popen = Popen(cmd, shell=True)
        popen.wait()
        # Get total number of sites in the system
        Nsites = get_site_number()
        
        # Setup and modify transfer integrals
        make_one_body_G_site0()  # Initialize one-body terms at site 0
        mod_trans(H, Nsites, dict_mag)  # Modify transfer integrals with magnetic field
        
        # Execute main HPhi calculation
        cmd = "sh ../run_hphi.sh {}".format(self.hphi_path)
        print("start running HPhi {}".format(i), datetime.now())
        popen = Popen(cmd, shell=True)
        popen.wait()
        print("end running HPhi {}".format(i), datetime.now())

    def calcvalues(self):
        """Calculate magnetic properties for all parameter sets.
        
        This method processes multiple magnetic field configurations and saves
        the results to a CSV file. For each magnetic field value, it:
        1. Changes to the appropriate directory
        2. Loads input parameters
        3. Calculates magnetic properties
        4. Saves results to a consolidated CSV file
        
        The output CSV contains magnetic field values and corresponding results.
        """
        # Load pre-calculated magnetic field values
        with open("mag_field.pkl", "rb") as f:
            mag_fields = pickle.load(f)
            
        # Open output CSV file for writing results
        csv = open("all_mag.csv", "w")
        
        # Process each parameter set
        for i in range(self.num_param):
            # Change to parameter-specific directory
            os.chdir("./h{}".format(i))
            # Load input parameters from TOML file
            input_dict = tomli.load("../" + self.toml_file)
            # Calculate magnetic properties
            Aft_mag.kitaev(input_dict)
            os.chdir("../")
            
            # Read and format calculation results
            with open("h{}/resul_mag.dat".format(i)) as fr:
                result = fr.read().rstrip().lstrip("[").rstrip("]")
            # Write magnetic field and result to CSV
            csv.write("{},{}\n".format(mag_fields[i], result))
            
        csv.close()
