/*
Opens a file that has been previously saved in .xbf format.
Subsequently saves it in .stp format, confirming the round trip.
*/

// OpenCascade includes
#include <BRep_Builder.hxx>
#include <Interface_Static.hxx>
#include <TopoDS_Compound.hxx>
#include <BinXCAFDrivers.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <STEPCAFControl_Writer.hxx>
#include <TDataStd_Name.hxx>
#include <TDocStd_Application.hxx>
#include <TDocStd_Document.hxx>
#include <TDocStd_XLinkTool.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <XSControl_Writer.hxx>
#include <XSControl_WorkSession.hxx>

const char* filename = "../models/as1-oc-214.xbf";
const char* save_step_file_name = "/home/doug/Desktop/round_trip.stp";


struct t_DocAppStruct
{
  Handle(TDocStd_Document)    doc;
  Handle(TDocStd_Application) app;
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
  // Create XDE document and app for loading file
  t_DocAppStruct projDocApp = ::createDoc();
  Handle(TDocStd_Application) app = projDocApp.app;
  Handle(TDocStd_Document) doc = projDocApp.doc;

  // Load file (previously saved in .xbf format)
  app->Open(filename, doc);

  // Save doc to step file
  STEPCAFControl_Writer Writer; 
  // To make subshape names work, the following static variable of OpenCascade
  // must be turned on.
  Interface_Static::SetIVal("write.stepcaf.subshapes.name", 1);

  // Write XDE document to file
  if ( !Writer.Transfer(doc, STEPControl_AsIs) )
  {
    std::cout << "The document cannot be translated or gives no result" << std::endl;
    app->Close(doc);
  }
  //
  const IFSelect_ReturnStatus ret = Writer.Write(save_step_file_name);
  //
  if ( ret != IFSelect_RetDone )
  {
    std::cout << "The document could not be written to file" << std::endl;
    app->Close(doc);
  }
  std::cout << "Document saved in STEP format." << std::endl;

  app->Close(doc);
  return 0;
}
