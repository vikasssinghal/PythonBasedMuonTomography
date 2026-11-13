cmake_minimum_required(VERSION 3.16)
project(MuonTomography)

find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})

add_executable(muon_sim
  main.cc
  src/DetectorConstruction.cc
  src/PrimaryGeneratorAction.cc
  src/ActionInitialization.cc
  src/RunAction.cc
  src/SteppingAction.cc
)

target_include_directories(muon_sim PRIVATE ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(muon_sim ${Geant4_LIBRARIES})
