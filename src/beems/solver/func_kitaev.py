import math


def get_h(stanin):
    """
    Extract magnetic field value from HPhi input file.

    Parameters
    ----------
    stanin : str
        Path to HPhi input file

    Returns
    -------
    float
        Magnetic field value H from input file
    """
    with open(stanin) as f:
        lines = f.readlines()
    for line in lines:
        if "=" in line:
            vals = line.split("=")
            vals = [x.strip() for x in vals]
            if vals[0] == "H":
                H = float(vals[1])
                break
    return H


def convert_stanin_kitaev(stanin):
    """
    Convert standard HPhi input file to Kitaev model format.

    Reads parameters from input file, converts them to Kitaev model parameters,
    and writes back to the same file.

    Parameters
    ----------
    stanin : str
        Path to HPhi input file to convert

    Returns
    -------
    None
        Modifies input file in place
    """
    # Parameters to extract from input file
    keys = ["K", "G", "GP", "G2", "GP2", "J", "J2", "J3"]
    
    with open(stanin) as f:
        lines = f.readlines()
    
    # Extract parameters and keep other lines
    dic_param = {}
    lines_out = []
    for line in lines:
        if "=" in line:
            vals = line.split("=")
            vals = [x.strip() for x in vals]
            if vals[0] in keys:
                dic_param[vals[0]] = float(vals[1])
            else:
                if vals[0] != "L":
                    if line[-1] != "\n":
                        line += "\n"
                    lines_out.append(line)
    
    # Convert to Kitaev parameters
    dic_kitaev = get_dic_kitaev(dic_param)
    
    # Write converted parameters
    for key in dic_kitaev.keys():
        lines_out.append("{} = {}\n".format(key, dic_kitaev[key]))
    
    with open(stanin, "w") as f:
        for line in lines_out:
            f.write(line)


def get_dic_kitaev(dic_param):
    """
    Convert input parameters to full Kitaev model parameters.

    Parameters
    ----------
    dic_param : dict
        Dictionary containing input parameters K, G, GP, G2, GP2, J, J2, J3

    Returns
    -------
    dict
        Dictionary containing full set of Kitaev model parameters for all bonds
    """
    # Set defaults for all parameters
    kitaev_params = {"K": 0.0, "G": 0.0, "GP": 0.0, "G2": 0.0, "GP2": 0.0, "J": 0.0, "J2": 0.0, "J3": 0.0}
    kitaev_params.update(dic_param)

    # Extract parameters from dictionary with defaults of 0.0
    K = kitaev_params.get("K", 0.0)
    G = kitaev_params.get("G", 0.0) 
    GP = kitaev_params.get("GP", 0.0)
    G2 = kitaev_params.get("G2", 0.0)
    GP2 = kitaev_params.get("GP2", 0.0)
    J = kitaev_params.get("J", 0.0)
    J2 = kitaev_params.get("J2", 0.0)
    J3 = kitaev_params.get("J3", 0.0)

    # Initialize empty dictionary to store all Kitaev model parameters
    dic_kitaev = {}
    
    # Helper function to add symmetric off-diagonal coupling terms
    # For each component (e.g. "xy"), adds both forward (xy) and reverse (yx) terms with same value
    def add_symmetric(prefix, val, components):
        for comp in components:
            dic_kitaev[f"{prefix}{comp}"] = val  # Add forward component 
            dic_kitaev[f"{prefix}{comp[::-1]}"] = val  # Add reverse component
    
    # Iterate through the three bond types (x,y,z bonds) to set all parameters
    for i, main_diag in enumerate([(J+K, J, J), (J, J+K, J), (J, J, J+K)]):
        bond = f"J{i}"  # J0, J1, or J2 for x,y,z bonds respectively
        
        # Set main diagonal terms - one enhanced by Kitaev coupling K
        # For x-bond: (J+K,J,J), y-bond: (J,J+K,J), z-bond: (J,J,J+K)
        dic_kitaev[f"{bond}x"], dic_kitaev[f"{bond}y"], dic_kitaev[f"{bond}z"] = main_diag
        
        # Set off-diagonal coupling terms G and GP
        # G couples perpendicular components, GP couples parallel components
        if i == 0:  # x-bond
            add_symmetric(bond, G, ["yz"])  # G couples y,z components
            add_symmetric(bond, GP, ["xy", "zx"])  # GP couples x with y,z
        elif i == 1:  # y-bond  
            add_symmetric(bond, G, ["zx"])  # G couples z,x components
            add_symmetric(bond, GP, ["xy", "yz"])  # GP couples y with x,z
        else:  # z-bond
            add_symmetric(bond, G, ["xy"])  # G couples x,y components
            add_symmetric(bond, GP, ["yz", "zx"])  # GP couples z with x,y
        
        # Set second-neighbor interactions
        # J2 for diagonal terms, G2/GP2 for off-diagonal terms
        add_symmetric(f"{bond}'", J2, ["x", "y", "z"])  # Diagonal J2 terms
        add_symmetric(f"{bond}'", G2, ["yz", "zx", "xy"][:i+1])  # G2 terms
        add_symmetric(f"{bond}'", GP2, ["yz", "zx", "xy"][i:])  # GP2 terms
        
        # Set third-neighbor interactions
        # Only diagonal J3 terms included
        add_symmetric(f"{bond}''", J3, ["x", "y", "z"])

    return dic_kitaev


