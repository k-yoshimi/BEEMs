import shutil
from datetime import datetime

class SolverBase:
    """Base solver class for running HPhi calculations and computing observables.

    This class provides the basic framework for running HPhi quantum many-body calculations
    and computing observables like magnetization. It is meant to be subclassed with specific
    implementations.

    Parameters
    ----------
    hphi_path : str
        Path to the HPhi executable
    toml_file : str
        Path to the TOML configuration file
    target_data : ndarray
        Array containing target data to compare against
    dir_summary : str
        Directory to store summary results
    hdf5 : str or None
        Path to HDF5 file for caching results, if any

    Attributes
    ----------
    hphi_path : str
        Stored path to HPhi executable
    toml_file : str
        Stored path to TOML config
    target_data : ndarray
        Stored target data array
    dir_summary : str
        Stored summary directory path
    hdf5 : str or None
        Stored HDF5 file path
    """

    def __init__(self, hphi_path, toml_file, target_data, dir_summary, hdf5):
        # Store all the initialization parameters
        self.hphi_path = hphi_path
        self.toml_file = toml_file
        self.target_data = target_data
        self.dir_summary = dir_summary
        self.hdf5 = hdf5

    def _run_hphi(self, logfile, sh5=None):
        """Run a single HPhi calculation.

        This is a placeholder that should be implemented by subclasses.

        Parameters
        ----------
        logfile : str
            Path to log file for HPhi output
        sh5 : SearchHDF5, optional
            HDF5 interface for caching results

        Raises
        ------
        SystemExit
            If not implemented in subclass
        """
        print("_run_hphi is not implemented.")
        exit(1)

    def _diff(self):
        """Calculate difference between computed and target values.

        This is a placeholder that should be implemented by subclasses.

        Returns
        -------
        None
            Placeholder return
        """
        print("_diff is not implemented.")
        return None

    def run(self, logfile, sh5=None):
        """Run HPhi calculations for all target data points.

        Iterates through target data points, running HPhi for each one
        and organizing the output files.

        Parameters
        ----------
        logfile : str
            Path to log file for HPhi output
        sh5 : SearchHDF5, optional
            HDF5 interface for caching results
        """
        import tqdm
        # Iterate through all target data points with progress bar
        for i in tqdm.tqdm(range(self.target_data.shape[0])):
            # Copy input file for this data point
            shutil.copy("stan{}.in".format(i), "stan.in")
            # Run HPhi calculation
            self._run_hphi(logfile, sh5)
            # Move output to numbered directory
            shutil.move("output", "h{}".format(i))

    def calcvalues(self):
        """Calculate physical observables from HPhi output.

        This is a placeholder that should be implemented by subclasses.

        Raises
        ------
        SystemExit
            If not implemented in subclass
        """
        print("calcvalues is not implemented.")
        exit(1)

    def cost(self, num_bo):
        """Calculate cost function for current parameters.

        Computes difference between calculated and target values,
        then moves results to summary directory.

        Parameters
        ----------
        num_bo : int
            Current Bayesian optimization iteration number

        Returns
        -------
        float
            Cost function value (difference from target)
        """
        # Calculate difference from target values
        diff_mag = self._diff(num_bo)
        # Move results to summary directory
        shutil.move("BO_No{}".format(num_bo), self.dir_summary)
        return diff_mag
