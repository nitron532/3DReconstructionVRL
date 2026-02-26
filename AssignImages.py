#FAULTY -- DO NOT USE -- FIX IN PROGRESS

#Creates a file tying img file names with their gps coords 
from pathlib import Path
import pandas as pd
from PIL import Image 
from pillow_heif import register_heif_opener
from pyproj import Transformer
import pyproj

class Img:
    name = ""
    number = -1
    def __init__(self, name, number):
        self.name = name
        self.number = number

def get_number(img):
    """
    in:
        -img: Img obj
    out:
        -number: number of that Img obj
    """
    return img.number

def get_img_names(img_dir):
    """
    in:
        -img_dir: directory of imgs
    out:
        -img_name_list: list of file names of imgs in img directory
    """
    img_obj_list = []
    img_name_list = []
    for f in Path(img_dir).iterdir():
        if f.is_file():
            img_obj_list.append(Img(f.name, f.name[-9:-5]))
    img_obj_list.sort(key=get_number)
    for img in img_obj_list:
        img_name_list.append(img.name)
    return img_name_list

def convert_imgs_to_jpg(src_dir, output_dir):
    """
    in:
        -src_dir: dir to original img folder
        -output_dir: dir to output
    out:
        -folder of converted imgs
    """
    register_heif_opener()
    img_names = get_img_names(src_dir)
    for img_name in img_names:
        pil_img = Image.open(f"{src_dir}/{img_name}")
        if pil_img.mode in ('RGBA', 'P', 'LA'):
            temp = Image.new("RGB", pil_img.size, (255, 255, 255))
            temp.paste(pil_img, mask=pil_img.split()[3] if pil_img.mode == 'RGBA' else None)
            pil_img = temp
        pil_img.save(f"./{output_dir}/{img_name[:-4]}jpg", 'JPEG', quality=95)

def assign_images(img_dir, points_dir, output_dir):
    """
    in:
        -img_dir: dir to img folder
        -points_dir: dir to points csv
        -output_dir: dir to output
    out:
        -saved point.colmap formatted file
    """
    pyproj.network.set_network_enabled(True)
    transformer = Transformer.from_crs("EPSG:4979", "EPSG:4326+5773", always_xy=True)
    with open(output_dir, 'w') as file:
        img_name_list = get_img_names(img_dir)
        points = pd.read_csv(points_dir)
        for idx, row in points.iterrows():
            ellipsoidal_height = float(row['Ellipsoidal height'])
            latitude = float(row['Latitude'])
            longitude = float(row['Longitude'])
            _, _, altitude = transformer.transform(longitude, latitude, ellipsoidal_height)
            file.write(f"{img_name_list[idx]} {latitude} {longitude} {altitude}\n")
# convert_imgs_to_jpg("./imgs", "./jpg_imgs")

assign_images("./chem_jpg_imgs", "./chem.csv", "./chem.txt")

