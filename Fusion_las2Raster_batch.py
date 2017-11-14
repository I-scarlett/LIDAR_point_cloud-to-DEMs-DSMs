# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Las2Rastertool.py
# Created on: 2015-12-20 15:37:00.00000
# Author:  Sijia Zhang
# Description: 
# This tool helps the user to process LIDAR las data and convert .las into 
# Bare earth raster(DEM), canopy surface model(CSM) or Canopy Height Model.
# This tool integrates with FUSION and Arcgis toolbox.
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
import os
import subprocess
import shutil
import time


# Script arguments

Input_LAS_Folder = arcpy.GetParameterAsText(0)
Fusion_Folder = arcpy.GetParameterAsText(1)
Reference_Coord = arcpy.GetParameter(2)
Choose_Model = arcpy.GetParameterAsText(3)
Output_Folder = arcpy.GetParameterAsText(4)
Output_Raster = arcpy.GetParameterAsText(5)
UTM_Zone = arcpy.GetParameterAsText(6)


# Local variables:
lasfile_list = os.listdir(Input_LAS_Folder)
BATCH_COUNT = 32
CELL_SIZE = 5
UNIT = "M"

raster_format = os.path.splitext(Output_Raster)[1]




# Process1: Remove the spaces in las file names:
arcpy.AddMessage("Processing: Remove spaces in las file names...")
for filename in lasfile_list: 
    new_filename = filename.replace(" ", "")
    os.rename(os.path.join(Input_LAS_Folder, filename),
              os.path.join(Input_LAS_Folder, new_filename))

# Process2: Create a new folder to store the output:
arcpy.AddMessage("Processing: Create a new folder in the Input LAS Folder to store the output...")
Las2Rastertool_output = os.path.join(Output_Folder, "Las2Rastertool_output")
if not os.path.isdir(Las2Rastertool_output):
   os.makedirs(Las2Rastertool_output)


# Process3: Create text files and loop through all las files:
arcpy.AddMessage("Processing: Create text files to store las file names...")
txt_paths = []
file_count = 0
lasfile_list = os.listdir(Input_LAS_Folder)
for filename in lasfile_list:
    if file_count % BATCH_COUNT == 0:
        arcpy.AddMessage("Processing: Create a text file to store " + str(BATCH_COUNT) + " las file names...")
        if file_count != 0:
            f.close()
        txt_path = os.path.join(Las2Rastertool_output,
                                "lasfile_names" + "_" + str(len(txt_paths)) + ".txt")
        txt_paths.append(txt_path)
        f = open(txt_path, "w")
    file_path = os.path.join(Input_LAS_Folder, filename)
    f.write(file_path + "\n")
    file_count += 1
f.close()

# read/create check point
checkpoint_file = os.path.join(Las2Rastertool_output, "checkpoint.txt")
checkpoint_handle = None
processed_files = []
if os.path.exists(checkpoint_file):
    checkpoint_handle = open(checkpoint_file, "r")
    for line in checkpoint_handle:
        processed_files.append(line)
    checkpoint_handle.close()
    os.remove(checkpoint_file)

