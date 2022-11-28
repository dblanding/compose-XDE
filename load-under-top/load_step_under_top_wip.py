#!/usr/bin/env python

"""
load_step_under_top_fixed.py
copyright 2022 Doug Blanding (dblanding@gmail.com)
Revised version of load_step_under_top.py intended to fix problems
of step file assemblies not correctly copied to label under root.

Works much better with as1-oc-214.stp
    saved step file looks perfect
    saved .xml file is not right
    saved .xbf file causes CAD Assistant to crash
Doesn't work as well with as1_pe_203.stp
    neither saved step nor saved .xml files are right
"""

from dataclasses import dataclass
import logging
import os
import os.path

from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.XmlXCAFDrivers import xmlxcafdrivers_DefineFormat
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.PCDM import PCDM_SS_OK
from OCC.Core.STEPCAFControl import (STEPCAFControl_Reader,
                                     STEPCAFControl_Writer)
from OCC.Core.STEPControl import STEPControl_AsIs
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence, TDF_ChildIterator
from OCC.Core.TDocStd import TDocStd_Document, TDocStd_XLinkTool
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Shape, TopoDS_Builder
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool_ShapeTool
from OCC.Core.XSControl import XSControl_WorkSession

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # set to DEBUG | INFO | ERROR


@dataclass
class Prototype:
    """A prototype shape and its associated label

    Instantiate: foo_proto = prototype(shape, label)
    Retrieve: foo_proto.shape  or  foo_proto.label
    """

    shape: TopoDS_Shape
    label: TDF_Label


def create_doc():
    """Create and return XCAF doc and app

    entry       label <class 'OCC.Core.TDF.TDF_Label'>
    0:1         doc.Main()                          (Depth = 1)
    0:1:1       shape_tool is at this label entry   (Depth = 2)
    0:1:2       color_tool at this entry            (Depth = 2)
    0:1:1:1     root_label and all referred shapes  (Depth = 3)
    0:1:1:x:x   component labels (references)       (Depth = 4)
    """

    # Initialize the document
    # Choose format for saved document (change saved file extension accordingly)
    # doc_format = "BinXCAF"  # Use file ext .xbf to save in binary format
    doc_format = "XmlXCAF"  # Use file ext .xml to save in xml format
    doc = TDocStd_Document(TCollection_ExtendedString(doc_format))
    app = XCAFApp_Application_GetApplication()
    app.NewDocument(TCollection_ExtendedString(doc_format), doc)
    binxcafdrivers_DefineFormat(app)
    xmlxcafdrivers_DefineFormat(app)
    return doc, app


def copy_label(source_label, target_label):
    """Inter-document copy (between 2 documents)"""

    XLinkTool = TDocStd_XLinkTool()
    XLinkTool.Copy(target_label, source_label)


def _load_step(file_path):
    """Read step file at file_path, transfer data to doc, return doc."""

    base = os.path.basename(file_path)  # f_name.ext
    f_name, ext = os.path.splitext(base)
    logger.debug("Load file name: %s", file_path)

    # Create a new doc and app for the step file
    step_doc, step_app = create_doc()

    # Create and prepare step reader
    step_reader = STEPCAFControl_Reader()
    step_reader.SetColorMode(True)
    step_reader.SetLayerMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetMatMode(True)

    # Read step file and transfer to doc
    status = step_reader.ReadFile(file_path)
    if status == IFSelect_RetDone:
        logger.info("Transfer doc to STEPCAFControl_Reader")
        step_reader.Transfer(step_doc)

    return f_name, step_doc, step_app


def save_doc(doc, app, f_name):
    """Save doc to file"""

    # One of the few places app is needed
    save_status = app.SaveAs(doc, TCollection_ExtendedString(f_name))
    if save_status == PCDM_SS_OK:
        print(f"File {f_name} saved successfully.")
    else:
        print("File save failed.")


def save_step_doc(doc, save_file_name):
    """Export doc to STEP file."""

    print(f"{save_file_name = }")
    # initialize STEP exporter
    WS = XSControl_WorkSession()
    step_writer = STEPCAFControl_Writer(WS, False)
    print("Step exporter initialized")
    # transfer shapes and write file
    step_writer.Transfer(doc, STEPControl_AsIs)
    status = step_writer.Write(save_file_name)
    print(f"{status = }")
    assert status == IFSelect_RetDone


if __name__ == "__main__":

    # Create main document
    doc, app = create_doc()
    shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())

    # Create top assembly at root
    root_label = shape_tool.NewShape()
    root_shape = shape_tool.GetShape(root_label)
    TDataStd_Name.Set(root_label, TCollection_ExtendedString("Root"))

    # Create target shape & label, store in prototype dataclass
    target_shape = TopoDS_Compound()
    t_builder = TopoDS_Builder()
    t_builder.MakeCompound(target_shape)
    target_proto = Prototype(target_shape, shape_tool.AddShape(target_shape, True))

    # Create root compound shape & label, store in prototype dataclass
    r_builder = TopoDS_Builder()
    r_builder.MakeCompound(root_shape)
    r_builder.Add(root_shape, target_proto.shape)

    # Read step file
    step_file = "../step/as1-oc-214.stp"
    f_name, step_doc, step_app = _load_step(step_file)
    print(f"Opened {f_name}")

    # Assign step file name to target instance
    itr = TDF_ChildIterator(root_label, False)
    while itr.More():
        component_label = itr.Value()
        TDataStd_Name.Set(
            component_label, TCollection_ExtendedString(f_name))
        itr.Next()

    # Get root label of step data to paste (source label)
    step_labels = TDF_LabelSequence()
    step_shape_tool = XCAFDoc_DocumentTool_ShapeTool(step_doc.Main())
    step_shape_tool.GetShapes(step_labels)
    source_label = step_labels.Value(1)

    # Copy source label to target label
    copy_label(source_label, target_proto.label)
    shape_tool.UpdateAssemblies()

    # Save composite step file
    save_file_name = "/home/doug/Desktop/step/as1-under-top.stp"
    save_step_doc(doc, save_file_name)

    # Save composite xml (or .xbf) file
    save_file_name = "/home/doug/Desktop/step/as1-under-top.xml"
    save_doc(doc, app, save_file_name)
