import numpy as np
from MuonTomography.config import Z_PLANES

class Track:
    def __init__(self, direction, centroid, slope_x, intercept_x, slope_y, intercept_y, chi2=0.0):
        """
        Represents a reconstructed track segment.
        
        Args:
            direction (np.ndarray): (3,) normalized direction vector
            centroid (np.ndarray): (3,) centroid of hits
            slope_x (float): Slope of X(z)
            intercept_x (float): Intercept of X(z)
            slope_y (float): Slope of Y(z)
            intercept_y (float): Intercept of Y(z)
            chi2 (float): Fit quality parameter
        """
        self.direction = direction
        self.centroid = centroid
        self.slope_x = slope_x
        self.intercept_x = intercept_x
        self.slope_y = slope_y
        self.intercept_y = intercept_y
        self.chi2 = chi2
        
    def evaluate_at_z(self, z):
        """Evaluate (x, y) coordinates of the track at a given Z position."""
        x = self.slope_x * z + self.intercept_x
        y = self.slope_y * z + self.intercept_y
        return np.array([x, y, z])

class TrackReconstructor:
    def __init__(self):
        pass

    def fit_line_least_squares(self, Z, coordinates):
        """
        Fits a 1D line coordinate = slope * Z + intercept using least-squares.
        
        Args:
            Z (np.ndarray): (M,) or (N, M) Z-coordinates
            coordinates (np.ndarray): (N, M) X or Y coordinates of hits
            
        Returns:
            slopes (np.ndarray): (N,) slope values
            intercepts (np.ndarray): (N,) intercept values
        """
        N, M = coordinates.shape
        
        if Z.ndim == 1:
            # All tracks have the same Z coordinates
            mean_z = np.mean(Z)
            z_diff = Z - mean_z
            sum_z_diff_sq = np.sum(z_diff**2)
            
            mean_coord = np.mean(coordinates, axis=1) # (N,)
            coord_diff = coordinates - mean_coord[:, None] # (N, M)
            
            slopes = np.sum(coord_diff * z_diff, axis=1) / sum_z_diff_sq
            intercepts = mean_coord - slopes * mean_z
        else:
            # Tracks have different Z coordinates
            mean_z = np.mean(Z, axis=1) # (N,)
            z_diff = Z - mean_z[:, None] # (N, M)
            sum_z_diff_sq = np.sum(z_diff**2, axis=1) # (N,)
            
            mean_coord = np.mean(coordinates, axis=1) # (N,)
            coord_diff = coordinates - mean_coord[:, None] # (N, M)
            
            slopes = np.sum(coord_diff * z_diff, axis=1) / np.where(sum_z_diff_sq > 1e-9, sum_z_diff_sq, 1.0)
            intercepts = mean_coord - slopes * mean_z
            
        return slopes, intercepts

    def reconstruct_tracks_vec(self, hits_in, hits_out):
        """
        Vectorized track reconstruction for incoming and outgoing stacks.
        
        Args:
            hits_in (np.ndarray): (N, 4, 3) incoming hit coordinates (x, y, z) on Planes 1-4
            hits_out (np.ndarray): (N, 4, 3) outgoing hit coordinates (x, y, z) on Planes 5-8
            
        Returns:
            dict: Reconstructed tracking variables
        """
        N = hits_in.shape[0]
        
        # 1. Incoming fits (Planes 1-4)
        z_in = hits_in[:, :, 2] # (N, 4)
        x_in = hits_in[:, :, 0] # (N, 4)
        y_in = hits_in[:, :, 1] # (N, 4)
        
        slope_x_in, intercept_x_in = self.fit_line_least_squares(z_in, x_in)
        slope_y_in, intercept_y_in = self.fit_line_least_squares(z_in, y_in)
        
        # Normalised incoming direction unit vector (downward travelling)
        # line direction: (-slope_x, -slope_y, -1)
        dir_in = np.stack([-slope_x_in, -slope_y_in, -np.ones(N)], axis=1)
        dir_in_norm = np.linalg.norm(dir_in, axis=1)
        dir_in = dir_in / dir_in_norm[:, None]
        
        centroid_in = np.stack([np.mean(x_in, axis=1), np.mean(y_in, axis=1), np.mean(z_in, axis=1)], axis=1)
        
        # 2. Outgoing fits (Planes 5-8)
        z_out = hits_out[:, :, 2] # (N, 4)
        x_out = hits_out[:, :, 0] # (N, 4)
        y_out = hits_out[:, :, 1] # (N, 4)
        
        slope_x_out, intercept_x_out = self.fit_line_least_squares(z_out, x_out)
        slope_y_out, intercept_y_out = self.fit_line_least_squares(z_out, y_out)
        
        dir_out = np.stack([-slope_x_out, -slope_y_out, -np.ones(N)], axis=1)
        dir_out_norm = np.linalg.norm(dir_out, axis=1)
        dir_out = dir_out / dir_out_norm[:, None]
        
        centroid_out = np.stack([np.mean(x_out, axis=1), np.mean(y_out, axis=1), np.mean(z_out, axis=1)], axis=1)
        
        # 3. Calculate scattering angles (between incoming and outgoing tracks)
        dot_products = np.sum(dir_in * dir_out, axis=1)
        dot_products = np.clip(dot_products, -1.0, 1.0)
        scattering_angles = np.arccos(dot_products) # in radians
        
        # 4. Centroid displacement on Plane 5 (Z_PLANES[4] = -30.0 cm)
        z_p5 = Z_PLANES[4]
        x_predicted = slope_x_in * z_p5 + intercept_x_in
        y_predicted = slope_y_in * z_p5 + intercept_y_in
        
        # Measured hit position is the hit coordinate on Plane 5 (which is the first index in hits_out)
        x_measured = hits_out[:, 0, 0]
        y_measured = hits_out[:, 0, 1]
        
        dx = x_measured - x_predicted
        dy = y_measured - y_predicted
        displacement = np.sqrt(dx**2 + dy**2)
        
        # Calculate fit residuals for quality assessment
        # e.g., standard deviation of hits relative to the fit
        res_x_in = x_in - (slope_x_in[:, None] * z_in + intercept_x_in[:, None])
        res_y_in = y_in - (slope_y_in[:, None] * z_in + intercept_y_in[:, None])
        residual_error = np.sqrt(np.mean(res_x_in**2 + res_y_in**2, axis=1))
        
        return {
            'slope_x_in': slope_x_in,
            'intercept_x_in': intercept_x_in,
            'slope_y_in': slope_y_in,
            'intercept_y_in': intercept_y_in,
            'dir_in': dir_in,
            'centroid_in': centroid_in,
            
            'slope_x_out': slope_x_out,
            'intercept_x_out': intercept_x_out,
            'slope_y_out': slope_y_out,
            'intercept_y_out': intercept_y_out,
            'dir_out': dir_out,
            'centroid_out': centroid_out,
            
            'scattering_angles': scattering_angles,
            'dx': dx,
            'dy': dy,
            'displacement': displacement,
            'residual_error': residual_error
        }
