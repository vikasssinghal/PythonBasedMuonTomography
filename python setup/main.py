import sys
import os
import numpy as np
import random
import time

# Ensure workspace root is in path for easy execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MuonTomography.config import Z_PLANES, DEFAULT_NUM_MUONS
from MuonTomography.materials import MATERIALS
from MuonTomography.container import Container, HiddenObject
from MuonTomography.detector import DetectorStack
from MuonTomography.scattering import ScatteringSimulator
from MuonTomography.tracking import TrackReconstructor
from MuonTomography.reconstruction import POCAReconstructor, MaterialClassifier
from MuonTomography.visualization import create_visualization
from MuonTomography.muon_generator import MuonGenerator

class Simulation:
    def __init__(self, num_muons=DEFAULT_NUM_MUONS, hidden_object=None):
        """
        Coordinates the entire Muon Tomography Simulation pipeline.
        """
        self.num_muons = num_muons
        self.container = Container(hidden_object=hidden_object)
        self.detector_stack = DetectorStack()
        self.simulator = ScatteringSimulator(self.container)
        self.track_reconstructor = TrackReconstructor()
        self.poca_reconstructor = POCAReconstructor()
        self.classifier = MaterialClassifier()
        self.muon_generator = MuonGenerator(start_z=85.0)

    def run(self):
        """Runs the simulation and track reconstruction."""
        # 1. Generate Muons
        print(f"Generating {self.num_muons} cosmic muons...")
        muon_data = self.muon_generator.generate_batch(self.num_muons)
        ids = muon_data['ids']
        positions = muon_data['positions']
        directions = muon_data['directions']
        momenta = muon_data['momenta']
        velocities = muon_data['velocities']
        
        # 2. Setup Hit Matrix and arrays to register hits on all 8 planes
        # hit_matrix: shape (num_muons+1, 9) to track active hits on planes 1-8
        hit_matrix = np.zeros((self.num_muons + 1, 9), dtype=bool)
        hits_in_arr = np.zeros((self.num_muons + 1, 4, 3))
        hits_out_arr = np.zeros((self.num_muons + 1, 4, 3))
        
        # 3. Propagate to Upper Stack (Planes 1-4)
        for d in range(1, 5):
            zp = Z_PLANES[d-1]
            t = (zp - positions[:, 2]) / directions[:, 2]
            x_hit = positions[:, 0] + t * directions[:, 0]
            y_hit = positions[:, 1] + t * directions[:, 1]
            
            hits_in_arr[ids, d-1, 0] = x_hit
            hits_in_arr[ids, d-1, 1] = y_hit
            hits_in_arr[ids, d-1, 2] = zp
            
            # Check if hit is in active area (100 cm x 100 cm)
            hit_active = (x_hit >= -50.0) & (x_hit <= 50.0) & (y_hit >= -50.0) & (y_hit <= 50.0)
            hit_matrix[ids, d] = hit_active
            
        # 4. Propagate through the Container (scattering)
        # We start propagation from Plane 4 (last plane of upper stack)
        pos_plane4 = hits_in_arr[ids, 3, :]
        print("Simulating Multiple Coulomb Scattering through container...")
        pos_after, dir_after, scat_records = self.simulator.simulate_scattering(
            pos_plane4, directions, momenta
        )
        
        # 5. Propagate to Lower Stack (Planes 5-8)
        for d in range(5, 9):
            zp = Z_PLANES[d-1]
            t = (zp - pos_after[:, 2]) / dir_after[:, 2]
            x_hit = pos_after[:, 0] + t * dir_after[:, 0]
            y_hit = pos_after[:, 1] + t * dir_after[:, 1]
            
            hits_out_arr[ids, d-5, 0] = x_hit
            hits_out_arr[ids, d-5, 1] = y_hit
            hits_out_arr[ids, d-5, 2] = zp
            
            hit_active = (x_hit >= -50.0) & (x_hit <= 50.0) & (y_hit >= -50.0) & (y_hit <= 50.0)
            hit_matrix[ids, d] = hit_active
            
        # 6. Trigger and select reconstructible muons (must hit all 8 planes)
        reconstructible_ids = ids[np.all(hit_matrix[ids, 1:9], axis=1)]
        num_recon = len(reconstructible_ids)
        print(f"Muons hitting all 8 planes (reconstructible): {num_recon} ({num_recon/self.num_muons*100:.2f}%)")
        
        if num_recon < 100:
            raise ValueError("Too few reconstructible muons! Increase starting batch size or check geometry alignment.")
            
        # Slice coordinate arrays for the reconstructible subset
        hits_in_subset = hits_in_arr[reconstructible_ids]
        hits_out_subset = hits_out_arr[reconstructible_ids]
        momenta_subset = momenta[reconstructible_ids - 1]
        
        # 7. Perform Linear Regression Track Fits
        print("Reconstructing incoming and outgoing tracks...")
        tracking_results = self.track_reconstructor.reconstruct_tracks_vec(hits_in_subset, hits_out_subset)
        tracking_results['momenta'] = momenta_subset
        tracking_results['muon_ids'] = reconstructible_ids
        
        # 8. Reconstruct 3D density map (POCA algorithm)
        print("Reconstructing 3D scattering density map (POCA)...")
        poca_pts, recon_mask = self.poca_reconstructor.reconstruct_density_map(tracking_results)
        
        # 9. Classify Hidden Material
        print("Estimating hidden material properties...")
        classification = self.classifier.classify(tracking_results, self.container)
        
        return {
            'tracking_results': tracking_results,
            'poca_pts': poca_pts,
            'recon_mask': recon_mask,
            'classification': classification,
            'num_reconstructed': num_recon
        }

