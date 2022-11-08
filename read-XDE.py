#!/usr/bin/env python

"""
open_file.py
copyright 2022 Doug Blanding (dblanding@gmail.com)
The goal of this file is to read the XDE data from the files written by compose-XDE.py
Two files were written: doc.xbf and chassis.stp
Lesson 15: Export OpenCascade assemblies to STEP with names and colors at:
https://www.youtube.com/watch?v=dq2-evewPeA&list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ&index=7
This video is one in a series of Open Cascade Lessons at Quaoar's Workshop:
https://www.youtube.com/playlist?list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ

This document can be stored using one of two main storage formats:
  1. binary version BinXCAF producing .xbf files
  2. XmlXCAF producing .xml files.
https://unlimited3d.wordpress.com/2021/09/08/xcaf-b-rep-changes-in-occt-7-6-0/
"""

import os
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool)
from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.XmlXCAFDrivers import xmlxcafdrivers_DefineFormat
from OCC.Core.PCDM import PCDM_RS_OK
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.STEPCAFControl import STEPCAFControl_Writer
from OCC.Core.IFSelect import IFSelect_RetDone

# Choose format for TDocStd_Document
# format = "BinXCAF"  # Use file ext .bxf to save in binary format
format = "XmlXCAF"  # Use file ext .xml to save in xml format
doc = TDocStd_Document(TCollection_ExtendedString(format))
app = XCAFApp_Application_GetApplication()
binxcafdrivers_DefineFormat(app)
xmlxcafdrivers_DefineFormat(app)
app.NewDocument(TCollection_ExtendedString(format), doc)

# Note that the method XCAFDoc_DocumentTool_ShapeTool returns
# the XCAFDoc_ShapeTool. The first time this method is used,
# it creates the XCAFDoc_ShapeTool.
shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())

doc1 = doc

def set_environ_vars():
    """In OCCT, it is necessary to set a couple of environment variables
    However, in pythonOCC I do not believe it is necessary."""

    path = "/home/doug/OCC/opencascade-7.6.0/src/XmlXCAFDrivers"
    os.environ['CSF_PluginDefaults'] = path
    os.environ['CSF_XCAFDefaults'] = path

def get_environ_vars():
    """Print a couple of important environment variables
    In OCCT, it is necessary to set a couple of environment variables
    However, in pythonOCC I do not believe it is necessary."""

    variables = ['CSF_PluginDefaults',
                 'CSF_XCAFDefaults',
                 'CASROOT',
                 'USER',
                 ]
    for v in variables:
        print(f"{v} : {os.getenv(v)}")
    print("")

def open_doc(fname):
    """Open (.xbf or .xml) file, return doc"""

    # Read file and transfer to doc
    read_status = app.Open(TCollection_ExtendedString(fname), doc)
    shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
    shape_tool.UpdateAssemblies()
    if read_status == PCDM_RS_OK:
        print("File opened successfully.")
    else:
        print("Unable to open file.")

    return doc


def write_step(doc, step_file_name):
    # initialize STEP exporter
    step_writer = STEPCAFControl_Writer()
    # transfer shapes and write file
    step_writer.Transfer(doc)
    status = step_writer.Write(step_file_name)
    if status == IFSelect_RetDone:
        print(f"STEP file saved to {step_file_name}\n")
    else:
        print(f"write_step {status = }")


if __name__ == "__main__":

    # set_environ_vars()

    step_file_name = "/home/doug/Desktop/save_chassis.stp"
    doc_file = "/home/doug/Desktop/doc.xml"
    doc = open_doc(doc_file)
    write_step(doc, step_file_name)
    if doc1 is doc:
        print("doc was unchanged by app.open()")