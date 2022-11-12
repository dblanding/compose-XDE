#!/usr/bin/env python

"""
compose-_plus_root.py
copyright 2022 Doug Blanding (dblanding@gmail.com)
Same as compose-XDE.py except with the addition of a top level root.
Converted to PythonOCC from the original C++ (OCCT) presented in the video tutorial:
Lesson 15: Export OpenCascade assemblies to STEP with names and colors at:
https://www.youtube.com/watch?v=dq2-evewPeA&list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ&index=7
This video is one in a series of Open Cascade Lessons at Quaoar's Workshop:
https://www.youtube.com/playlist?list=PL_WFkJrQIY2iVVchOPhl77xl432jeNYfQ
"""

from dataclasses import dataclass
import math
import os
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
from OCC.Core.TDF import TDF_Label, TDF_ChildIterator
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
W  = 100   # Wheel width
D  = 50    # Axle diameter
L  = 1000  # Axle length
CL = 1000  # Chassis length

# Initialize the document
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
ST = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
CT = XCAFDoc_DocumentTool_ColorTool(doc.Main())


# Define dataclass (Python equivalent of a C struct)
# Initialize: foo_proto = prototype(shape, label)
# Retrieve: foo_proto.shape  or  foo_proto.label
@dataclass
class prototype:
    """A shape and its associated label"""
    shape: TopoDS_Shape
    label: TDF_Label


@dataclass
class face_prototype:
    """A face and its associated label"""
    face: TopoDS_Face
    label: TDF_Label


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


def build_chassis(wheel_axle, CL):
    """Build and return a compound chassis shape from wheel_axle (x2)."""
    comp = TopoDS_Compound()
    bbuilder = TopoDS_Builder()
    bbuilder.MakeCompound(comp)

    # Location Transformations
    frontT = gp_Trsf()
    frontT.SetTranslationPart(gp_Vec(0, CL/2, 0))
    front_loc = TopLoc_Location(frontT)

    rearT = gp_Trsf()
    rearT.SetTranslationPart(gp_Vec(0, -CL/2, 0))
    rear_loc = TopLoc_Location(rearT)

    # Copy shapes (moved by location vector), add to compound
    bbuilder.Add(comp, wheel_axle.Moved(front_loc))
    bbuilder.Add(comp, wheel_axle.Moved(rear_loc))

    return comp

def create_chassis_doc():

    # Create wheel shape & label, store in prototype dataclass
    wheel_origin = gp_Ax2( gp_Pnt(-W/2, 0, 0), gp_Dir(1.0, 0.0, 0.0))
    wheel = BRepPrimAPI_MakeCylinder(wheel_origin, OD/2, W).Shape()
    wheel_proto = prototype(wheel,
                            ST.AddShape(wheel, False))

    # Create axle shape & label, store in prototype dataclass
    axle_origin = gp_Ax2( gp_Pnt(-L/2, 0, 0), gp_Dir(1.0, 0.0, 0.0))
    axle = BRepPrimAPI_MakeCylinder(axle_origin, D/2, L).Shape()
    axle_proto = prototype(axle,
                           ST.AddShape(axle, False))

    # Create wheel_axle compound shape & label, store in prototype dataclass
    wheel_axle_comp = build_wheel_axle(wheel, axle, L)
    wheel_axle_proto = prototype(wheel_axle_comp,
                                 ST.AddShape(wheel_axle_comp, True))

    # Create chassis compound shape & label, store in prototype dataclass
    chassis_comp = build_chassis(wheel_axle_proto.shape, CL)
    chassis_proto = prototype(chassis_comp,
                              ST.AddShape(chassis_comp, True))

    # Create root label
    root_comp = TopoDS_Compound()
    bbuilder = TopoDS_Builder()
    bbuilder.MakeCompound(root_comp)
    bbuilder.Add(root_comp, chassis_proto.shape)
    root_proto = prototype(root_comp,
                           ST.AddShape(root_comp, True))
    TDataStd_Name.Set(root_proto.label, TCollection_ExtendedString("root"))



    # Assign names to each of the labels contained in prototypes
    TDataStd_Name.Set(wheel_proto.label, TCollection_ExtendedString("wheel"))
    TDataStd_Name.Set(axle_proto.label, TCollection_ExtendedString("axle"))
    TDataStd_Name.Set(wheel_axle_proto.label, TCollection_ExtendedString("wheel-axle"))
    TDataStd_Name.Set(chassis_proto.label, TCollection_ExtendedString("chassis"))

    # Assign name to chassis instance
    itr = TDF_ChildIterator(root_proto.label, False)
    while itr.More():
        component_label = itr.Value()
        TDataStd_Name.Set(component_label,
                          TCollection_ExtendedString("Chassis-1"))
        itr.Next()


    # Assign names to the instances of wheel-axle (labels not directly accessible)
    itr = TDF_ChildIterator(chassis_proto.label, False)
    counter = 1
    while itr.More():
        component_label = itr.Value()
        TDataStd_Name.Set(component_label,
                          TCollection_ExtendedString(f"wheel-axle-{counter}"))
        counter += 1
        itr.Next()

    # Assign names to the instances of wheel and axle (labels not directly accessible)
    itr = TDF_ChildIterator(wheel_axle_proto.label, False)
    counter = 1
    while itr.More():
        component_label = itr.Value()
        if counter < 3:
            name = f'wheel-{counter}'
            counter += 1
        else:
            name = 'axle-1'
        TDataStd_Name.Set(component_label,
                          TCollection_ExtendedString(name))
        itr.Next()

    # Apply color to parts
    CT.SetColor(wheel_proto.label, Quantity_Color(1, 0, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen)
    CT.SetColor(axle_proto.label, Quantity_Color(0, 1, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen)

    # find the front face of the wheel
    all_wheel_faces = TopTools_IndexedMapOfShape()
    topexp_MapShapes(wheel_proto.shape, TopAbs_FACE, all_wheel_faces)
    front_face = topods_Face(all_wheel_faces(2))

    # create the dataclass object for holding the face and label
    wheel_face_proto = face_prototype(front_face, ST.AddSubShape(wheel_proto.label, front_face))

    # Apply color to front face (of wheel)
    CT.SetColor(wheel_face_proto.label, Quantity_Color(0, 0, 1, Quantity_TOC_RGB), XCAFDoc_ColorSurf)

    # print(f"{wheel_proto.shape = }")  # wheel_proto.shape = <class 'TopoDS_Solid'>

    return chassis_proto, doc

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
    from OCC.Display.SimpleGui import init_display

    # Create chassis and associated document
    chassis_proto, doc = create_chassis_doc()

    # Depending on
    save_file = "/home/doug/Desktop/doc.xml"
    save_doc(save_file, doc)

    step_file_name = "/home/doug/Desktop/chassis.step"
    write_step(doc, step_file_name)

    # Display results
    display, start_display, add_menu, add_function_to_menu = init_display()

    display.DisplayShape(chassis_proto.shape, update=True)
    start_display()
