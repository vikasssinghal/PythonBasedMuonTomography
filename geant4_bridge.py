import pandas as pd
import numpy as np

# Import your exact code
from MuonTomography.tracking import TrackReconstructor
from MuonTomography.reconstruction import POCAReconstructor, MaterialClassifier

# --- Mock Container for the Classifier ---
class HiddenObject:
    def __init__(self):
        self.shape_type = 'cylinder'
        self.center = np.array([0.0, 0.0, 0.0])
        self.params = {'radius': 8.6, 'height': 24.4}

class Container:
    def __init__(self):
        self.hidden_object = HiddenObject()

def run_pipeline():
    csv_path = "data/geant4/muon_hits_nt_Hits.csv"
    print(f"Loading {csv_path}...")
    
    try:
        df = pd.read_csv(csv_path, comment='#', names=['event_id', 'plane_id', 'x_mm', 'y_mm', 'z_mm', 'edep_MeV', 'time_ns', 'momentum_MeV'])
    except FileNotFoundError:
        print("Error: Could not find the CSV. Did you run Geant4?")
        return

    # 1. Group by event and plane to ensure 1 hit per plane per muon
    df_clean = df.groupby(['event_id', 'plane_id']).first().reset_index()
    
    # 2. Filter events that hit all 8 planes
    hits_per_event = df_clean.groupby('event_id')['plane_id'].count()
    good_events = hits_per_event[hits_per_event == 8].index
    
    df_good = df_clean[df_clean['event_id'].isin(good_events)].sort_values(['event_id', 'plane_id']).reset_index(drop=True)
    
    if len(good_events) == 0:
        print("No muons hit all 8 planes! Run Geant4 with more muons.")
        return
        
    print(f"Found {len(good_events)} reconstructible muons out of {df['event_id'].nunique()} total.")

    # 3. Extract coordinates and convert to (N, 4, 3) arrays
    N = len(good_events)
    coords = df_good[['x_mm', 'y_mm', 'z_mm']].values / 10.0
    
    all_hits = coords.reshape((N, 8, 3))
    hits_in = all_hits[:, 0:4, :]
    hits_out = all_hits[:, 4:8, :]

    # 4. Run Track Reconstruction
    print("\nReconstructing tracks...")
    tracker = TrackReconstructor()
    tracking_results = tracker.reconstruct_tracks_vec(hits_in, hits_out)
    
    # Extract real momentum from the first plane (Plane 0) for each event
    momenta = df_good['momentum_MeV'].values[0::8]
    tracking_results['momenta'] = momenta 
    
    print(f"DEBUG: Mean angle in tracking_results: {np.mean(tracking_results['scattering_angles']):.4f} rad")

    # 5. Run POCA Reconstruction
    print("Running POCA 3D Reconstruction...")
    poca = POCAReconstructor()
    poca_pts, mask = poca.reconstruct_density_map(tracking_results, angle_threshold_deg=0.0)
    
    print(f"Voxel grid shape: {poca.density_grid.shape}")
    print(f"Non-zero voxels: {np.count_nonzero(poca.density_grid)}")

    # 6. Run Material Classification
    print("\nClassifying Material...")
    container = Container()
    classifier = MaterialClassifier()
    results = classifier.classify(tracking_results, container)
    
    print("\n--- RESULTS ---")
    print(f"Predicted Material: {results['predicted_material']}")
    print(f"Confidence: {results['confidence']*100:.2f}%")
    print(f"Avg Scattering Angle: {results['avg_scattering_angle']:.4f} rad")

if __name__ == "__main__":
    run_pipeline()
