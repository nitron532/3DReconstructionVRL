from pathlib import Path
import csv
import xml.etree.ElementTree as ET


def test(src_path, out_path):
    """
    in:
        -src_path: path to the xml file with pt info
        -output_path: where you want you output file + name
    out:
        -count: number of emlid pt associations found (for sanity check)
        creates file of poses associated with imgs readable by colmap
    """
    tree = ET.parse(src_path)
    with open(out_path, "w") as out_file:
        count = 0
        for photo in tree.getroot().iter('Photo'):
            match = photo.find('Match')
            #if has corresponding emlid point
            matched = match.find('Matched')
            
            if matched.text.lower() == 'true':
                photo_path = photo.find('Path').text
                photo_name = photo_path[photo_path.rfind('\\')+1:]

                emlidgps = match.find('EmlidGps')
                latitude = emlidgps.find('Latitude').text
                longitude = float(emlidgps.find('Longitude').text)
                orthometric_height = float(emlidgps.find('OrthometricHeight').text)
                out_file.write(f"{photo_name} {latitude} {longitude} {orthometric_height}\n")
                count += 1
    return count

test("./manifest_photo_emlid.xml", "./out/something.txt")
