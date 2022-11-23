#!/usr/bin/env python

"""
File: read-XDE.py
copyright 2022 Doug Blanding (dblanding@gmail.com)
The goal of this file is to read a document stored in .xbf format
then save the document in Step format.
I can't get this working in python, although the C++ code works fine.

The failure is at the very last line:
RuntimeError: Standard_Failure cannot close a document that has not
been opened raised from method Close of class TDocStd_Application
"""

from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.STEPCAFControl import STEPCAFControl_Writer
from OCC.Core.STEPControl import STEPControl_AsIs
from OCC.Core.XSControl import XSControl_WorkSession

def create_doc():
    """Create (and return) XCAF doc and app

    entry       label <class 'OCC.Core.TDF.TDF_Label'>
    0:1         doc.Main()                          (Depth = 1)
    0:1:1       shape_tool is at this label entry   (Depth = 2)
    0:1:2       color_tool at this entry            (Depth = 2)
    0:1:1:1     root_label and all referred shapes  (Depth = 3)
    0:1:1:x:x   component labels (references)       (Depth = 4)
    """

    # Initialize the document
    # Choose format for TDocStd_Document
    doc_format = "BinXCAF"  # Use file ext .xbf to save in binary format
    # doc_format = "XmlXCAF"  # Use file ext .xml to save in xml format
    doc = TDocStd_Document(TCollection_ExtendedString(doc_format))
    app = XCAFApp_Application_GetApplication()
    app.NewDocument(TCollection_ExtendedString(doc_format), doc)
    binxcafdrivers_DefineFormat(app)
    # xmlxcafdrivers_DefineFormat(app)
    return doc, app


if __name__ == "__main__":

    doc_file = "../models/as1-oc-214.xbf"
    step_file_name = "/home/doug/Desktop/test-open-doc.stp"

    doc, app = create_doc()

    # Read doc from .xbf file
    app.Open(TCollection_ExtendedString(doc_file), doc)

    # Initialize STEP exporter
    WS = XSControl_WorkSession()
    step_writer = STEPCAFControl_Writer(WS, False)

    # Transfer shapes
    step_writer.Transfer(doc, STEPControl_AsIs)

    # Write step file
    write_status = step_writer.Write(step_file_name)
    if write_status == IFSelect_RetDone:
        print(f"STEP file saved to {step_file_name}\n")
    else:
        print(f"Save step file failed. {write_status = }")

    app.Close(doc)