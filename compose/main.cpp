#include <iostream>


// OpenCascade includes
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BinXCAFDrivers.hxx>
#include <gp_Quaternion.hxx>
#include <Interface_Static.hxx>
#include <Quantity_Color.hxx>
#include <STEPCAFControl_Writer.hxx>
#include <TDF_ChildIterator.hxx>
#include <TDataStd_Name.hxx>
#include <TDocStd_Application.hxx>
#include <TDocStd_Document.hxx>
#include <TopExp.hxx>
#include <TopoDS.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>

//-----------------------------------------------------------------------------

namespace
{
  bool WriteStepWithMeta(const Handle(TDocStd_Document)& doc,
                         const char*                     filename)
  {
    STEPCAFControl_Writer Writer;

    // To make subshape names work, we have to turn on the following static
    // variable of OpenCascade.
    Interface_Static::SetIVal("write.stepcaf.subshapes.name", 1);

    // Write XDE document to file.
    try
    {
      if ( !Writer.Transfer(doc, STEPControl_AsIs) )
      {
        return false;
      }

      const IFSelect_ReturnStatus ret = Writer.Write(filename);

      if ( ret != IFSelect_RetDone )
      {
        return false;
      }
    }
    catch ( ... )
    {
      return false;
    }

    return true;
  }

  namespace ShapeReflection
  {
    //! This function builds a cylindrical primitive representing a simplified
    //! shape of an abstract wheel, including its rim and a tire fused to each
    //! other. The primitive is constructed in the local reference frame, which
    //! would be coincident with the global origin if rendered without any extra
    //! placement transformation. The assumed axle is collinear with the OX axis.
    //!
    //! \param[in] OD the overall diameter of a wheel.
    //! \param[in] W  the tire width.
    TopoDS_Shape CreateWheel(const double OD,
                             const double W)
    {
      return BRepPrimAPI_MakeCylinder(gp_Ax2( gp_Pnt(-W/2, 0., 0.), gp::DX() ), OD/2, W);
    }

    //! This function builds a geometric primitive for an axle.
    //!
    //! \param[in] D the diameter of an axle.
    //! \param[in] L the axle length.
    TopoDS_Shape CreateAxle(const double D,
                            const double L)
    {
      return BRepPrimAPI_MakeCylinder(gp_Ax2( gp_Pnt(-L/2, 0., 0.), gp::DX() ), D/2, L);
    }

    //! Creates a wheel-axle subassembly shape.
    TopoDS_Shape CreateWheelAxle(const TopoDS_Shape& wheel,
                                 const TopoDS_Shape& axle,
                                 const double        L)
    {
      TopoDS_Compound compShape;
      BRep_Builder bbuilder;
      bbuilder.MakeCompound(compShape);

      gp_Trsf wright_T;
      wright_T.SetTranslationPart( gp_Vec(L/2, 0, 0) );

      gp_Quaternion qn(gp::DY(), M_PI);
      gp_Trsf wleft_TR;
      wleft_TR.SetRotation(qn);
      //
      gp_Trsf wleft_T = wright_T.Inverted() * wleft_TR;

      bbuilder.Add( compShape, wheel.Moved(wleft_T) );
      bbuilder.Add( compShape, wheel.Moved(wright_T) );
      bbuilder.Add( compShape, axle ); // Without transformation.

      return compShape;
    }

    TopoDS_Shape CreateChassis(const TopoDS_Shape& wheelAxle,
                               const double        CL)
    {
      TopoDS_Compound compShape;
      BRep_Builder bbuilder;
      bbuilder.MakeCompound(compShape);

      gp_Trsf wfront_T; wfront_T .SetTranslationPart( gp_Vec(0,  CL/2, 0) );
      gp_Trsf wrear_T;  wrear_T  .SetTranslationPart( gp_Vec(0, -CL/2, 0) );

      bbuilder.Add( compShape, wheelAxle.Moved(wfront_T) );
      bbuilder.Add( compShape, wheelAxle.Moved(wrear_T) );

      return compShape;
    }
  }
}

//-----------------------------------------------------------------------------

struct t_prototype
{
  TopoDS_Shape shape;
  TDF_Label    label;
};

struct t_wheelPrototype : public t_prototype
{
  TopoDS_Face frontFace;
  TDF_Label   frontFaceLabel;
};

