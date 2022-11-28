#!/usr/bin/env python

"""
compose_alt.py
copyright 2022 Doug Blanding (dblanding@gmail.com)
This file is intended to produce a result similar to compose-XDE.py
but utilizes an alternative method.

compose-XDE.py uses TopoDS_Builder.Add() method to add located components
to a top-level assembly. Component labels are created implicitly.
shape_tool.Add() is used to add a top level shape and return the label.
It works well to produce a valid Step file.

compose_alt.py uses ST.AddComponent() method, which explicitly
returns the component label, but unfortunately, doesn't produce
a valid step file (although it does produce a fairly convincing
looking doc_alt.xml file). Anyway, it's trouble. Don't use it.
"""

from dataclasses import dataclass
import math
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCC.Core.gp import (
    gp_Ax2,
    gp_Pnt,
    gp_DY,
    gp_Dir,
    gp_Trsf,
    gp_Vec,
    gp_Quaternion,
)
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_ColorGen,
                              XCAFDoc_ColorSurf,
                              XCAFDoc_DocumentTool_ColorTool)
from OCC.Core.TopoDS import (
    TopoDS_Shape,
    TopoDS_Builder,
    TopoDS_Compound,
)
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.XmlXCAFDrivers import xmlxcafdrivers_DefineFormat
from OCC.Core.PCDM import PCDM_SS_OK
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.STEPCAFControl import STEPCAFControl_Writer
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopTools import TopTools_IndexedMapOfShape
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopExp import topexp_MapShapes
from OCC.Core.TopoDS import TopoDS_Face, topods_Face

# Parameters
OD = 500   # Wheel OD
W = 100   # Wheel width
D = 50    # Axle diameter
L = 1000  # Axle length
CL = 1000  # Chassis length

# Initialize the document
# Choose format for TDocStd_Document
# doc_format = "BinXCAF"  # Use file ext .bxf to save in binary format
doc_format = "XmlXCAF"  # Use file ext .xml to save in xml format
doc = TDocStd_Document(TCollection_ExtendedString(doc_format))
app = XCAFApp_Application_GetApplication()
binxcafdrivers_DefineFormat(app)
xmlxcafdrivers_DefineFormat(app)
app.NewDocument(TCollection_ExtendedString(doc_format), doc)

# Note that the method XCAFDoc_DocumentTool_ShapeTool returns
# the XCAFDoc_ShapeTool. The first time this method is used,
# it creates the XCAFDoc_ShapeTool.
ST = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
CT = XCAFDoc_DocumentTool_ColorTool(doc.Main())


# Define dataclass (Python equivalent of a C struct)
# Initialize: foo_proto = prototype(shape, label)
# Retrieve: foo_proto.shape  or  foo_proto.label
@dataclass
class Prototype:
    """A shape and its associated label"""
    shape: TopoDS_Shape
    label: TDF_Label


@dataclass
class Face_Prototype:
    """A face and its associated label"""
    face: TopoDS_Face
    label: TDF_Label


def create_wheel_proto():
    # Create wheel shape & label, return prototype dataclass
    wheel_origin = gp_Ax2(gp_Pnt(-W/2, 0, 0), gp_Dir(1.0, 0.0, 0.0))
    wheel = BRepPrimAPI_MakeCylinder(wheel_origin, OD/2, W).Shape()
    wheel_proto = Prototype(wheel, ST.AddShape(wheel, False))
    TDataStd_Name.Set(wheel_proto.label, TCollection_ExtendedString("Wheel"))
    return wheel_proto

def create_axle_proto():
    # Create axle shape & label, return prototype dataclass
    axle_origin = gp_Ax2(gp_Pnt(-L/2, 0, 0), gp_Dir(1.0, 0.0, 0.0))
    axle = BRepPrimAPI_MakeCylinder(axle_origin, D/2, L).Shape()
    axle_proto = Prototype(axle, ST.AddShape(axle, False))
    TDataStd_Name.Set(axle_proto.label, TCollection_ExtendedString("Axle"))
    return axle_proto

