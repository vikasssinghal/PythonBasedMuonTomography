#include "DetectorConstruction.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"

G4VPhysicalVolume* DetectorConstruction::Construct() {
  G4NistManager* nist = G4NistManager::Instance();

  // Materials
  G4Material* air = nist->FindOrBuildMaterial("G4_AIR");
  G4Material* steel = nist->FindOrBuildMaterial("G4_Fe");
  G4Material* tungsten = nist->FindOrBuildMaterial("G4_U");
  G4Material* scint = nist->FindOrBuildMaterial("G4_PLASTIC_SC_VINYLTOLUENE");

  // World
  G4double world_size = 1.5 * m;
  G4Box* solidWorld = new G4Box("World", world_size/2, world_size/2, world_size/2);
  G4LogicalVolume* logicWorld = new G4LogicalVolume(solidWorld, air, "World");
  logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());
  G4VPhysicalVolume* physWorld = new G4PVPlacement(0, G4ThreeVector(), logicWorld, "World", 0, false, 0);

  // --- Container (Hollow) ---
  G4double c_outer_size = 40.0 * cm;
  G4double c_thick = 0.5 * cm;
  G4double c_inner_size = c_outer_size - (2.0 * c_thick); // 39 cm

  // Outer Steel Box
  G4Box* solidContainerOuter = new G4Box("ContainerOuter", c_outer_size/2, c_outer_size/2, c_outer_size/2);
  G4LogicalVolume* logicContainerOuter = new G4LogicalVolume(solidContainerOuter, steel, "ContainerOuter");
  new G4PVPlacement(0, G4ThreeVector(0,0,0), logicContainerOuter, "ContainerOuter", logicWorld, false, 0);
  
  // Set container color (grey)
  G4VisAttributes* containerVis = new G4VisAttributes(G4Colour(0.5, 0.5, 0.5, 0.2));
  logicContainerOuter->SetVisAttributes(containerVis);

  // Inner Air Cavity (placed inside the steel box)
  G4Box* solidContainerInner = new G4Box("ContainerInner", c_inner_size/2, c_inner_size/2, c_inner_size/2);
  G4LogicalVolume* logicContainerInner = new G4LogicalVolume(solidContainerInner, air, "ContainerInner");
  new G4PVPlacement(0, G4ThreeVector(0,0,0), logicContainerInner, "ContainerInner", logicContainerOuter, false, 0);

  // --- Hidden Object ---
  G4double obj_radius = 8.6 * cm;
  G4double obj_height = 24.4 * cm;
  G4Tubs* solidObject = new G4Tubs("HiddenObject", 0, obj_radius, obj_height/2, 0, 360*deg);
  G4LogicalVolume* logicObject = new G4LogicalVolume(solidObject, tungsten, "HiddenObject");
  new G4PVPlacement(0, G4ThreeVector(0,0,0), logicObject, "HiddenObject", logicContainerInner, false, 0);

  // Set hidden object color (green)
  G4VisAttributes* objVis = new G4VisAttributes(G4Colour(0.0, 1.0, 0.0, 1.0));
  logicObject->SetVisAttributes(objVis);

  // --- Detector Planes ---
  G4double plane_size = 100.0 * cm;
  G4double plane_thick = 1.0 * cm;
  G4Box* solidPlane = new G4Box("Plane", plane_size/2, plane_size/2, plane_thick/2);
  G4LogicalVolume* logicPlane = new G4LogicalVolume(solidPlane, scint, "Plane");
  
  G4VisAttributes* planeVis = new G4VisAttributes(G4Colour(1.0, 0.0, 0.0, 0.3));
  logicPlane->SetVisAttributes(planeVis);

  // Upper stack (+25 to +55 cm)
  for (int i = 0; i < 4; i++) {
    G4double z = 25.0*cm + i*10.0*cm;
    new G4PVPlacement(0, G4ThreeVector(0,0,z), logicPlane, "UpperPlane", logicWorld, false, i);
  }
  // Lower stack (-25 to -55 cm)
  for (int i = 0; i < 4; i++) {
    G4double z = -25.0*cm - i*10.0*cm;
    new G4PVPlacement(0, G4ThreeVector(0,0,z), logicPlane, "LowerPlane", logicWorld, false, i+4);
  }

  return physWorld;
}
