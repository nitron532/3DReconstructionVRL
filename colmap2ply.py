import pycolmap
from pathlib import Path
import pymap3d as pm

def get_recons(proj_path):
    """
    in:
        -proj_path: directory where the map folders are (like the parent dir of the 0, 1, 2 recons. If there's only one recon, then just make an obj)
    out:
        -recon_list: list of recons 
    """
    folder_list = [folder for folder in Path(proj_path).iterdir() if folder.is_dir()]
    recon_list = [pycolmap.Reconstruction(f"{proj_path}/{folder.name}") for folder in folder_list]
    return recon_list


def get_point3Ds(recon):
    """
    in:
        -recon: recon obj
    out:
        -point3D_list: list of point3D objs 
    """
    point3D_list = [point3D for id, point3D in recon.points3D.items()]
    return point3D_list

def get_img_world_coords(recon):
    """
    in:
        -recon: recon obj
    out:
        -output: list of tuples (str img name, img world coords)
    """
    output = []
    for _, image in recon.images.items():
        if not image.has_pose:
            continue
        pose = image.cam_from_world()
        rotation = pose.rotation.matrix()
        translation = pose.translation
        camera_center_world = rotation.T @ -translation
        output.append((image.name, camera_center_world))
    return output

def ecefs_to_enus(point3D_list, ref):
    """
    in:
        -point3D_list: list of point3D objs in ecef
        -ref: lat/lon/alt tuple for reference
    out:
        -enu_list: list of enu tuples
    """
    enu_list = [pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2]) for point3D in point3D_list]
    return enu_list

def ply_from_3D_tuple_list(output_path, tuple_3D_list, ref, comment="none"):
    """
    in:
        -output_path: dir for output ply including ply file name and its extension
        -tuple_3D_list: list of 3D tuples
        -ref: lat/lon/alt tuple for reference
    out:
        ply file will be in output_path
    """
    with open(output_path, 'w') as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"comment {comment}\n")
        file.write(f"element vertex {len(tuple_3D_list)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("end_header\n")
        for tuple_3D in tuple_3D_list:
            e, n, u = pm.ecef2enu(tuple_3D[0], tuple_3D[1], tuple_3D[2], ref[0], ref[1], ref[2])
            file.write(f"{e} {n} {u}\n")

def ply_from_point3D_list(output_path, point3D_list, ref, comment="none"):
    """
    in:
        -output_path: dir for output ply including ply file name and its extension
        -pt_list: list of point3D objs
        -ref: lat/lon/alt tuple for reference
    out:
        ply file will be in output_path
    """
    with open(output_path, 'w') as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"comment {comment}\n")
        file.write(f"element vertex {len(point3D_list)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("property uchar red\n")
        file.write("property uchar green\n")
        file.write("property uchar blue\n")
        file.write("end_header\n")
        for point3D in point3D_list:
            e, n, u = pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2])
            r, g, b = point3D.color
            file.write(f"{e} {n} {u} {r} {g} {b}\n")

def ply_from_rigs_list(output_path, rigs_list, ref, comment="none"):
    """
    in:
        -output_path: dir for output ply including ply file name and its extension
        -pt_list: list of point3D objs
        -ref: lat/lon/alt tuple for reference
    out:
        ply file will be in output_path
    """
    with open(output_path, 'w') as file:
        file.write("ply\n")
        file.write("format ascii 1.0\n")
        file.write(f"comment {comment}\n")
        file.write(f"element vertex {len(rigs_list)}\n")
        file.write("property float x\n")
        file.write("property float y\n")
        file.write("property float z\n")
        file.write("end_header\n")
        # for point3D in point3D_list:
        #     e, n, u = pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2])
        #     r, g, b = point3D.color
        #     file.write(f"{e} {n} {u} {r} {g} {b}\n")
#REPLACE THIS WITH THE LAT/LON/ALT THAT YOU WANT TO BE THE ORIGIN. THIS IS SOME POINT ON CAMPBELL
LAT_0 = 34.41622191
LON_0 = -119.8456223
H_0 = 15.223058115078384


"""
example; change the directories, obviously

recons = get_recons("./recons/priors extra options/campbell")

all_point3Ds = []
for recon in recons:
    all_point3Ds = all_point3Ds + get_point3Ds(recon)
ply_from_point3D_list("./plys/priors extra options/campbell.ply", all_point3Ds, (LAT_0, LON_0, H_0), "campbell")
"""

recons = get_recons("./recons/no priors no extra options/chem/no priors no extra options")
test_recon = recons[0]
print(get_img_world_coords(test_recon))