def print_ascii_histogram(data, bins=10, title="Histogram"):
    """Draws a clean ASCII bar chart in the console."""
    counts, edges = np.histogram(data, bins=bins)
    max_count = np.max(counts) if np.max(counts) > 0 else 1
    max_width = 40
    print(f"\n=================== {title.upper()} ===================")
    for i in range(len(counts)):
        bar = "#" * int(counts[i] / max_count * max_width)
        print(f"[{edges[i]:6.2f} - {edges[i+1]:6.2f}]: {counts[i]:5d} | {bar}")
    print("========================================================\n")

def run_performance_validation(num_runs=10, num_muons=30000):
    """
    Runs multiple independent simulations with different hidden objects
    to evaluate the material classification accuracy.
    """
    print(f"\n========================================================")
    print(f"    RUNNING DETECTOR PERFORMANCE VALIDATION ({num_runs} runs)")
    print(f"========================================================")
    
    correct_count = 0
    t_start = time.time()
    
    for r in range(num_runs):
        # Place random object
        hidden_obj = HiddenObject()
        sim = Simulation(num_muons=num_muons, hidden_object=hidden_obj)
        results = sim.run()
        
        truth = hidden_obj.material_name
        pred = results['classification']['predicted_material']
        conf = results['classification']['confidence']
        
        is_correct = truth == pred
        if is_correct:
            correct_count += 1
            status = "SUCCESS [✓]"
        else:
            status = "FAIL    [✗]"
            
        print(f"Run {r+1:2d} | Truth: {truth:10s} | Pred: {pred:10s} | Conf: {conf*100:5.1f}% | {status}")
        
    t_end = time.time()
    accuracy = correct_count / num_runs * 100.0
    print(f"\nValidation complete in {t_end - t_start:.2f} seconds.")
    print(f"Overall Material Identification Accuracy: {accuracy:.1f}%\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="3D Muon Scattering Tomography Simulator")
    parser.add_argument('--muons', type=int, default=100000, help="Number of muons to simulate")
    parser.add_argument('--runs', type=int, default=5, help="Number of validation runs")
    parser.add_argument('--val-muons', type=int, default=25000, help="Number of muons per validation run")
    args = parser.parse_args()

    # --- Step 1: Detailed High-Statistics Simulation Run ---
    print("========================================================")
    print("      STARTING DETAILED MUON TOMOGRAPHY SIMULATION      ")
    print("========================================================")
    
    # We choose a specific interesting object for the detailed display:
    # A tungsten cylinder centered at the origin
    tungsten_cylinder = HiddenObject(shape_type='cylinder', material_name='Tungsten', center=[0.0, 0.0, 0.0])
    
    sim = Simulation(num_muons=args.muons, hidden_object=tungsten_cylinder)
    results = sim.run()
    
    tracking_results = results['tracking_results']
    poca_pts = results['poca_pts']
    recon_mask = results['recon_mask']
    classification = results['classification']
    
    # --- Step 2: Display Statistical Results ---
    angles_deg = np.degrees(tracking_results['scattering_angles'])
    displacements = tracking_results['displacement']
    
    print("\n========================================================")
    print("                  SIMULATION SUMMARY                    ")
    print("========================================================")
    print(f"Ground Truth Hidden Material: {sim.container.hidden_object.material_name}")
    print(f"Ground Truth Hidden Geometry: {sim.container.hidden_object.get_summary()}")
    print(f"Estimated Material          : {classification['predicted_material']}")
    print(f"Classification Confidence   : {classification['confidence']*100:.2f}%")
    print(f"Average Scattering Angle    : {classification['avg_scattering_angle']:.5f} rad ({np.degrees(classification['avg_scattering_angle']):.3f}°)")
    print(f"Maximum Scattering Angle    : {np.max(tracking_results['scattering_angles']):.5f} rad ({np.degrees(np.max(tracking_results['scattering_angles'])):.3f}°)")
    print(f"Average Centroid Shift      : {classification['avg_centroid_shift']:.3f} cm")
    print(f"Predicted Radiation Length  : {classification['radiation_length']:.2f} cm")
    print(f"Predicted Density           : {classification['density']:.2f} g/cm³")
    print("========================================================")
    
    # Print ASCII Histograms
    print_ascii_histogram(angles_deg, bins=10, title="Scattering Angle Distribution (degrees)")
    print_ascii_histogram(displacements, bins=10, title="Centroid Displacement Distribution (cm)")
    
    # --- Step 3: Create and Save 3D Visualization ---
    print("Generating 3D interactive Plotly visualization...")
    # Only pass POCA points that are valid reconstructions
    poca_recon = poca_pts[recon_mask]
    
    fig = create_visualization(
        detector_stack=sim.detector_stack,
        container=sim.container,
        tracking_results=tracking_results,
        poca_pts=poca_recon,
        density_grid=sim.poca_reconstructor.density_grid,
        num_show_tracks=70,
        recon_mask=recon_mask
    )
    
    html_filename = "muon_tomography_display.html"
    fig.write_html(html_filename)
    print(f"3D Event Display saved successfully to: {os.path.abspath(html_filename)}")
    print("You can open this file in any web browser to rotate, zoom, and inspect the 3D geometry.")
    
    # --- Step 4: Run Performance Validation Loops ---
    run_performance_validation(num_runs=args.runs, num_muons=args.val_muons)

if __name__ == "__main__":
    main()
