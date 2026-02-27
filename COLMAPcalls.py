import subprocess
from pathlib import Path

#run on parent directory
PARENT_DIR = "./"
DATABASE_PATH = f"{PARENT_DIR}/data/features.db"
IMG_PATH = f"{PARENT_DIR}/data/imgs"
def setup_directory():
    subprocess.run(["mkdir", f"{PARENT_DIR}/data"])
    subprocess.run(["mkdir", IMG_PATH])
    subprocess.run(["mkdir", f"{PARENT_DIR}/georegistered"])
    subprocess.run(["mkdir", f"{PARENT_DIR}/sparse cloud"])
    subprocess.run(["touch", DATABASE_PATH])

def feature_extraction():
    return subprocess.run(["colmap", "feature_extractor", 
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH],
                            capture_output=True, text=True)
def feature_matching():
    return subprocess.run(["colmap", "exhaustive_matcher", 
                            "--database_path", DATABASE_PATH],
                            capture_output=True, text=True)
def feature_mapper():
    return subprocess.run(["colmap", "mapper",
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH,
                            "--output_path", f"{PARENT_DIR}/sparse cloud"],
                            capture_output=True, text=True)
def feature_pose_prior_mapper(ref_images_dir):
    return subprocess.run(["colmap", "pose_prior_mapper",
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH,
                            "--output_path", f"{PARENT_DIR}/sparse cloud"],
                            capture_output=True, text=True)
def model_aligner(ref_images_dir):#relative to parent dir and no ./ at beginning
    outputs = []
    current_dir = Path(f"{PARENT_DIR}/sparse cloud")
    dirs = [dir.name for dir in current_dir.iterdir() if dir.is_dir()]
    for name in dirs:
        subprocess.run(["mkdir", f"{PARENT_DIR}/georegistered/{name}"])
        outputs.append(subprocess.run(["colmap", "model_aligner",
                        "--input_path", f"{PARENT_DIR}/sparse cloud/{name}", 
                        "--output_path", f"{PARENT_DIR}/georegistered/{name}", 
                        "--ref_images_path", f"{PARENT_DIR}/{ref_images_dir}", 
                        "--ref_is_gps", "1",
                        "--alignment_type", "ecef",
                        "--alignment_max_error", "3.0"],
                        capture_output=True, text=True))
    return outputs
