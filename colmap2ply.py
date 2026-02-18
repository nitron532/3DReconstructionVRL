#Helper functions to extract ecef colmap points, convert them into enu and place into ply file
import pycolmap
import pymap3d as pm
from pathlib import Path

def get_recons(proj_dir):
    """
    in:
        -proj_dir: directory where the map folders are (like the parent dir of the 0, 1, 2 recons. If there's only one recon, then just make an obj)
    out:
        -recon_list: list of recons 
    """
    proj_path = Path(proj_dir)
    folder_list = [folder for folder in proj_path.iterdir() if folder.is_dir()]
    recon_list = [pycolmap.Reconstruction(f"{proj_dir}/{folder.name}") for folder in folder_list]
    return recon_list

def get_point3Ds(recon):
    """
    in:
        -recon: recon obj
    out:
        -point3D_list: list of point3D objs 
    """
    point3D_list = [recon.point3D(id) for id in recon.point3D_ids()]
    return point3D_list

def get_xyzs(recon):
    """
    in:
        -recon: recon obj
    out:
        -point3D_xyz_set: set of 3d tuples with xyz of every point in recon obj (typically in ecef after model aligning)
    """
    point3D_xyz_set = set()
    for point in get_point3Ds(recon):
        point3D_xyz_set.add(tuple(point.xyz))
    return point3D_xyz_set

def ecefs_to_enus(ecef_list, ref):
    """
    in:
        -ecef_list: list of ecef tuples
        -ref: lat/lon/alt tuple for reference
    out:
        -enu_list: list of enu tuples
    """
    enu_list = [pm.ecef2enu(point[0], point[1], point[2], ref[0], ref[1], ref[2]) for point in ecef_list]
    return enu_list

def make_ply(outputdir, pt_list, comment="none"):
    """
    in:
        -outputdir: dir for output ply including ply file name and its extension
        -pt_list: list of 3d tuples
    out:
        ply file will be in outputdir
    """
    with open(outputdir, 'w') as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"comment {comment}\n")
        file.write(f"element vertex {len(pt_list)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("end_header\n")
        for pt in pt_list:
            file.write(f"{pt[0]} {pt[1]} {pt[2]}\n")

#REPLACE THIS WITH THE LAT/LON/ALT THAT YOU WANT TO BE THE ORIGIN. THIS IS SOME POINT ON CAMPBELL
LAT_0 = 34.41622191
LON_0 = -119.8456223
H_0 = 15.223058115078384


#example; change the directories, obviously
recons = get_recons("./chem2")
chem_recons = get_recons("./chem2")

all_xyzs = set()
for recon in chem_recons:
    all_xyzs.update(get_xyzs(recon))
all_enus = ecefs_to_enus(all_xyzs, (LAT_0, LON_0, H_0))
make_ply("./plys/chem2.ply", all_enus, "chem2")


