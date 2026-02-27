from pillow_heif import register_heif_opener
from PIL import Image 
from pathlib import Path

def convert_imgs_to_jpg(src_path, output_path):
    """
    in:
        -src_path: dir to original img folder
        -output_path: dir to output
    out:
        -folder of converted imgs
    """
    register_heif_opener()
    img_names = [f.name for f in Path(src_path).iterdir() if f.is_file]
    for img_name in img_names:
        pil_img = Image.open(f"{src_path}/{img_name}")
        if pil_img.mode in ('RGBA', 'P', 'LA'):
            temp = Image.new("RGB", pil_img.size, (255, 255, 255))
            temp.paste(pil_img, mask=pil_img.split()[3] if pil_img.mode == 'RGBA' else None)
            pil_img = temp
        pil_img.save(f"./{output_path}/{img_name[:img_name.find(".")+1]}jpg", 'JPEG', quality=95)