from copy import copy
import os
import shutil
import json
import zipfile
import numpy as np
from cv2 import imread, error
from datetime import datetime as dt

def unzip_file(zippath, dstpath):
    with zipfile.ZipFile(zippath, 'r') as zip_ref:
        path = os.path.join(dstpath, os.path.basename(zippath)[:-4])
        zip_ref.extractall(path)

def get_photo_month(jsonpath: str):
    f = open(jsonpath, 'r')
    j = json.load(f)
    t = dt.fromtimestamp(int(j["photoTakenTime"]["timestamp"]))
    monthname = t.strftime("%m %B %Y")
    return monthname

def check_repeated(src_imgpath: str, dst_imgpath: str):
    try:
        src_im = imread(src_imgpath)
        dst_im = imread(dst_imgpath)
        # Check if both images are equal
        if src_im.shape == dst_im.shape and not(np.bitwise_xor(src_im, dst_im).any()):
            return True
    except AttributeError as e:
        print("Video file:", os.path.basename(src_imgpath))     # Video files will be rejected by default
        return True
    return False

def handle_repeated(src_imgpath: str, dst_imgpath: str):
    count = 0
    path, ext = os.path.splitext(dst_imgpath)
    # If an image with the same name already exists
    while os.path.exists(dst_imgpath) and not check_repeated(src_imgpath, dst_imgpath):    
    # If both images are not the same
        print(f"Error! Path already exists: {dst_imgpath}")
        count += 1
        dst_imgpath = path + f"({count})" + ext
    if os.path.exists(dst_imgpath):     # If name still exists, that exact image already exists
        print("Repeated image or video!")
        return ""                       # Return empty string
    return dst_imgpath                  # Return path with no repetition  

def check_image_name(src_imgpath: str):
    if not os.path.exists(src_imgpath):
        imgname = os.path.basename(src_imgpath)
        album = os.path.dirname(src_imgpath)
        photos = [f.path for f in os.scandir(album) if imgname in f.name and os.path.splitext(f.name)[1] != ".json"]
        return "" if photos == [] else photos[0]
    return src_imgpath

folderpath = os.path.realpath("D:\Imágenes\phototest\Photo Manager")      # Top directory

zippath = os.path.realpath("D:\Imágenes\phototest\Zips 28-02-2024")         # Directory with zip folders from Google Takeout
os.makedirs(os.path.join(zippath, "Extracted"), exist_ok=True)              # Create "Extracted" folder if it doesn't exist
ziplist = [f.path for f in os.scandir(zippath) if os.path.splitext(f.name)[1] == ".zip"]    # List of zips to extract
for zip in ziplist:
    print("Extracting zip file:", os.path.basename(zip))
    unzip_file(zip, folderpath)                             # Extract zip
    shutil.move(zip, os.path.join(zippath, "Extracted"))    # Move file to "Extracted" folder

takeoutpath = "Takeout\Google Photos"                       # Path from zip folder to photos

resulting_folder = "Photos"             # Name of destiny folder for resulting photos

folderlist = [f.name for f in os.scandir(folderpath) if f.is_dir()]     # Get list of extracted zip folders on top directory

for folder in folderlist:
    if folder != resulting_folder:      # Don't analyse destiny folder
        print("Analysing folder:", folder)
        path = os.path.join(folderpath, folder, takeoutpath)            # Access photos in extracted zip
        if not os.path.exists(path):
            print("Folder does not follow Google Takeout format, it will be skipped")
            continue
        albumlist = [f.path for f in os.scandir(path) if f.is_dir()]    # Get list of photo "albums"
        for album in albumlist:
            print("Analysing album:", os.path.basename(album))
            jsonlist = [f.path for f in os.scandir(album) if os.path.splitext(f.name)[1] == ".json"]    # Get list of jsons in album
            for jsonpath in jsonlist:
                if os.path.basename(jsonpath) != "metadata.json":     # Exclude album metadata
                    monthname = get_photo_month(jsonpath)       # Get photo month and year
                    yearname = monthname[-4:]
                    src_imgpath = jsonpath[:-5]                 # Get photo path
                    src_imgpath = check_image_name(src_imgpath)
                    if src_imgpath == "":
                        os.remove(jsonpath)                         # Delete json
                        print(f"JSON {os.path.basename(jsonpath)} deleted: {not os.path.exists(jsonpath)}")
                        continue
                    imgname = os.path.basename(src_imgpath)
                    dst_folderpath = os.path.join(folderpath, resulting_folder, yearname, monthname)
                    os.makedirs(dst_folderpath, exist_ok=True)  # If it doesn't exist, create destiny folder for photo month and year
                    dst_imgpath = os.path.join(dst_folderpath, imgname)     # Create image path in destiny folder
                    dst_imgpath = handle_repeated(src_imgpath, dst_imgpath) # Check for duplicates, edit name if necessary
                    if dst_imgpath != "":                           # If not a duplicate:
                        shutil.move(src_imgpath, dst_imgpath)       # Move file
                        print(f"File {imgname} moved: {not os.path.exists(src_imgpath)}")
                    else:                           # If duplicate:
                        os.remove(src_imgpath)      # Delete file
                        print(f"File {imgname} deleted: {not os.path.exists(src_imgpath)}")
                    os.remove(jsonpath)                         # Delete json
                    print(f"JSON {imgname}.json deleted: {not os.path.exists(jsonpath)}")
            metapath = os.path.join(album, "metadata.json")
            if os.path.exists(metapath):
                os.remove(metapath)                         # Delete metadata.json
                print(f"JSON metadata.json from album {os.path.basename(album)} deleted: {not os.path.exists(metapath)}")
            with os.scandir(album) as it:
                remaining_files = [f for f in it]    # List of remaining files
                if remaining_files != []:             # If album not empty, move everything to unknown folder
                    unknownpath = os.path.join(folderpath, resulting_folder, "Unknown")
                    os.makedirs(unknownpath, exist_ok=True)      # Create Unknown folder if it doesn't exist
                    for filepath in remaining_files:
                        filename = os.path.basename(filepath)
                        shutil.move(filepath, os.path.join(unknownpath, filename))          # Move file to Unknown folder
                        print(f"File {filename} moved: {not os.path.exists(filepath)}")
                try: 
                    os.rmdir(album)         # Delete album folder
                    print(f"Folder {os.path.basename(album)} has been removed successfully") 
                except OSError as error: 
                    print(error) 
                    print(f"Folder {os.path.basename(album)} cannot be deleted")
        # Delete analysed folder
        shutil.rmtree(os.path.join(folderpath, folder))
        print(f"Directory {folder} has been removed successfully") 
