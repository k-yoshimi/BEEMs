import shutil
from datetime import datetime

class SolverBase:

    def __init__(self, hphi_path, toml_file, target_data, dir_summary, hdf5):
        self.hphi_path = hphi_path
        self.toml_file = toml_file
        self.target_data = target_data
        self.dir_summary = dir_summary
        self.hdf5 = hdf5

    def _run_hphi(self, logfile, sh5=None):
        print("_run_hphi is not implemented.")
        exit(1)

    def _diff(self):
        print("_diff is not implemented.")
        return None

    def run(self, logfile, sh5=None):
        import tqdm
        for i in tqdm.tqdm(range(self.target_data.shape[0])):
            shutil.copy("stan{}.in".format(i), "stan.in")
            self._run_hphi(logfile, sh5)
            shutil.move("output", "h{}".format(i))

    def calcvalues(self):
        print("calcvalues is not implemented.")
        exit(1)

    def cost(self, num_bo):
        diff_mag = self._diff(num_bo)
        shutil.move("BO_No{}".format(num_bo), self.dir_summary)
        return diff_mag
