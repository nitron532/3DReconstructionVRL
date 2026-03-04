import pycolmap
from pathlib import Path
import pymap3d as pm
import xml.etree.ElementTree as ET
from pyproj import Transformer
import numpy as np

class Parsing:
    #pycolmap
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
    #other
    def tuple_3D_list_from_ref_file(src_path):
        """
        in:
            -src_path: path to ref txt file w/ line formatted as [imgname, x, y, alt]
        out:
            -tuple_3D_list: list of emlid xyz tuples
        """
        tuple_3D_list = []
        with open(src_path, "r") as file:
            for line in file.readlines():
                line = line.strip().split(" ")
                tuple_3D_list.append((float(line[1]), float(line[2]), float(line[3])))
        return tuple_3D_list

    def tuple_3D_list_from_manifest_file(src_path):
        """
        in:
            -src_path: path to manifest xml file
        out:
            -tuple_3D_list: list of emlid xyz tuples
        """
        tuple_3D_list = []
        tree = ET.parse(src_path)
        for photo in tree.getroot().iter('Photo'):
            match = photo.find('Match')
            #if has corresponding emlid point
            matched = match.find('Matched')
            
            if matched.text.lower() == 'true':
                photo_path = photo.find('Path').text
                photo_name = photo_path[photo_path.rfind('\\')+1:]

                emlidgps = match.find('EmlidGps')
                latitude = float(emlidgps.find('Latitude').text)
                longitude = float(emlidgps.find('Longitude').text)
                orthometric_height = float(emlidgps.find('OrthometricHeight').text)
                tuple_3D_list.append((latitude, longitude, orthometric_height))
        return tuple_3D_list

class CoordConversions:
    def ecef_to_enu_tuple_3D_list(tuple_3D_list, ref):
        """
        in:
            -tuple_3D_list: list of 3D tuples in ecef
            -ref: lat/lon/alt tuple for reference
        out:
            -enu_list: list of enu tuples
        """
        enu_list = [pm.ecef2enu(point[0], point[1], point[2], ref[0], ref[1], ref[2]) for point in tuple_3D_list]
        return enu_list

    def ecef_to_enu_point3D(point3D_list, ref):
        """
        in:
            -point3D_list: list of point3D objs in ecef
            -ref: lat/lon/alt tuple for reference
        out:
            -enu_list: list of enu tuples
        """
        enu_list = [pm.ecef2enu(point3D.xyz[0], point3D.xyz[1], point3D.xyz[2], ref[0], ref[1], ref[2]) for point3D in point3D_list]
        return enu_list

    def ecef_to_web_mercator_tuple_3D_list(tuple_3D_list):
        """
        in:
            -tuple_3D_list: list of 3D tuples in ecef
        out:
            -web_mercator_list: list of web mercator + alt tuples
        """
        web_mercator_list = []
        transformer = Transformer.from_crs("EPSG:4978", "EPSG:3857", always_xy=True)
        for ecef_x, ecef_y, ecef_z in tuple_3D_list:
            web_mercator_x, web_mercator_y, web_mercator_z = transformer.transform(ecef_x, ecef_y, ecef_z)
            web_mercator_list.append((web_mercator_x, web_mercator_y, web_mercator_z))
        return web_mercator_list

    def latlonalt_to_web_mercator_tuple_3D_list(tuple_3D_list):
        """
        in:
            -tuple_3D_list: list of 3D tuples in ecef
        out:
            -web_mercator_list: list of web mercator + alt tuples
        """
        web_mercator_list = []
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        for lat, lon, alt in tuple_3D_list:
            web_mercator_x, web_mercator_y, web_mercator_z = transformer.transform(lon, lat, alt)
            web_mercator_list.append((web_mercator_x, web_mercator_y, web_mercator_z))
        return web_mercator_list

    def latlonalt_to_enu_tuple_3D_list(tuple_3D_list, ref):
        """
        in:
            -point3D_list: list of point3D objs in ecef
            -ref: lat/lon/alt tuple for reference
        out:
            -enu_list: list of enu tuples
        """
        enu_list = [pm.geodetic2enu(point[0], point[1], point[2], ref[0], ref[1], ref[2], deg=True) for point in tuple_3D_list]
        return enu_list
    
    def web_mercator_scale_and_define_origin(web_mercator_list, origin, scale_factor):
        """
        in:
            -web_mercator_list: list of 3D web mercator coord tuples
            -origin: 3D lon lat alt tuple to be origin
            -scale_factor: float for scaling
        out:
            -output: scaled and shifted web_mercator_list
        """
        output = []
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        origin_x, origin_y, origin_z = transformer.transform(origin[1], origin[0], origin[2])
        for x, y, z in web_mercator_list:
            output.append(((x - origin_x) * scale_factor, (y - origin_y) * scale_factor, (z - origin_z) * scale_factor))
        return output

class MakePly:
    def ply_from_tuple_3D_list(output_path, tuple_3D_list, comment="none"):
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
            for x, y, z in tuple_3D_list:
                file.write(f"{x} {y} {z}\n")
            
    def ply_from_point3D_list(output_path, point3D_list, comment="none"):
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
                x, y, z = point3D.xyz
                r, g, b = point3D.color
                file.write(f"{x} {y} {z} {r} {g} {b}\n")

#REPLACE THIS WITH THE LAT/LON/ALT THAT YOU WANT TO BE THE ORIGIN. THIS IS SOME POINT ON CAMPBELL
LAT_0 = 34.41622191
LON_0 = -119.8456223
H_0 = 15.223058115078384


all_point3Ds = []
all_xyzs = []
recons = Parsing.get_recons("./recons/priors no extra options/campbell")
for recon in recons:
    all_point3Ds = all_point3Ds + Parsing.get_point3Ds(recon)
for point3D in all_point3Ds:
    all_xyzs.append(tuple(point3D.xyz))
all_mercator_web = CoordConversions.ecef_to_web_mercator_tuple_3D_list(all_xyzs)
all_mercator_web = CoordConversions.web_mercator_scale_and_define_origin(all_mercator_web, (LAT_0, LON_0, H_0), 1)
for a in range(len(all_point3Ds)):
    all_point3Ds[a].xyz = all_mercator_web[a]
MakePly.ply_from_point3D_list("./plys/WebMercator/priors no extra options/campbell.ply", all_point3Ds, "campbell")

#getting all pt 3ds
# all_point3Ds = []
# for recon in recons:
#     all_point3Ds = all_point3Ds + Parsing.get_point3Ds(recon)
# all_point3Ds = CoordConversions.ecef_to_enu_point3D(all_point3Ds, (LAT_0, LON_0, H_0))
# MakePly.ply_from_point3D_list("./plys/campbelllocked.ply", all_point3Ds, (LAT_0, LON_0, H_0), "campbelllocked")

#getting all cam coords
# all_img_world_coords = []
# for recon in recons:
#     all_img_world_coords = all_img_world_coords + [tuple(img_coord_tuple[1]) for img_coord_tuple in get_img_world_coords(recon)]
# ply_from_tuple_3D_list_ecef_to_enu("./plys/priors no extra options/ESB_cams.ply", all_img_world_coords, (LAT_0, LON_0, H_0))

all_point3Ds = []

