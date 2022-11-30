/*
Imports a step file and loads it into an XDE document
as a component of root. The document is then saved in
both step format and .xbf format.
*/

// OpenCascade includes
#include <BRep_Builder.hxx>
#include <Interface_Static.hxx>
#include <TopoDS_Compound.hxx>
#include <BinXCAFDrivers.hxx>
#include <TDF_ChildIterator.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <STEPCAFControl_Writer.hxx>
#include <TDataStd_Name.hxx>
#include <TDocStd_Application.hxx>
#include <TDocStd_Document.hxx>
#include <TDocStd_XLinkTool.hxx>
#include <TNaming_Builder.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <XSControl_Writer.hxx>
#include <XSControl_WorkSession.hxx>

const char* filename = "../models/as1-oc-214.stp";
const char* savename = "as1-oc-214.stp";
const char* save_step_file_name = "/home/doug/Desktop/under_top_fixed.stp";
const char* save_doc_file_name = "/home/doug/Desktop/under_top_fixed.xbf";

struct t_DocAppStruct
{
  Handle(TDocStd_Document)    doc;
  Handle(TDocStd_Application) app;
};

struct t_prototype
{
  TopoDS_Shape shape;
  TDF_Label    label;
};

namespace
{
  t_DocAppStruct createDoc()
  {
    // Create XDE document
    Handle(TDocStd_Application) app = new TDocStd_Application;
    BinXCAFDrivers::DefineFormat(app);
    //
    Handle(TDocStd_Document) doc;
    app->NewDocument("BinXCAF", doc);
    //
    // Create a DocAppStruct
    t_DocAppStruct docApp;
    docApp.app = app;
    docApp.doc = doc;

    return docApp;
  }
}

int main(int argc, char** argv)
{
  // Step section:

  STEPCAFControl_Reader Reader;

  // Create XDE document and app for step data
  t_DocAppStruct stepDocApp = ::createDoc();
  Handle(TDocStd_Application) stepApp = stepDocApp.app;
  Handle(TDocStd_Document) stepDoc = stepDocApp.doc;

  // Read CAD and associated data from file
  IFSelect_ReturnStatus outcome = Reader.ReadFile(filename);
  //
  if ( outcome != IFSelect_RetDone )
  {
    stepApp->Close(stepDoc);
  }

  if ( !Reader.Transfer(stepDoc) )
  {
    stepApp->Close(stepDoc);
  }

  // Tools for step doc
  Handle(XCAFDoc_ShapeTool)
    SST = XCAFDoc_DocumentTool::ShapeTool( stepDoc->Main() ); // Shape tool.
  Handle(XCAFDoc_ColorTool)
    SCT = XCAFDoc_DocumentTool::ColorTool( stepDoc->Main() ); // Color tool.

  // Get root label of step data to paste (sourceLabel)
  TDF_LabelSequence stepLabels;
  SST->GetShapes(stepLabels);
  TDF_Label sourceLabel = stepLabels.Value(1);

  // Project section:

  // Create XDE document and app for project data
  t_DocAppStruct projDocApp = ::createDoc();
  Handle(TDocStd_Application) app = projDocApp.app;
  Handle(TDocStd_Document) doc = projDocApp.doc;

  // Tools for project doc
  Handle(XCAFDoc_ShapeTool)
    ST = XCAFDoc_DocumentTool::ShapeTool( doc->Main() ); // Shape tool.
  Handle(XCAFDoc_ColorTool)
    CT = XCAFDoc_DocumentTool::ColorTool( doc->Main() ); // Color tool.

  // Create target shape and label
  TopoDS_Compound targetShape;
  TopoDS_Builder tbuilder;
  tbuilder.MakeCompound(targetShape);
  t_prototype targetProto;
  targetProto.shape = targetShape;
  targetProto.label = ST->AddShape(targetShape, true); // Add assy to the document.

  // Create root prototype.
  TopoDS_Compound rootShape;
  TopoDS_Builder rbuilder;
  rbuilder.MakeCompound(rootShape);
  rbuilder.Add(rootShape, targetProto.shape);
  t_prototype rootProto;
  rootProto.shape = rootShape;
  rootProto.label = ST->AddShape(rootShape, true); // Add assy to the document.
  TDataStd_Name::Set( rootProto.label, TCollection_ExtendedString("Root") );

  // Copy source label of step doc to target label of project doc
  TDocStd_XLinkTool XLinkTool;
  XLinkTool.Copy(targetProto.label, sourceLabel);
  ST->UpdateAssemblies();

  // Set names of target label instance
  for ( TDF_ChildIterator cit(rootProto.label); cit.More(); cit.Next() )
  {
    TDataStd_Name::Set(cit.Value(), savename);
  }

  // Save project doc to step file
  STEPCAFControl_Writer Writer; 
  // To make subshape names work, we have to turn on the following static
  // variable of OpenCascade.
  Interface_Static::SetIVal("write.stepcaf.subshapes.name", 1);
  // Write XDE document to file

  if ( !Writer.Transfer(doc, STEPControl_AsIs) )
  {
    std::cout << "The document cannot be translated or gives no result" << std::endl;
    app->Close(doc);
  }

  const IFSelect_ReturnStatus ret = Writer.Write(save_step_file_name);

  if ( ret != IFSelect_RetDone )
  {
    std::cout << "The document could not be written to file" << std::endl;
    app->Close(doc);
  }
  std::cout << "Document saved in STEP format." << std::endl;

   // Write doc out to file
  PCDM_StoreStatus sstatus = app->SaveAs(doc, save_doc_file_name);
  //
  if ( sstatus != PCDM_SS_OK )
  {
    app->Close(doc);
    std::cout << "Cannot write XCAF document." << std::endl;
    return 1;
  }
  std::cout << "Wrote XCAF document in .xbf format." << std::endl;

  app->Close(doc);
  return 0;
}
