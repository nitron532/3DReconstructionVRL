import subprocess
from pathlib import Path

#run on parent directory
PARENT_DIR = "./current/ESB" #change to what your parent dir is (with recon folders, data folder, etc)
DATABASE_PATH = f"{PARENT_DIR}/data/features.db"
IMG_PATH = f"{PARENT_DIR}/data/imgs"
SPARSE_OUTPUT_PATH = f"{PARENT_DIR}/recons/no priors no extra options"
ALIGNED_OUTPUT_PATH = f"{PARENT_DIR}/aligned recons/no priors no extra options"

def setup_directory():
    subprocess.run(["mkdir", f"{PARENT_DIR}/data"])
    subprocess.run(["mkdir", f"{PARENT_DIR}/recons"])
    subprocess.run(["mkdir", f"{PARENT_DIR}/aligned recons"])
    subprocess.run(["mkdir", IMG_PATH])
    subprocess.run(["touch", DATABASE_PATH])

def feature_extraction():
    subprocess.run(["colmap", "feature_extractor", 
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH],
                            stdout=None)
def feature_matching():
    subprocess.run(["colmap", "exhaustive_matcher", 
                            "--database_path", DATABASE_PATH],
                            stdout=None)
def mapper():
    subprocess.run(["mkdir", f"{SPARSE_OUTPUT_PATH}"], 
                        stdout=None)
    subprocess.run(["colmap", "mapper",
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH,
                            "--output_path", f"{SPARSE_OUTPUT_PATH}"],
                            stdout=None)
def pose_prior_mapper(ref_images_dir):
    subprocess.run(["mkdir", f"{SPARSE_OUTPUT_PATH}"], 
                        stdout=None)
    subprocess.run(["colmap", "pose_prior_mapper",
                            "--database_path", DATABASE_PATH,
                            "--image_path", IMG_PATH,
                            "--output_path", f"{SPARSE_OUTPUT_PATH}",
                            "--prior_position_std_x", "1",
                            "--prior_position_std_y", "1",
                            "--prior_position_std_z", "1"],
                            stdout=None)
def model_aligner(ref_images_dir):#relative to parent dir and no ./ at beginning
    subprocess.run(["mkdir", f"{ALIGNED_OUTPUT_PATH}"])
    outputs = []
    dirs = [dir.name for dir in Path(SPARSE_OUTPUT_PATH).iterdir() if dir.is_dir()]
    for name in dirs:
        subprocess.run(["mkdir", f"{ALIGNED_OUTPUT_PATH}/{name}"], 
                        stdout=None)
        subprocess.run(["colmap", "model_aligner",
                        "--input_path", f"{SPARSE_OUTPUT_PATH}/{name}", 
                        "--output_path", f"{ALIGNED_OUTPUT_PATH}/{name}", 
                        "--ref_images_path", f"{PARENT_DIR}/{ref_images_dir}", 
                        "--ref_is_gps", "1",
                        "--alignment_type", "ecef",
                        "--alignment_max_error", "3.0"],
                        stdout=None)
    return outputs