def create_whl_axl_asy_proto(father_label):
    # Create wheel_axle_asy shape
    wa_asy = TopoDS_Compound()
    builder = TopoDS_Builder()
    builder.MakeCompound(wa_asy)
    c_label = ST.AddComponent(father_label, wa_asy, True)
    TDataStd_Name.Set(c_label, TCollection_ExtendedString("wheel-axle-1"))

    # Get label of wheel-axle assembly
    wa_asy_label = TDF_Label()
    ST.GetReferredShape(c_label, wa_asy_label)
    TDataStd_Name.Set(wa_asy_label, TCollection_ExtendedString("wheel-axle"))

    # create prototype
    wa_proto = Prototype(wa_asy, wa_asy_label)
    return wa_proto

def build_wheel_axle(wheel, axle, L):
    """Build and return a compound shape from wheel & axle."""
    comp = TopoDS_Compound()
    bbuilder = TopoDS_Builder()
    bbuilder.MakeCompound(comp)

    # Location Transformations
    wheelT_right = gp_Trsf()
    wheelT_right.SetTranslationPart(gp_Vec(L/2, 0, 0))
    right_whl_loc = TopLoc_Location(wheelT_right)

    wheelT_left = gp_Trsf()
    qn = gp_Quaternion(gp_Vec(gp_DY()), math.pi)
    R = gp_Trsf()
    R.SetRotation(qn)
    wheelT_left = wheelT_right.Inverted() * R
    left_whl_loc = TopLoc_Location(wheelT_left)

    # Copy shapes (moved by location vector), add to compound
    bbuilder.Add(comp, wheel.Moved(right_whl_loc))
    bbuilder.Add(comp, wheel.Moved(left_whl_loc))
    bbuilder.Add(comp, axle)

    return comp



def write_step(doc, step_file_name):
    # initialize STEP exporter
    step_writer = STEPCAFControl_Writer()

    # transfer shapes and write file
    step_writer.Transfer(doc)
    status = step_writer.Write(step_file_name)
    if status == IFSelect_RetDone:
        print(f"STEP file saved to {step_file_name}\n")


def save_doc(save_file, doc):
    """Save the document"""
    filename = TCollection_ExtendedString(save_file)
    sstatus = TCollection_ExtendedString()
    sstatus = app.SaveAs(doc, filename)
    print(f"{sstatus=}")
    print(f"{PCDM_SS_OK=}")
    if sstatus == PCDM_SS_OK:
        print(f"Document saved to {save_file}\n")


if __name__ == "__main__":
    # Create new empty top-level assembly
    root_label = ST.NewShape()
    TDataStd_Name.Set(root_label, TCollection_ExtendedString("Chassis"))

    # Create wheel and axle prototypes
    wheel_proto = create_wheel_proto()
    axle_proto = create_axle_proto()

    # Create wheel_axle compound shape & label, store in prototype dataclass
    wheel_axle_comp = build_wheel_axle(wheel_proto.shape, axle_proto.shape, L)
    wheel_axle_proto = Prototype(wheel_axle_comp,
                                 ST.AddShape(wheel_axle_comp, True))

    # Wheel Location Transformations
    wheelT_right = gp_Trsf()
    wheelT_right.SetTranslationPart(gp_Vec(L/2, 0, 0))
    right_whl_loc = TopLoc_Location(wheelT_right)

    wheelT_left = gp_Trsf()
    qn = gp_Quaternion(gp_Vec(gp_DY()), math.pi)
    R = gp_Trsf()
    R.SetRotation(qn)
    wheelT_left = wheelT_right.Inverted() * R
    left_whl_loc = TopLoc_Location(wheelT_left)

    # Add components of wheel_axle_assembly
    cw1_label = ST.AddComponent(wheel_axle_proto.label, wheel_proto.label, right_whl_loc)
    cw2_label = ST.AddComponent(wheel_axle_proto.label, wheel_proto.label, left_whl_loc)
    ca1_label = ST.AddComponent(wheel_axle_proto.label, axle_proto.label, TopLoc_Location())
    TDataStd_Name.Set(cw1_label, TCollection_ExtendedString("wheel-1"))
    TDataStd_Name.Set(cw2_label, TCollection_ExtendedString("wheel-2"))
    TDataStd_Name.Set(ca1_label, TCollection_ExtendedString("axle-1"))

    # Apply color to parts
    CT.SetColor(wheel_proto.label, Quantity_Color(
        1, 0, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen)
    CT.SetColor(axle_proto.label, Quantity_Color(
        0, 1, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen)


    save_file = "/home/doug/Desktop/step/doc_alt.xml"
    save_doc(save_file, doc)

    step_file_name = "/home/doug/Desktop/step/chassis_alt.stp"
    write_step(doc, step_file_name)

