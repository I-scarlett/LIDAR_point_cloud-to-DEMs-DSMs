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
import sys
import subprocess


# Script arguments

Input_LAS_Folder = arcpy.GetParameterAsText(0)
Fusion_Folder = arcpy.GetParameterAsText(1)
Choose_Model = arcpy.GetParameterAsText(2)
Output_Folder = arcpy.GetParameterAsText(3)
Output_Raster = arcpy.GetParameterAsText(4)



# Local variables:
lasfile_list = os.listdir(Input_LAS_Folder)




# Process1: Remove the spaces in las file names:
arcpy.AddMessage("Processing: Remove spaces in las file names...")
for filename in lasfile_list: 
    new_filename = filename.replace(" ","")
    os.rename(os.path.join(Input_LAS_Folder,filename),
              os.path.join(Input_LAS_Folder,new_filename))    

# Process2: Create a new folder to store the outcome files:
arcpy.AddMessage("Processing: Create a new folder in the Input LAS Folder to store the output...")
Las2Rastertool_output = os.path.join(Output_Folder,"Las2Rastertool_output")
if not os.path.isdir(Las2Rastertool_output):
   os.makedirs(Las2Rastertool_output)


# Process3: Create a text file to store all las file names:
arcpy.AddMessage("Processing: Create a text file to store all las file names...")
txt_path = os.path.join(Las2Rastertool_output,"lasfile_names.txt")
f = open(txt_path,"w")
lasfile_list = os.listdir(Input_LAS_Folder)
for filename in lasfile_list:
    file_path = os.path.join(Input_LAS_Folder,filename)
    f.write(file_path + "\n")
f.close()


# Process4: Using FUSION tool to create Bare earth/ Canopy Surface Model / Canopy Height Model:
arcpy.AddMessage("Processing: Using FUSION tool to create " + Choose_Model + "...")
if (Choose_Model == "Bare Earth Model" ):
    Executable_Path = os.path.join(Fusion_Folder,"Groundfilter.exe")
    lda_path = os.path.join(Las2Rastertool_output,"las_groundpoints.las")
    parameters = [Executable_Path , "/gparam:-1" ,"/wparam:2" ,"/tolerance:0.1" ,"/iterations:10",
                  lda_path,"5",txt_path]
    subprocess.call(parameters)
    
    Executable_Path2 = os.path.join(Fusion_Folder,"gridsurfacecreate.exe")
    dtm_path = os.path.join(Las2Rastertool_output,"las_surface.dtm")
    parameters2 = [Executable_Path2, dtm_path, "5", "M", "M", "1", "16", "2", "2", lda_path]
    subprocess.call(parameters2)
    output_dtm = dtm_path
    arcpy.AddMessage(Choose_Model + " dtm format is completed!")

elif (Choose_Model == "Canopy Surface Model"):
    Executable_Path = os.path.join(Fusion_Folder,"canopymodel.exe")
    csm_path = os.path.join(Las2Rastertool_output,"las_CanopySurface.dtm")
    parameters = [Executable_Path, csm_path, "5", "M", "M", "1", "16", "2", "2", txt_path]
    subprocess.call(parameters)
    output_dtm = csm_path
    arcpy.AddMessage(Choose_Model + " dtm format is completed!")
    
elif (Choose_Model == "Canopy Height Model"):
     Executable_Path = os.path.join(Fusion_Folder,"canopymodel.exe")
     dtm_path = os.path.join(Las2Rastertool_output,"las_surface.dtm")
     chm_path = os.path.join(Las2Rastertool_output,"las_CanopyaHeight.dtm")
     parameters = [Executable_Path,"/ground:" + dtm_path, chm_path , "5", "M", "M", "1", "16", "2", "2", txt_path]
     subprocess.call(parameters)
     output_dtm = chm_path
     arcpy.AddMessage(Choose_Model + " dtm format is completed!")
  
else :
    exit(-1)
    arcpy.AddMessage("ERROR! dtm format is not completed!")

# Process5：Export the model(dtm) into Ascii format:
arcpy.AddMessage("Processing: Export the dtm model into Ascii format...")
Executable_Path = os.path.join(Fusion_Folder,"DTM2ASCII.exe")
output_Ascii = os.path.splitext(output_dtm)[0] + ".asc"
parameters = [Executable_Path,output_dtm,output_Ascii]
subprocess.call(parameters)    

# Process6: Using Arcgis toolbox to convert the Ascii format into raster format:
arcpy.AddMessage("Processing: Using Arcgis toolbox to convert the Ascii format into raster format...")
arcpy.ASCIIToRaster_conversion(output_Ascii, Output_Raster, "FLOAT")
arcpy.AddMessage(Choose_Model + "raster data conversion is complete! Check the raster dataset in your selected output folder")
