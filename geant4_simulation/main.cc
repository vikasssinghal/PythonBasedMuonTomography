#include "G4RunManager.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"
#include "G4PhysListFactory.hh"
#include "DetectorConstruction.hh"
#include "PrimaryGeneratorAction.hh"
#include "ActionInitialization.hh"
#include <cstdlib>

int main(int argc, char** argv) {
  G4UIExecutive* ui = nullptr;
  if (argc == 1) ui = new G4UIExecutive(argc, argv);

  G4RunManager* runManager = new G4RunManager();
  runManager->SetUserInitialization(new DetectorConstruction());
  
  G4PhysListFactory physListFactory;
  runManager->SetUserInitialization(physListFactory.GetReferencePhysList("QGSP_BERT_EMZ"));
  runManager->SetUserInitialization(new ActionInitialization());

  G4VisManager* visManager = nullptr;
  if (ui) {
    visManager = new G4VisExecutive();
    visManager->Initialize();
  }

  G4UImanager* UImanager = G4UImanager::GetUIpointer();

  if (ui) {
    UImanager->ApplyCommand("/control/execute init_vis.mac");
    ui->SessionStart();
    delete ui;
  } else {
    G4String command = "/control/execute ";
    UImanager->ApplyCommand(command + argv[1]);
  }

  // Force exit to avoid Geant4 11.x double-free segfault on cleanup
  std::exit(0); 
}
