from pathlib import Path
import quaternion
import numpy as np

#only works for txt outputs of COLMAP

class Image:
    def __init__(self, image_line):
        split_image_line = image_line.split(" ")
        self.id = int(split_image_line[0])
        pose_slice = [float(pose_component) for pose_component in split_image_line[1:8]]
        self.pose = (np.quaternion(pose_slice[0], pose_slice[1], pose_slice[2], pose_slice[3]), np.array([pose_slice[4], pose_slice[5], pose_slice[6]]))
        self.camera_id = int(split_image_line[8])
        self.name = split_image_line[9]
        

class Sensor:
    def __init__(self, id, type, pose):
        self.id = id
        self.type = type
        self.pose = pose #tuple (scalar first np quaternion, np.array len 3 translation)
      
    def __lt__(self, other):
        return self.id < other.id

class Rig:
    #not really useful
    # def __init__(self, id, ref_sensor_type, ref_sensor_id):
    #     self.id = id
    #     self.ref_sensor_type = ref_sensor_type
    #     self.ref_sensor_id = ref_sensor_id
    #     self.sensors = []
    
    def __init__(self, rig_line):
        split_rig_line = rig_line.split(" ")
        #handling rig: RIG_ID, NUM_SENSORS, REF_SENSOR_TYPE, REF_SENSOR_ID
        self.id = int(split_rig_line[0])
        self.sensors = dict()

        ref_sensor_type = split_rig_line[2]
        self.ref_sensor_id = int(split_rig_line[3])
        self.add_sensor(Sensor(id=self.ref_sensor_id, 
                            type=ref_sensor_type, 
                            pose=(np.quaternion(1, 0, 0, 0), np.array([0, 0, 0]))
                        ))
        #handling sensors: SENSOR_TYPE, SENSOR_ID, HAS_POSE, [QW, QX, QY, QZ, TX, TY, TZ]
        for a in range(4, len(split_rig_line), 10):
            type = split_rig_line[a]
            id = split_rig_line[a + 1]
            has_pose = int(split_rig_line[a + 2])
            if not has_pose:
                continue
            pose_slice = [float(pose_component) for pose_component in split_rig_line[a + 3:]]
            pose = (np.quaternion(pose_slice[0], pose_slice[1], pose_slice[2], pose_slice[3]), np.array([pose_slice[4], pose_slice[5], pose_slice[6]]))
            self.add_sensor(Sensor(id=id, type=type, pose=pose))

    def add_sensor(self, sensor):
        self.sensors[sensor.id] = sensor
    
    def __lt__(self, other):
        return self.id < other.id
    
class Reconstruction:
    def _get_rigs(self):
        """
        in:
        out: 
        """
        assert Path(f"{self.recon_path}/rigs.txt").exists(), f"cannot find rigs.txt in {self.recon_path}"
        with open(f"{self.recon_path}/rigs.txt", "r") as file:
            for line in file.readlines():
                line = line.strip()
                if line[0] == "#":
                    continue
                rig = Rig(line)
                self.rigs[rig.id] = rig
    def _get_images(self):
        assert Path(f"{self.recon_path}/images.txt").exists(), f"cannot find images.txt in {self.recon_path}"
        with open(f"{self.recon_path}/images.txt", "r") as file:
            lines = [line.strip() for line in file.readlines() if line.strip()[0] != "#"]
            for line_idx in range(0, len(lines), 2):
                image = Image(lines[line_idx])
                self.images[image.id] = image


                

    def __init__(self, recon_path):
        self.recon_path = recon_path
        self.rigs = dict()
        self._get_rigs()
        self.images = dict()
        self._get_images()

    #
    @staticmethod
    def get_recons(proj_path):
        """
        in:
            -proj_path: path to a dir with recon subdirs (0, 1, 2, etc)
        out:
            -recon_list: list of Reconstruction objects that correspond to each recon in the given path (immediate subdirs only)
        """
        recon_list = [Reconstruction(f"{proj_path}/{recon.name}") for recon in Path(proj_path).iterdir() if recon.is_dir()]
        return recon_list
    

#ex:
recons = Reconstruction.get_recons("./fakerecon") #has 0, 1, 2 as subdirs
for recon in recons:
    print("sensor poses:")
    for rig in recon.rigs.values():
        for sensor in rig.sensors.values():
            print(sensor.pose)
    print("\nimg poses:")
    for img in recon.images.values():
        print(img.pose)
    print("\n==========================\n")