int main(int argc, char** argv)
{
  // Create XDE document.
  Handle(TDocStd_Application) app = new TDocStd_Application;
  BinXCAFDrivers::DefineFormat(app);
  //
  Handle(TDocStd_Document) doc;
  app->NewDocument("BinXCAF", doc);

  // Tools.
  Handle(XCAFDoc_ShapeTool)
    ST = XCAFDoc_DocumentTool::ShapeTool( doc->Main() ); // Shape tool.
  Handle(XCAFDoc_ColorTool)
    CT = XCAFDoc_DocumentTool::ColorTool( doc->Main() ); // Color tool.

  /* ===========================
   *  Prepare assembly document.
   * =========================== */

  // Parameters.
  const double OD = 500;
  const double W  = 100;
  const double L  = 1000;
  const double CL = 1000;

  // Create one wheel prototype.
  t_wheelPrototype wheelPrototype;
  wheelPrototype.shape = ::ShapeReflection::CreateWheel(OD, W);
  wheelPrototype.label = ST->AddShape(wheelPrototype.shape, false); // Add to the XDE document.

  // Create one axle prototype.
  t_prototype axlePrototype;
  axlePrototype.shape = ::ShapeReflection::CreateAxle(OD/10, L);
  axlePrototype.label = ST->AddShape(axlePrototype.shape, false); // Add to the XDE document.

  // Create one wheel-axle subassembly. Notice that shapes are not duplicated.
  // By this moment, the output STEP file would contain only two MANIFOLD_SOLID_BREP
  // entities.
  t_prototype wheelAxlePrototype;
  wheelAxlePrototype.shape = ::ShapeReflection::CreateWheelAxle(wheelPrototype.shape, axlePrototype.shape, L);
  wheelAxlePrototype.label = ST->AddShape(wheelAxlePrototype.shape, true); // Add to the XDE document.

  /* Main assembly.
     The STEP file would still contain just a couple on entities.

     In Analysis Situs:
     > asm-xde-load -model M -filename C:/Users/serge/Desktop/test.step
     > asm-xde-browse -model M
  */
  t_prototype chassisPrototype;
  chassisPrototype.shape = ::ShapeReflection::CreateChassis(wheelAxlePrototype.shape, CL);
  chassisPrototype.label = ST->AddShape(chassisPrototype.shape, true); // Add to the XDE document.

  // Assign colors to parts.
  CT->SetColor( wheelPrototype.label, Quantity_Color(1, 0, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen );
  CT->SetColor( axlePrototype.label,  Quantity_Color(0, 1, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen );

  // Set names of prototypes.
  TDataStd_Name::Set(wheelPrototype.label,     "wheel");
  TDataStd_Name::Set(axlePrototype.label,      "axle");
  TDataStd_Name::Set(wheelAxlePrototype.label, "wheel-axle");
  TDataStd_Name::Set(chassisPrototype.label,   "chassis");

  // Set names of subassembly instances.
  for ( TDF_ChildIterator cit(chassisPrototype.label); cit.More(); cit.Next() )
  {
    TDataStd_Name::Set(cit.Value(), "wheel-axle-ref");
  }

  // Explode wheel shape by faces.
  TopTools_IndexedMapOfShape wheelFaces;
  TopExp::MapShapes(wheelPrototype.shape, TopAbs_FACE, wheelFaces);
  //
  wheelPrototype.frontFace      = TopoDS::Face( wheelFaces(2) );
  wheelPrototype.frontFaceLabel = ST->AddSubShape(wheelPrototype.label, wheelPrototype.frontFace);

  CT->SetColor( wheelPrototype.frontFaceLabel, Quantity_Color(0, 0, 1, Quantity_TOC_RGB), XCAFDoc_ColorSurf );

  // Set name for a subshape.
  TDataStd_Name::Set(wheelPrototype.frontFaceLabel, "front-face");

  /* ==========
   *  Finalize.
   * ========== */


  // Save to file.
  if ( argc > 1 )
  {
    if ( !::WriteStepWithMeta(doc, argv[1]) )
    {
      std::cout << "Failed to write XDE document to a STEP file " << argv[1] << std::endl;
      return 1;
    }
  }

  /* Save for debugging. Make sure to use the same version of OpenCascade
     when loading the stored document back into memory. E.g., if an older
     version of OpenCascade is used, you're likely to end up having
     the `PCDM_RS_NoVersion` error on reading.

     In DRAWEXE:

     > pload ALL
     > Open C:/users/serge/Desktop/test.xbf D
     > DFBrowse D

   */
  PCDM_StoreStatus sstatus = app->SaveAs(doc, "/home/doug/Desktop/test.xbf");
  //
  if ( sstatus != PCDM_SS_OK )
  {
    app->Close(doc);

    std::cout << "Cannot write OCAF document." << std::endl;
    return 1;
  }

  app->Close(doc); // Close the document upon exiting the message loop.
  return 0;
}
