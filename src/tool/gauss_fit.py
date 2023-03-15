import physbo
import tomli
import numpy as np
import os
import sys

def load_data(param_num, path_to_params=os.path.join("org", "param.csv")):
    A = np.loadtxt(path_to_params, skiprows=1, delimiter=',', dtype="unicode")
    X_org = np.array(A[:, 1:1 + param_num], dtype=np.float64)
    X_center = physbo.misc.centering(X_org)
    mask_train = np.where(A[:, 0] != "")
    A_train = np.array(A[mask_train], dtype=np.float64)
    X_train = np.array(X_center[mask_train], dtype=np.float64)
    t_train = A_train[:, 0]
    return X_org, X_center, X_train, t_train


def main():
    args = sys.argv
    if len(args) == 2:
        file_name = args[1]
    else:
        print("Usage: python gauss_fit.py [params.toml]")
        exit(1)

    if not os.path.exists(file_name):
        print("File not found: {}".format(file_name))
        exit(1)

    with open(file_name, "rb") as f:
        toml_dict = tomli.load(f)

    if toml_dict["physbo"].get("params") is None:
        print("params.toml is invalid")
        exit(1)

    param_num = len(toml_dict["physbo"]["params"])
    X_org, X_center, X_train, t_train = load_data(param_num)
    cov = physbo.gp.cov.gauss(X_train.shape[1], ard=False)
    mean = physbo.gp.mean.const()
    lik = physbo.gp.lik.gauss()
    gp = physbo.gp.model(lik=lik, mean=mean, cov=cov)
    config = physbo.misc.set_config()
    gp.fit(X_train, t_train, config)
    gp.print_params()

    gp.prepare(X_train, t_train)
    fmean = -gp.get_post_fmean(X_train, X_center)
    fcov = gp.get_post_fcov(X_train, X_center)
    print(np.min(fmean))
    with open("gp_fit.dat", "w") as fw:
        for idx, X_org_ in enumerate(X_org):
            file_str = ""
            for param_ in X_org_:
                file_str += "{} ".format(param_)
            file_str += "{} {}\n".format(fmean[idx], fcov[idx])
            fw.write(file_str)

if __name__ == "__main__":
    main()
