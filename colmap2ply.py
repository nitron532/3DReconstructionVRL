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
    print(folder_list)
    recon_list = [pycolmap.Reconstruction(f"{proj_dir}/{folder.name}") for folder in folder_list]
    print(recon_list)
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

def point3Ds_to_enus(point3D_list, ref):
    """
    in:
        -point3D_list: list of point3D objs
        -ref: lat/lon/alt tuple for reference
    out:
        -enu_list: list of enu tuples
    """
    enu_list = [pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2]) for point3D in point3D_list]
    return enu_list

def make_ply(outputdir, point3D_list, ref, comment="none"):
    """
    in:
        -outputdir: dir for output ply including ply file name and its extension
        -pt_list: list of point3D objs
        -ref: lat/lon/alt tuple for reference
    out:
        ply file will be in outputdir
    """
    with open(outputdir, 'w') as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"comment {comment}\n")
        file.write(f"element vertex {len(point3D_list)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        #todo handle colors
        file.write("property uchar red\n")
        file.write("property uchar green\n")
        file.write("property uchar blue\n")
        file.write("end_header\n")
        for point3D in point3D_list:
            e, n, u = pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2])
            r, g, b = point3D.color
            file.write(f"{e} {n} {u} {r} {g} {b}\n")

#REPLACE THIS WITH THE LAT/LON/ALT THAT YOU WANT TO BE THE ORIGIN. THIS IS SOME POINT ON CAMPBELL
LAT_0 = 34.41622191
LON_0 = -119.8456223
H_0 = 15.223058115078384


#example; change the directories, obviously
recons = get_recons("./recons/prior/scuffed_campbell_translock_false")

all_point3Ds = []
for recon in recons:
    all_point3Ds = all_point3Ds + get_point3Ds(recon)
make_ply("./plys/scuffed_campbellprior.ply", all_point3Ds, (LAT_0, LON_0, H_0), "scuffedcampbellprior")



"""
Notes:
Add color to points (they are in colmap point3D objs)
Add phys sci north to recon
Basecamp post about alignment
"""
"""
Notes:
-COLMAP find where BA ceres solver is called
-Find implementation of BA ceres solver
-Figure out how to lock things during BA ceres solver 
-Apply
"""

"""
-Find out how to incorporate azimuth and lat lon for pose priors in reconstructions
-write script to run colmap reconstruction commands 
"""
