# -*- coding: utf-8 -*-
import csv
import numpy as np
import os
import physbo
import random
import scipy
import sys
import tomli
import tomli_w

def get_toml_dic(dic_param, toml_dic):
    for key in dic_param.keys():
        toml_dic["hphi_params"][key] = dic_param[key]
    return toml_dic


def output_toml(toml_dic, toml_file="input.toml"):
    with open(toml_file, "wb") as f:
        tomli_w.dump(toml_dic, f)


def load_data(path_to_param, physbo_log="physbo.txt"):
    param_csv = os.path.join("..", "org", "param.csv")
    fp = open(os.path.join("..", physbo_log), "a")
    print("load_data (BO_single.py): parameter csv file is {}".format(param_csv), file=fp)
    fp.close()
    arr = np.genfromtxt(param_csv, skip_header=1, delimiter=',')

    # Only samples with values filled in the target column are extracted as training data.
    arr_train = arr[~np.isnan(arr[:, 0]), :]
    arr_test = arr[np.isnan(arr[:, 0]), :]
    X_train = arr_train[:, 1:]
    t_train = arr_train[:, 0]

    X_all = arr[:, 1:]

    # Get a list of test data indices.
    test_idx_list = np.where(np.isnan(arr[:, 0]))[0].tolist()
    test_actions = test_idx_list

    actions = [i for i in range(len(X_all))]

    actions = list(set(actions) - set(test_actions))
    actions.sort()

    return X_train, t_train, X_all, actions, test_actions


# Design of policy
def main(param_toml="params.toml", input_toml="input.toml"):
    with open(param_toml, "rb") as f:
        dic_toml = tomli.load(f)

    # Parameters for physbo section
    num_search_each_probe = dic_toml["physbo"].get("num_search_each_probe", 1)
    seed = dic_toml["physbo"].get("seed", 1)
    score = dic_toml["physbo"].get("score", "TS")
    interval = dic_toml["physbo"].get("interval", 0)
    num_rand_basis = dic_toml["physbo"].get("num_rand_basis", 5000)
    num_random = dic_toml["physbo"].get("num_random", 3)
    physbo_params_list = dic_toml["physbo"]["params"]
    physbo_log = dic_toml["physbo"].get("log", "physbo.txt")

    fp = open(os.path.join("../", physbo_log), "a")

    X_train, t_train, X_all, actions, test_actions = load_data(physbo_log)
    print("BO_single.py actions:", actions, file=fp)

    if len(t_train) > num_random-1:

        initial_actions = actions
        X = physbo.misc.centering(X_all)
        policy = physbo.search.discrete.policy(test_X=X, initial_data=[initial_actions, t_train])
        policy.set_seed(seed)

        actions = policy.bayes_search(max_num_probes=num_search_each_probe, num_search_each_probe=num_search_each_probe,
                                      simulator=None, score=score, interval=interval, num_rand_basis=num_rand_basis)

        for i in range(num_search_each_probe):
            print("Next Point: " + str(X_all[actions[i]]) + "   Row Number: " + str(actions[i] + 2), file=fp)
            tmp = str(X_all[actions[i]]).split("[")
            tmp2 = tmp[1].split("]")
            tmp3 = tmp2[0].split()
            print(tmp3, file=fp)
            dic_param = {}
            for j, param in enumerate(physbo_params_list):
                dic_param[param] = float(tmp3[j])
            else:
                toml_dic = get_toml_dic(dic_param, dic_toml)
            output_toml(toml_dic, toml_file=input_toml)
            with open("info", 'w') as f:
                string = " " + str(actions[i] + 2) + " "
                for j, param in enumerate(physbo_params_list):
                    string += "{} ".format(tmp3[j])
                print(string, file=f)

    else:

        remain = len(test_actions)
        action = random.randint(0, remain - 1)

        print("Next Point: " + str(X_all[test_actions[action]]) + "   Row Number: " + str(test_actions[action] + 2),
              file=fp)
        tmp = str(X_all[test_actions[action]]).split("[")
        tmp2 = tmp[1].split("]")
        tmp3 = tmp2[0].split()
        print(tmp3, file=fp)
        dic_param = {}
        for i, param in enumerate(physbo_params_list):
            dic_param[param] = float(tmp3[i])
        else:
            toml_dic = get_toml_dic(dic_param, dic_toml)
        output_toml(toml_dic, toml_file=input_toml)
        with open("info", 'w') as f:
            string = " " + str(test_actions[action] + 2) + " "
            for i, param in enumerate(physbo_params_list):
                string += "{} ".format(tmp3[i])
            print(string, file=f)
    fp.close()
    return dic_param

if __name__ == "__main__":
    main()
