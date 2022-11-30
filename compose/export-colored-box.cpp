/*
How to export colored STEP files in OpenCASCADE
https://techoverflow.net/2019/06/14/how-to-export-colored-step-files-in-opencascade/
*/

#include <occutils/ExtendedSTEP.hxx>
#include <occutils/Primitive.hxx>

TopoDS_Shape cube = Primitive::MakeCube(5 /* mm */);

STEP::ExtendedSTEPExporter stepExporter;
stepExporter.AddShapeWithColor(cube, Quantity_NOC_RED);
stepExporter.Write("ColoredCube.step");
stepExporter.AddShape(myShape);
// Get global application
Handle(TDocStd_Application) application = XCAFApp_Application::GetApplication();
// Create document
Handle(TDocStd_Document) document;
application->NewDocument("MDTV-XCAF", document);
// Get shape & color tools
Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(document->Main());
Handle(XCAFDoc_ColorTool) colorTool = XCAFDoc_DocumentTool::ColorTool(document->Main());
// Create shape
// IMPORTANT: DO NOT use shapeTool->AddShape(TopoDS_Shape)!
// This WILL NOT PRESERVE the color!
TDF_Label partLabel = shapeTool->NewShape();
shapeTool->SetShape(partLabel, filletedBody);

//TDF_Label redColor = colorTool->AddColor();
colorTool->SetColor(partLabel, Quantity_NOC_RED, XCAFDoc_ColorGen);

STEPCAFControl_Writer writer;
writer.SetColorMode(true);
writer.Perform(document, "ColoredShape.step");

Quantity_Color red(1.0 /* R */, 0.0 /* G */, 0.0 /* B */, Quantity_TypeOfColor::Quantity_TOC_RGB);
Quantity_Color brownishOrange(1.0 /* H */, 0.5 /* L */, 0.5 /* S */, Quantity_TypeOfColor::Quantity_TOC_HLS);