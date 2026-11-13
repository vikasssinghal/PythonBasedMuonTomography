#include "PrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <cmath>

PrimaryGeneratorAction::PrimaryGeneratorAction() {
  fParticleGun = new G4ParticleGun(1);
  G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
  fParticleGun->SetParticleDefinition(particleTable->FindParticle("mu-"));
  fParticleGun->SetParticleEnergy(0); // Silence warning
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
  delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent) {
  // Shoot exactly at X=0, Y=0
  fParticleGun->SetParticlePosition(G4ThreeVector(0.0, 0.0, 100.0 * cm));

  G4double momentum = (1.0 + G4UniformRand() * 9.0) * GeV;
  fParticleGun->SetParticleMomentum(momentum);

  // Shoot perfectly straight down (0 degree spread)
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0.0, 0.0, -1.0));

  fParticleGun->GeneratePrimaryVertex(anEvent);
}
