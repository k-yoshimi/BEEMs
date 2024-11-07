import physbo
import tomli
import numpy as np
import os
import sys

def load_data(param_num, path_to_params=os.path.join("org", "param.csv")):
    """Load and preprocess parameter data from CSV file.

    Parameters
    ----------
    param_num : int
        Number of parameters to load from the CSV file
    path_to_params : str, optional
        Path to the CSV file containing parameters, by default "org/param.csv"

    Returns
    -------
    tuple
        X_org : ndarray
            Original parameter values
        X_center : ndarray 
            Centered parameter values
        X_train : ndarray
            Training data subset of centered parameters
        t_train : ndarray
            Training target values
    """
    # Load raw data from CSV, skipping header row
    A = np.loadtxt(path_to_params, skiprows=1, delimiter=',', dtype="unicode")
    
    # Extract parameter columns and convert to float
    X_org = np.array(A[:, 1:1 + param_num], dtype=np.float64)
    
    # Center the parameter values
    X_center = physbo.misc.centering(X_org)
    
    # Create training dataset mask where first column is not empty
    mask_train = np.where(A[:, 0] != "")
    
    # Apply mask to get training data
    A_train = np.array(A[mask_train], dtype=np.float64)
    X_train = np.array(X_center[mask_train], dtype=np.float64)
    t_train = A_train[:, 0]
    
    return X_org, X_center, X_train, t_train


def main():
    """Main function to perform Gaussian Process fitting on parameter data.
    
    Reads parameters from a TOML configuration file, loads training data,
    fits a Gaussian Process model, and outputs predictions to a file.
    """
    # Parse command line arguments
    args = sys.argv
    if len(args) == 2:
        file_name = args[1]
    else:
        print("Usage: python gauss_fit.py [params.toml]")
        exit(1)

    # Check if config file exists
    if not os.path.exists(file_name):
        print("File not found: {}".format(file_name))
        exit(1)

    # Load TOML configuration file
    with open(file_name, "rb") as f:
        toml_dict = tomli.load(f)

    # Validate TOML structure
    if toml_dict["physbo"].get("params") is None:
        print("params.toml is invalid")
        exit(1)

    # Get number of parameters and load data
    param_num = len(toml_dict["physbo"]["params"])
    X_org, X_center, X_train, t_train = load_data(param_num)

    # Setup Gaussian Process model components
    cov = physbo.gp.cov.gauss(X_train.shape[1], ard=False)  # Gaussian covariance function
    mean = physbo.gp.mean.const()  # Constant mean function
    lik = physbo.gp.lik.gauss()  # Gaussian likelihood
    gp = physbo.gp.model(lik=lik, mean=mean, cov=cov)
    
    # Configure and fit the GP model
    config = physbo.misc.set_config()
    gp.fit(X_train, t_train, config)
    gp.print_params()

    # Prepare model for predictions
    gp.prepare(X_train, t_train)
    
    # Get posterior mean and covariance
    fmean = -gp.get_post_fmean(X_train, X_center)  # Negative for minimization
    fcov = gp.get_post_fcov(X_train, X_center)
    print(np.min(fmean))
    
    # Write predictions to output file
    with open("gp_fit.dat", "w") as fw:
        for idx, X_org_ in enumerate(X_org):
            file_str = ""
            for param_ in X_org_:
                file_str += "{} ".format(param_)
            file_str += "{} {}\n".format(fmean[idx], fcov[idx])
            fw.write(file_str)

if __name__ == "__main__":
    main()
