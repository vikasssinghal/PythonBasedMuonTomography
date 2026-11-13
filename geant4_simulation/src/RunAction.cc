#include "RunAction.hh"
#include "G4AnalysisManager.hh"

RunAction::RunAction() {
  auto man = G4AnalysisManager::Instance();
  man->SetDefaultFileType("csv");
  man->SetFileName("/mnt/c/Users/himan/OneDrive/MuonTomography/PythonBasedMuonTomography/data/geant4/muon_hits");
  
  man->CreateNtuple("Hits", "Muon Hits");
  man->CreateNtupleIColumn("event_id");
  man->CreateNtupleIColumn("plane_id");
  man->CreateNtupleDColumn("x_mm");
  man->CreateNtupleDColumn("y_mm");
  man->CreateNtupleDColumn("z_mm");
  man->CreateNtupleDColumn("edep_MeV");
  man->CreateNtupleDColumn("time_ns");
  man->CreateNtupleDColumn("momentum_MeV"); // ADDED MOMENTUM
  man->FinishNtuple();
}

RunAction::~RunAction() {}

void RunAction::BeginOfRunAction(const G4Run*) {
  G4AnalysisManager::Instance()->OpenFile();
}

void RunAction::EndOfRunAction(const G4Run*) {
  G4AnalysisManager::Instance()->Write();
  G4AnalysisManager::Instance()->CloseFile();
}
