# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# lastoolraster.py
# Created on: 2015-12-10 15:07:00.00000
# Author: Sijia Zhang
# Description: 
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
import arcgisscripting
import os
import shutil



# Script arguments
Input_LAS_Folder = arcpy.GetParameterAsText(0)
LAStool_path = arcpy.GetParameterAsText(1)
Return_Selection = arcpy.GetParameterAsText(2)
Cell_Size = arcpy.GetParameterAsText(3)
Reference_Coord = arcpy.GetParameter(4)
Output_Folder = arcpy.GetParameterAsText(5)
raster_format = arcpy.GetParameterAsText(6)
Output_Raster = arcpy.GetParameterAsText(7)




# Load required toolboxes
gp = arcgisscripting.create(10.1)
gp.AddToolbox(LAStool_path)

# Local variables:
laslist = os.listdir(Input_LAS_Folder)
arcpy.gp.toolbox = "F:\\lastools\\LAStools\\ArcGIS_toolbox\\LAStools.tbx"
raster_paths = []

# Process: Iterate Files to run blast2dem
arcpy.AddMessage("Processing: Running Blast2DEM tool in LAStool...")
for file in laslist:
    path = os.path.join(Input_LAS_Folder,file)
    name = os.path.basename(path)
    new_name = name + "_b." + raster_format
    new_path = os.path.join(Output_Folder,new_name)
    arcpy.gp.blast2dem(path, Cell_Size, "100", "elevation", "actual values", "north east", "1 pm", "", "",
                       Return_Selection, "false",raster_format,new_path, Output_Folder , "", "", "true")
    raster_paths.append(new_path)
arcpy.AddMessage("Completed Blast2DEM tool in LAStool...")

# Process7: Define coordinate system for the Raster dataset:
arcpy.AddMessage("Processing: Define coordinate system for the Raster dataset...")
sr = Reference_Coord
for raster in raster_paths:
    arcpy.DefineProjection_management(raster, sr)

# Process: Mosaic all the Raster dataset into one:
arcpy.AddMessage("Processing: Mosaic all the Raster dataset into one...")
if len(raster_paths) == 1:
    shutil.copyfile(raster_paths[0], Output_Raster)
elif len(raster_paths) == 0:
    arcpy.AddMessage("ERROR: Raster mosaic incomplete!")
else:
    last_raster_path = raster_paths.pop()
    shutil.copyfile(last_raster_path, Output_Raster)
    arcpy.Mosaic_management(";".join(raster_paths), Output_Raster, "BLEND", "MATCH","", "", "", "", "NONE")
arcpy.AddMessage(" raster data conversion is complete! " +
                 "Check the raster dataset in your selected output folder")