def get_site_number(file_name="locspn.def"):
    """
    Get number of sites from locspn.def file.

    Parameters
    ----------
    file_name : str, optional
        Path to locspn.def file, by default "locspn.def"

    Returns
    -------
    int
        Number of sites in the system
    """
    with open(file_name, "r") as fw:
        lines = fw.readlines()
        Nsites = int(lines[1].split()[1])

    return Nsites


def mod_trans(H, Nsites, dict_mag):
    """
    Generate trans.def file with magnetic field parameters.

    Parameters
    ----------
    H : float
        Magnetic field strength
    Nsites : int
        Number of sites in system
    dict_mag : dict
        Dictionary containing magnetic parameters:
        amp_z, amp_tot, theta, phi, gab, gc, bohr

    Returns
    -------
    None
        Writes trans.def file
    """
    # Extract parameters
    amp_z = dict_mag["amp_z"]
    amp_tot = dict_mag["amp_tot"]
    theta = dict_mag["theta"]
    phi = dict_mag["phi"]
    gab = dict_mag["gab"]
    gc = dict_mag["gc"]
    bohr = dict_mag["bohr"]

    # Calculate field components
    h = amp_tot * H
    hx = gab * bohr * h * math.sin(math.pi * theta) * math.cos(math.pi * phi)
    hy = gab * bohr * h * math.sin(math.pi * theta) * math.sin(math.pi * phi)
    hz = gc * bohr * h * amp_z * math.cos(math.pi * theta)
    
    # Define the parameter patterns for each site
    # Each pattern represents a term in the magnetic field coupling:
    # - (spin1, spin2, param1, param2) where:
    #   spin1, spin2: indices for the spin operators (0=up, 1=down)
    #   param1: real part of the coupling (proportional to field components)
    #   param2: imaginary part of the coupling
    # The patterns implement the magnetic field terms:
    # - S^x terms with hx (patterns 0,1)
    # - S^y terms with hy (patterns 0,1) 
    # - S^z terms with hz (patterns 2,3)
    patterns = [
        (0, 1, -0.5 * hx,  0.5 * hy),  # S^- term
        (1, 0, -0.5 * hx, -0.5 * hy),  # S^+ term  
        (0, 0, -0.5 * hz,  0.0),       # S^z up term
        (1, 1,  0.5 * hz,  0.0)        # S^z down term
    ]
    
    # Write trans.def file which defines the one-body terms
    # Format: site1 spin1 site2 spin2 Re(t) Im(t)
    # where t is the coupling parameter
    with open("trans.def", "w") as f:
        # Write header with total number of terms (4 terms per site)
        f.write("===================\n")
        f.write(f"num {4 * Nsites:8d}\n")
        f.write("===================\n" * 3)
        
        # Write parameters for each site
        # Loop over all sites and apply the 4 magnetic field patterns
        # This creates the local magnetic field terms for each site
        for site in range(Nsites):
            for spin1, spin2, param1, param2 in patterns:
                f.write(f" {site:8d}  {spin1:8d}   {site:8d}   {spin2:8d}   {param1:8f}   {param2:8f}\n")


def make_one_body_G_site0(file_name="greenone.def"):
    """
    Generate greenone.def file for site 0.

    Parameters
    ----------
    file_name : str, optional
        Output file name, by default "greenone.def"

    Returns
    -------
    None
        Writes greenone.def file
    """
    with open(file_name, "w") as fw:
        fw.write("===================" + "\n")
        fw.write("num 8 \n")
        fw.write("===================" + "\n")
        fw.write("===================" + "\n")
        fw.write("===================" + "\n")
        fw.write("  0     0     0     1\n")
        fw.write("  0     1     0     0\n")
        fw.write("  0     0     0     0\n")
        fw.write("  0     1     0     1\n")
        fw.write("  1     0     1     1\n")
        fw.write("  1     1     1     0\n")
        fw.write("  1     0     0     0\n")
        fw.write("  1     1     1     1\n")


if __name__ == "__main__":
    stanin = "stan_kitaev.in"
    convert_stanin_kitaev(stanin)
