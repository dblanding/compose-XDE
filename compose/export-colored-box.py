"""
Started as a Python version of:
How to export colored STEP file in OpenCASCADE
https://techoverflow.net/2019/06/14/how-to-export-colored-step-files-in-opencascade/

Now it's a playground for exploring
"""

from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.XmlXCAFDrivers import xmlxcafdrivers_DefineFormat
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.PCDM import PCDM_SS_OK
from OCC.Core.STEPCAFControl import (
    STEPCAFControl_Reader,
    STEPCAFControl_Writer,
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.STEPControl import STEPControl_AsIs
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence, TDF_ChildIterator
from OCC.Core.TDocStd import TDocStd_Document, TDocStd_XLinkTool
from OCC.Core.TopAbs import TopAbs_EDGE
from OCC.Core.TopoDS import topods, TopoDS_Edge, TopoDS_Compound
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.XCAFApp import XCAFApp_Application_GetApplication
from OCC.Core.XCAFDoc import (
    XCAFDoc_DocumentTool_ShapeTool,
    XCAFDoc_DocumentTool_ColorTool,
    XCAFDoc_ColorGen,
)
from OCC.Core.XSControl import XSControl_WorkSession


def create_doc():
    """Create and return XCAF doc and app

    entry       label <class 'OCC.Core.TDF.TDF_Label'>
    0:1         doc.Main()                          (Depth = 1)
    0:1:1       shape_tool is at this label entry   (Depth = 2)
    0:1:2       color_tool at this entry            (Depth = 2)
    0:1:1:1     root_label and all referred shapes  (Depth = 3)
    0:1:1:x:x   component labels (references)       (Depth = 4)
    """

    doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))
    app = XCAFApp_Application_GetApplication()
    app.NewDocument(TCollection_ExtendedString("XmlXCAF"), doc)
    binxcafdrivers_DefineFormat(app)
    xmlxcafdrivers_DefineFormat(app)
    return doc, app


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


def save_doc(save_file, doc):
    """Save the document"""
    filename = TCollection_ExtendedString(save_file)
    sstatus = app.SaveAs(doc, filename)
    print(f"{sstatus=}")
    print(f"{PCDM_SS_OK=}")
    if sstatus == PCDM_SS_OK:
        print(f"Document saved to {save_file}\n")


if __name__ == "__main__":

    # Create document
    doc, app = create_doc()
    shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
    color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())

    # Create root shape and label
    root_label = shape_tool.NewShape()
    root_shape = shape_tool.GetShape(root_label)
    TDataStd_Name.Set(root_label, TCollection_ExtendedString("Root"))
    # Create cube_shape
    S = 5.0
    box = BRepPrimAPI_MakeBox(S, S, S)

    # Add fillets to all edges
    mkFillet = BRepFilletAPI_MakeFillet(box.Shape())
    anEdgeExplorer = TopExp_Explorer(box.Shape(), TopAbs_EDGE)
    while anEdgeExplorer.More():
        anEdge = topods.Edge(anEdgeExplorer.Current())
        mkFillet.Add(S / 12.0, anEdge)
        anEdgeExplorer.Next()
    cube_shape = mkFillet.Shape()

    # Add finished cube_shape to doc
    builder = BRep_Builder()
    builder.MakeCompound(root_shape)
    builder.Add(root_shape, cube_shape)
    shape_tool.AddShape(cube_shape, False)
    cube_label = TDF_Label()
    if shape_tool.FindShape(cube_shape, cube_label):
        print("Found cube_label")

    # Set name and color
    TDataStd_Name.Set(cube_label, TCollection_ExtendedString("cube_shape"))
    color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
    color_tool.SetColor(cube_label, color, XCAFDoc_ColorGen)

    save_step_file_name = "/home/doug/Desktop/step/redbox.stp"
    save_step_doc(doc, save_step_file_name)

    save_file = "/home/doug/Desktop/step/redbox.xml"
    save_doc(save_file, doc)
