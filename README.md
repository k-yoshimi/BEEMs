# BEEMs

## About

*BEEMs* (Bayesian optimization of Effective Models) is a tool for optimizing quantum lattice models using Bayesian methods. It combines:

- [HΦ](https://github.com/issp-center-dev/HPhi) as a quantum lattice solver to compute magnetization curves
- [PHYSBO](https://github.com/issp-center-dev/PHYSBO) for Bayesian optimization to efficiently search the parameter space

Given a target magnetization curve, BEEMs finds the optimal Hamiltonian parameters by minimizing the deviation between computed and target curves.

## Installation

### Requirements

- [HΦ](https://github.com/issp-center-dev/HPhi)
- Python packages listed in `pyproject.toml`

The python packages are listed in `pyproject.toml`.

### Build
*BEEMs* is available from this GitHub page.

```bash
$ git clone https://github.com/k-yoshimi/BEEMs.git
$ cd BEEMs
$ pip3 install .
```

Then, you can use *beems* as a python package.
Post tools *gauss_fit*, *mag_plt*, and *output_score* are also available.

## How to use
This section explains how to use *BEEMs*, using `sample/spin_j1j2j3` as an example. 
First, change directory to `sample/spin_j1j2j3`
```bash
$ cd sample/spin_j1j2j3
```

In this directory, you can find the following files.

- mag_j1j2j3.csv
    - The target magnetization curve csv file.
- params.toml
    - The input file for *beems*.
- run_hphi.sh
    - The script file for running HPhi.

### 1. Preparation for the target magnetization file.

First, the target data for comparison needs to be prepared.
Here, mag_j1j2j3.csv is used as a sample.
This file is data obtained by calculating magnetisation using HPhi, with
Heisenberg Chain with L=12 with J0 = 1.0, J0' = 0.1, J0'' = 0.02 and 
the magnetic field in the range [-3.0, 0.0].
The field is varied in increments of 0.05.

```
   0.0,-0.0
   0.05,0.0
   0.1,0.0
   0.15,0.0
   0.2,0.0
   0.25,0.0
   0.3,0.0
   0.35,0.0
   0.4,0.08333333333333333333
   0.45,0.0833333333333333333
   0.5,0.08333333333333333
   0.55,0.0833333333333333333
   0.6,0.08333333333333333
   (Omitted below)
```

In the above, the first row is the magnetic field and the second row is the magnetisation.


### 2. Preparation for the input file.

Next, the input file for *beems* must be prepared.
This file is a TOML file, which is a format for configuration files.
For the input file, params.toml is used as a sample.

```
   [physbo]
   max_itr = 5
   seed = 1
   score = "TS"
   params = ["J0'", "J0''"]
   "J0'" = [0.1, 0.8, 15]
   "J0''" = [0.02, 0.06, 9]

   [hphi_params]
   model = "SpinGC"
   method = "CG"
   lattice = "chain"
   L = 12
   exct = 2
   J0 = 1.0
   lanczos_max = 10000
   EigenvecIO = "none"

   [path]
   target_csv = "./mag_j1j2j3.csv"
   hphi_dir = "../../../HPhi/build/src"
```
Here, we briefly explain the meaning of each parameter.

- [physbo] section
  
  - max_iter (required, integer)

    - Maximum number of iterations to run PHYSBO.
  
  - params (required, list of strings)

    - List of parameters to be searched for.
  
  - Each string in the above params (mandatory, [float, float, int])

    - Range and number of divisions of the parameter to be explored. [minimum, maximum, number of divisions].

  - seed (optional, integer, default value: 1)

    - SEED value given to PHYSBO.

  - num_search_each_probe (optional, integer, default value: 1)

    - Maximum number of search processes by Bayesian optimization

  - score (optional, string, default value: "TS")

    - Gives the type of acquisition function: TS (Thompson Sampling), EI (Expected Improvement) or PI (Probability of Improvement).

  - interval (optional, integer, default value: 0)

    - Interval at which hyperparameters are learned; if interval is set to a negative value, no hyperparameters are learned.

  - num_rand_basis (optional, integer, default value: 5000)

    - Number of basis functions.

  - num_search_each_probe, score, interval and num_rand_basis are variables to be passed to the function bayes_search to perform Bayesian optimization in the physbo.search.discrete.policy class

    - For more information see https://issp-center-dev.github.io/PHYSBO/manual/master/ja/api/physbo.search.discrete.policy.html

  - num_random (optional, integer, default value: 3)

    - The number of times the random process is executed. num_random times the random process is executed, after which the Bayesian optimization search is performed.

  - restart (optional, string, default value: "True")
  
    - Whether restart calculation is performed.
  　If " True", the restart calculation will be performed while  if "False", it will not be performed. 
    If there is no previous calculation data, a new run is automatically performed even if "True" is selected.

  - log (optional, string, default value: "log")

    - Name of the log file.

- [hphi_params] section (required)

  - Describe here any standard modes of HPhi that are not included in the list of params.

  - If a parameter included in params is described here, it will be overwritten with the candidate value when BEEMs is executed.

  - For information on the parameters available in HPhi's standard mode, see http://issp-center-dev.github.io/HPhi/manual/master/ja/html/filespecification/standardmode_ja/index See _standardmode_en.html

- [path] section

  - target_csv (required, string)

    - File name of the magnetisation data (in CSV format) to be referenced when BEEMs is executed

  - hphi_dir (required, string)

    - PATH of the directory where the HPhi executable files are located.


### 3. Bayesian optimization

Running Bayesian optimization on sample/spin_j1j2j3

```
$beems params.toml
```

Then, the Bayesian optimization will be performed.
In this example, the output is as follows.

```
   Read TOML file params.toml ...
   Read target csv file /InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv ...
   Warning: Summary directory does not exist. Restart flag changes to False.
   New mode.
   Start BEEMs (max_itr=5, num_h=61, target_csv=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv, hphi_dir=/InstalledDirectory/HPhi/build/src, orig_dir=org, summary_dir=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/Sum, param_toml=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/params.toml, input_toml=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/input.toml, bo_dic={'param_toml': PosixPath('/InstalledDirectory/BEEMs/sample/spin_j1j2j3/params.toml'), 'input_toml': PosixPath('/InstalledDirectory/BEEMs/sample/spin_j1j2j3/input.toml')}, hdf5=None, restart=False)
   read mag file: /InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv
   Iteration Number 1 (Random)
   Make input files.
   read mag file: /InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv
   Proposed parameters: {"J0'": 0.5, "J0''": 0.04}
   Calculate observables.
   100%|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■| 61/61 [00:42<00:00,  1.43it/s]
   Current score: -0.0023156165483365692
   Current best score: -0.00231562
   Current best parameters: {"J0'": 0.5, "J0''": 0.04}
   End Iteration Number 1
   ...
   Iteration Number 5 (Bayesian Optimization)
   Make input files.
   Start the initial hyper parameter searching ...
   Done

   Start the hyper parameter learning ...
   0 -th epoch marginal likelihood -19.896292031398644
   50 -th epoch marginal likelihood -19.904414779727873
   100 -th epoch marginal likelihood -19.912525394737457
   150 -th epoch marginal likelihood -19.919976925738702
   200 -th epoch marginal likelihood -19.926436569575607
   250 -th epoch marginal likelihood -19.931491008476318
   300 -th epoch marginal likelihood -19.935041560935073
   350 -th epoch marginal likelihood -19.937322076018987
   400 -th epoch marginal likelihood -19.93873851829338
   450 -th epoch marginal likelihood -19.93966616751587
   500 -th epoch marginal likelihood -19.940348594311565
   Done

   read mag file: /InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv
   Proposed parameters: {"J0'": 0.1, "J0''": 0.05}
   Calculate observables.
   100%|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■| 61/61 [00:24<00:00,  2.48it/s]
   Current score: -0.0002696616219273481
   Current best score: -0.00022769
   Current best parameters: {"J0'": 0.15, "J0''": 0.035}
   End Iteration Number 5

   Finish BEEMs (max_itr=5, num_h=61, target_csv=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/mag_j1j2j3.csv, hphi_dir=/InstalledDirectory/HPhi/build/src, orig_dir=org, summary_dir=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/Sum, param_toml=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/params.toml, input_toml=/InstalledDirectory/BEEMs/sample/spin_j1j2j3/input.toml, bo_dic={'param_toml': PosixPath('/InstalledDirectory/BEEMs/sample/spin_j1j2j3/params.toml'), 'input_toml': PosixPath('/InstalledDirectory/BEEMs/sample/spin_j1j2j3/input.toml')}, hdf5=None, restart=False)

```

### 4. Output files

After finishing the running *beems*, the following output files are generated as follows.

- Sum/BO_No{n} : Directory containing the results of the {n}th execution of PHYSBO ({n} takes numbers 1-5 in the sample).
 
  The following files and directories are generated in the above directory

  - all_mag.csv: file containing the magnetisation of the nth run of PHYSBO (in CSV format)

  - best.csv: file recording the maximum Delta value after each run of PHYSBO (CSV format)

  - info: file containing the parameters used for the {n}th PHYSBO run

  - std.out: file containing the standard output of HPhi (overwritten for each HPhi run).

  - h\*: directory containing the results of each HPhi run for each magnetic field

  - \*.def, stan\*.in, geometry.dat: files output from HPhi (overwritten for each HPhi run)

- org/ : directory containing candidate parameter points, etc. The results computed by each Bayesian optimisation are also collected in this directory.

  The following files are generated in the above directory

  - param.cev: Data file (CSV format) outputting candidate parameter points, from which candidate points are selected for each iteration of BEEMs and the resulting Delta values are written to this file.

  - best.csv: File (in CSV format) recording the maximum Delta value after each run of PHYSBO.

  - info: file containing the candidate points recorded for the PHYSBO run

The delta and parameter pairs obtained by Bayesian optimisation are stored in the org directory
param.csv file.

```
   delta,J0'_cand,J0''_cand
   ,0.100000,0.020000
   ,0.100000,0.025000
   ,0.100000,0.030000
   ,0.100000,0.035000
   ,0.100000,0.040000
   ,0.100000,0.045000
    -0.00026966 ,0.100000,0.050000
   ,0.100000,0.055000
   ,0.100000,0.060000
   ,0.150000,0.020000
   ,0.150000,0.025000
   ,0.150000,0.030000
    -0.00022769 ,0.150000,0.035000
    -0.00034153 ,0.150000,0.040000
   ,0.150000,0.045000
   ,0.150000,0.050000
   (Abbreviations below)
```
### 5. Post tools

The following tools are provided to analyze the results of BEEMs.
- output_score: Output the best parameter set obtained by Bayesian optimisation.
  - Arguments: params.toml (get location of target file), output_BO_num (1 if none)
  - Output: score_list.csv (also put out on stdout)
    - example (```$output_score params.toml 10```)
    ```
    #BO_No, diff, J0', J0''
    12, 3.627567663932239e-08, 0.1, 0.025
    14, 0.00011387122699703351, 0.05, 0.025
    4, 0.0002277065325020824, 0.1, 0.05
    8, 0.00022770684263977338, 0.05, 0.05
    20, 0.00022771714176003527, 0.0, 0.05
    16, 0.00022772506593830337, 0.0, 0.025
    15, 0.0002277321441005834, 0.15, 0.025
    17, 0.00033575767959264746, 0.15, 0.0
    13, 0.0003371863331483626, 0.1, 0.0
    10, 0.0003415637429403177, 0.15, 0.05
    ```

- gauss_fit: Gaussian fitting of the Delta values obtained by Bayesian optimisation
  - Argument: params.toml (get location of target file)
  - Output: File (gp_fit.dat) with output of values fitted by the Gaussian process using the calculation results.
    - example (```$ gauss_fit params.toml```)
    ```
    0.0 0.0 0.0003672000250873799 1.6659781255835176e-08
    0.0 0.0 0.0003672000250873799 1.6659781255835176e-08
    0.0 0.025 0.00027958997644297705 8.71011597447326e-09
    0.0 0.0 0.0003672000250873799 1.6659781255835176e-08
    0.0 0.025 0.00027958997644297705 8.71011597447326e-09
    0.0 0.05 0.00036336513398635244 7.255393750528992e-09
    ...
    ```
    
- plot_mag: Plot the magnetisation obtained by Bayesian optimisation.
  - Arguments: params.toml (to get the location of the target file), plot_BO_no (if not present, output the best one)
  - Output: pdf file with magnetisation curves for target and estimated
  
##  License
The distribution of the program package and the source codes for *BEEMs* follow GNU General Public License version 3 (GPL v3).

We hope that you cite the following paper when you publish results using *BEEMs*.

- [“Quantum lattice model solver HΦ”, M. Kawamura, K. Yoshimi, T. Misawa, Y. Yamaji, S. Todo, and N. Kawashima, Computer Physics Communications 217, 180 (2017).](https://github.com/issp-center-dev/HPhi/edit/master/README.md)
- [“Bayesian optimization package: PHYSBO”, Yuichi Motoyama, Ryo Tamura, Kazuyoshi Yoshimi, Kei Terayama, Tsuyoshi Ueno, Koji Tsuda, Computer Physics Communications Volume 278, September 2022, 108405.](https://doi.org/10.1016/j.cpc.2022.108405)

## Authors
Kazuyoshi Yoshimi, Ryo Tamura, Takahiro Misawa.