# Process4: loop through all txt files and use FUSION tool to create
# Bare earth/ Canopy Surface Model / Canopy Height Model:
txt_count = 0
raster_paths = []
for txt_path in txt_paths:
    # skip processed file
    txt_processed = False
    for processed_file in processed_files:
        if processed_file == txt_path:
            txt_processed = True
            break
    if txt_processed:
        arcpy.AddMessage("Skipping processed file " + txt_path)
        continue

    arcpy.AddMessage("Processing: Using FUSION tool to create " + Choose_Model + "...")
    if ((Choose_Model == "Bare Earth Model") or ( Choose_Model == "Canopy Height Model")):
        Executable_Path = os.path.join(Fusion_Folder, "Groundfilter.exe")
        lda_path = os.path.join(Las2Rastertool_output, "las_groundpoints" + "_" + str(txt_count) + ".las")
        parameters = [Executable_Path , "/gparam:-1",  "/wparam:" + str(CELL_SIZE), "/tolerance:0.1", "/iterations:10",
                      lda_path, str(CELL_SIZE),txt_path]
        subprocess.call(parameters)

        Executable_Path2 = os.path.join(Fusion_Folder,"gridsurfacecreate.exe")
        surface_path = os.path.join(Las2Rastertool_output,"las_surface" + "_" + str(txt_count) + ".dtm")
        parameters2 = [Executable_Path2, surface_path, str(CELL_SIZE), UNIT, UNIT, "1", UTM_Zone, "2", "2", lda_path]
        subprocess.call(parameters2)
        output_dtm = surface_path
        os.remove(lda_path)
        arcpy.AddMessage(Choose_Model + " " + str(txt_count) + " dtm format is completed!")

    if (Choose_Model == "Canopy Surface Model"):
        Executable_Path = os.path.join(Fusion_Folder,"canopymodel.exe")
        csm_path = os.path.join(Las2Rastertool_output,"las_CanopySurface" + "_" + str(txt_count) + ".dtm")
        parameters = [Executable_Path, csm_path, str(CELL_SIZE), UNIT, UNIT, "1", UTM_Zone, "2", "2", txt_path]
        subprocess.call(parameters)
        output_dtm = csm_path
        arcpy.AddMessage(Choose_Model + " " + str(txt_count) + " dtm format is completed!")

    if (Choose_Model == "Canopy Height Model"):
         Executable_Path = os.path.join(Fusion_Folder,"canopymodel.exe")
         surface_path = os.path.join(Las2Rastertool_output,"las_surface" + "_" + str(txt_count) + ".dtm")
         chm_path = os.path.join(Las2Rastertool_output,"las_CanopyaHeight" + "_" + str(txt_count) + ".dtm")
         parameters = [Executable_Path, "/ground:" + surface_path, chm_path, str(CELL_SIZE), UNIT, UNIT, "1", UTM_Zone, "2", "2", txt_path]
         subprocess.call(parameters)
         output_dtm = chm_path
         os.remove(surface_path)
         arcpy.AddMessage(Choose_Model + " " + str(txt_count) + " dtm format is completed!")


    # Process5：Export the model(dtm) into Ascii format:
    arcpy.AddMessage("Processing: Export the dtm model into Ascii format...")
    Executable_Path = os.path.join(Fusion_Folder, "DTM2ASCII.exe")
    output_Ascii = os.path.splitext(output_dtm)[0] + ".asc"
    parameters = [Executable_Path,output_dtm, output_Ascii]
    subprocess.call(parameters)
    os.remove(output_dtm)

    # Process6: Using Arcgis toolbox to convert the Ascii format into raster format:
    arcpy.AddMessage("Processing: Using Arcgis toolbox to convert the Ascii format into raster format...")
    arcpy.ASCIIToRaster_conversion(output_Ascii, Output_Raster, "FLOAT")
    output_raster_new = os.path.splitext(Output_Raster)[0] + "_" + str(txt_count) + raster_format
    os.rename(Output_Raster, output_raster_new)
    raster_paths.append(output_raster_new)
    txt_count += 1
    os.remove(output_Ascii)

    # write processed
    if (os.path.exists(checkpoint_file)):
        checkpoint_handle = open(checkpoint_file, "w+")
    else:
        checkpoint_handle = open(checkpoint_file, "w")
    checkpoint_handle.write(txt_path + "\n")
    checkpoint_handle.close()

    # wait for a while to avoid overloading
    time.sleep(180)


# Process7: Define coordinate system for the Raster dataset:
arcpy.AddMessage("Processing: Define coordinate system for the Raster dataset...")
sr = Reference_Coord
for raster in raster_paths:
    arcpy.DefineProjection_management(raster, sr)

# Process8: Mosaic all the Raster dataset into one:
arcpy.AddMessage("Processing: Mosaic all the Raster dataset into one...")
if len(raster_paths) == 1:
    shutil.copy(raster_paths[0], Output_Raster)
elif len(raster_paths) == 0:
    arcpy.AddMessage("ERROR: Raster mosaic incomplete!")
else:
    last_raster_path = raster_paths.pop()
    shutil.copy(last_raster_path, Output_Raster)
    arcpy.Mosaic_management(";".join(raster_paths), Output_Raster, "BLEND", "MATCH",
                            "", "", "", "", "")
arcpy.AddMessage(Choose_Model + " raster data conversion is complete! " +
                 "Check the raster dataset in your selected output folder")









