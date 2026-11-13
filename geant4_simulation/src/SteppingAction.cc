#include "SteppingAction.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4EventManager.hh" // Needed for event ID

void SteppingAction::UserSteppingAction(const G4Step* step) {
  G4Track* track = step->GetTrack();
  if (track->GetDefinition()->GetParticleName() != "mu-") return;

  G4VPhysicalVolume* volume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume();
  if (!volume) return;
  
  G4String volName = volume->GetName();
  if (volName == "UpperPlane" || volName == "LowerPlane") {
    auto man = G4AnalysisManager::Instance();
    G4ThreeVector pos = step->GetPreStepPoint()->GetPosition();
    G4double edep = step->GetTotalEnergyDeposit();
    G4double time = step->GetPreStepPoint()->GetGlobalTime();
    
    // Correct way to get event ID
    G4int eventID = G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID();
    
    G4int planeID = step->GetPreStepPoint()->GetTouchableHandle()->GetCopyNumber();
    G4double momentum = track->GetMomentum().mag() / MeV;
    
    man->FillNtupleIColumn(0, eventID);
    man->FillNtupleIColumn(1, planeID);
    man->FillNtupleDColumn(2, pos.x() / mm);
    man->FillNtupleDColumn(3, pos.y() / mm);
    man->FillNtupleDColumn(4, pos.z() / mm);
    man->FillNtupleDColumn(5, edep / MeV);
    man->FillNtupleDColumn(6, time / ns);
    man->FillNtupleDColumn(7, momentum); // FILL MOMENTUM
    man->AddNtupleRow();
  }
}
