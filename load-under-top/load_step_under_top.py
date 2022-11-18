from dataclasses import dataclass
import logging
import os
import os.path

from OCC.Core.BinXCAFDrivers import binxcafdrivers_DefineFormat
from OCC.Core.XmlXCAFDrivers import xmlxcafdrivers_DefineFormat
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.PCDM import PCDM_SS_OK, PCDM_RS_OK
from OCC.Core.STEPCAFControl import (STEPCAFControl_Reader,
                                     STEPCAFControl_Writer)
from OCC.Core.STEPControl import STEPControl_AsIs
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.TDF import TDF_Label, TDF_LabelSequence
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
    # Choose format for TDocStd_Document
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


def set_label_name(label, name):
    TDataStd_Name.Set(label, TCollection_ExtendedString(name))


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


def save_doc(doc, app, fname):
    """Save doc to file in XML Format (.xml)"""

    # One of the few places app is needed
    save_status = app.SaveAs(doc, TCollection_ExtendedString(fname))
    if save_status == PCDM_SS_OK:
        print(f"File {fname} saved successfully.")
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

    # Create Top assembly shape & label
    shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
    root_comp = TopoDS_Compound()
    root_builder = TopoDS_Builder()
    root_builder.MakeCompound(root_comp)
    root_proto = Prototype(
        root_comp, shape_tool.AddShape(root_comp, True))
    set_label_name(root_proto.label, "Top")

    # Read a step file
    file_name = "../step/as1-oc-214.stp"
    f_name, step_doc, step_app = _load_step(file_name)
    print(f"Opened {f_name}")

    # Add a compound shape as a component under Top
    comp = TopoDS_Compound()
    builder = TopoDS_Builder()
    builder.MakeCompound(comp)
    root_label = root_proto.label
    c_label = shape_tool.AddComponent(root_label, comp, True)
    TDataStd_Name.Set(c_label, TCollection_ExtendedString(f_name))

    # Adding the compound shape as a component of root creates a
    # 'sibling' label at root level holding the new prototype shape.
    # This label will be the target for pasting the step root label.
    ref_label = TDF_Label()  # label of referred shape
    __ = shape_tool.GetReferredShape(c_label, ref_label)
    target_label = ref_label

    # Get root label of step data to paste (source label)
    step_labels = TDF_LabelSequence()
    step_shape_tool = XCAFDoc_DocumentTool_ShapeTool(step_doc.Main())
    step_shape_tool.GetShapes(step_labels)
    source_label = step_labels.Value(1)

    # Copy source label to target label
    copy_label(source_label, target_label)
    shape_tool.UpdateAssemblies()

    # Save composite step file
    save_file_name = "/home/doug/Desktop/step/under-top.stp"
    save_step_doc(doc, save_file_name)

    # Save composite xml file
    save_file_name = "/home/doug/Desktop/step/under-top.xml"
    save_doc(doc, app, save_file_name)

