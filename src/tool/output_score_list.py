import tomli
import numpy as np
import sys
import os
import glob

def main():
    args = sys.argv
    if len(args) == 2:
        file_name = args[1]
        output_BO_num = 1
    elif len(args) == 3:
        file_name = args[1]
        output_BO_num = np.int64(args[2])
    else:
        print("Usage: python output_score_list.py [file_name] [output_BO_num]")
        print("output_BO_num: number of BO_No to output score list (default 1)")
        exit(1)

    if not os.path.exists(file_name):
        print("File not found: {}".format(file_name))
        exit(1)

    with open(file_name, "rb") as f:
        toml_dict = tomli.load(f)

    target_file_name = toml_dict["path"]["target_csv"]
    if target_file_name is None:
        print("params.toml is invalid.")
        print("target_csv is not found.")
        exit(1)

    if not os.path.exists(target_file_name):
        print("File not found: {}".format(target_file_name))
        exit(1)

    param_inf = toml_dict["physbo"].get("params")
    if param_inf is None:
        print("params.toml is invalid.")
        print("physbo.params is not found.")
        exit(1)

    target_data = np.loadtxt(target_file_name, delimiter=',', dtype=np.float64)
    all_mag_list = glob.glob("Sum/BO_No*")
    total_num = len(all_mag_list)
    all_diff = np.zeros(total_num)
    all_info = []
    for idx  in range(total_num):
        mag_file = os.path.join("Sum", "BO_No{}".format(idx+1), "all_mag.csv")
        BO_data = np.loadtxt(mag_file, delimiter=',', dtype=np.float64)
        info_file = os.path.join("Sum", "BO_No{}".format(idx+1), "info")
        all_info.append(np.loadtxt(info_file, dtype=np.float64))
        all_diff[idx] = np.mean((target_data[:, 1]-BO_data[:, 1])**2)

    score_list = np.argsort(all_diff)

    with open("score_list.csv", "w") as fw:
        str_header = "#BO_No, diff"
        for key in param_inf:
            str_header += ", {}".format(key)
        print(str_header)
        str_header += "\n"
        fw.write(str_header)
        for idx in score_list[:output_BO_num]:
            str_score = "{}, {}".format(idx+1, all_diff[idx])
            for info in all_info[idx][1:]:
                str_score += ", {}".format(info)
            print(str_score)
            str_score += "\n"
            fw.write(str_score)

if __name__ == "__main__":
    main()
