import numpy as np
from MuonTomography.config import ACTIVE_AREA_SIZE, MUON_MIN_MOMENTUM, MUON_MAX_MOMENTUM, MUON_ANGULAR_SPREAD

class Muon:
    def __init__(self, muon_id, start_pos, direction, momentum):
        """
        Represents a single cosmic-ray muon.
        
        Args:
            muon_id (int): Unique ID of the muon
            start_pos (np.ndarray): (3,) starting position vector (cm)
            direction (np.ndarray): (3,) direction unit vector (ux, uy, uz)
            momentum (float): Momentum in MeV/c
        """
        self.muon_id = muon_id
        self.start_pos = np.array(start_pos, dtype=float)
        self.direction = np.array(direction, dtype=float)
        self.momentum = momentum
        
        # Velocity v = beta * c. For muon, m = 105.66 MeV/c^2.
        # c = 30 cm/ns.
        m_mu = 105.66
        E = np.sqrt(momentum**2 + m_mu**2)
        self.beta = momentum / E
        self.velocity = self.beta * 30.0 # cm/ns

class MuonGenerator:
    def __init__(self, start_z=85.0):
        """
        Generates cosmic-ray muons.
        
        Args:
            start_z (float): Starting Z-coordinate for all generated muons
        """
        self.start_z = start_z

    def generate_batch(self, num_muons=100000, angular_distribution='cos2'):
        """
        Generates a batch of muons in a vectorized format.
        
        Args:
            num_muons (int): Number of muons to generate
            angular_distribution (str): 'cos2' (realistic cosmic-ray distribution) 
                                         or 'gaussian' (with MUON_ANGULAR_SPREAD)
                                         
        Returns:
            dict: Vectorized arrays representing the generated muons
        """
        half_width = ACTIVE_AREA_SIZE / 2.0
        
        # 1. Random starting position (x, y) on the plane above the tracker
        # We generate positions slightly wider than the active area to allow for inclined tracks
        x0 = np.random.uniform(-half_width * 1.2, half_width * 1.2, num_muons)
        y0 = np.random.uniform(-half_width * 1.2, half_width * 1.2, num_muons)
        z0 = np.full(num_muons, self.start_z)
        positions = np.stack([x0, y0, z0], axis=1)
        
        # 2. Momentum distribution (flat between min and max momentum, or standard cosmic power-law)
        # We will use flat distribution as requested: 1 to 10 GeV/c
        momenta = np.random.uniform(MUON_MIN_MOMENTUM, MUON_MAX_MOMENTUM, num_muons)
        
        # 3. Direction (mostly vertical, u_z is negative)
        phi = np.random.uniform(0, 2.0 * np.pi, num_muons)
        
        if angular_distribution == 'cos2':
            # Cosmic ray intensity I(theta) ~ cos^2(theta)
            # CDF of cos(theta) is F(z) = z^3. Inverse CDF: cos(theta) = u^(1/3)
            u = np.random.uniform(0.0, 1.0, num_muons)
            cos_theta = u**(1.0 / 3.0)
            sin_theta = np.sqrt(1.0 - cos_theta**2)
        else:
            # Gaussian spread in theta around vertical axis
            sigma_rad = np.radians(MUON_ANGULAR_SPREAD)
            theta = np.abs(np.random.normal(0, sigma_rad, num_muons))
            theta = np.clip(theta, 0, np.pi/2)
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)
            
        ux = sin_theta * np.cos(phi)
        uy = sin_theta * np.sin(phi)
        uz = -cos_theta # downward travelling
        directions = np.stack([ux, uy, uz], axis=1)
        
        # 4. Velocities
        m_mu = 105.66
        E = np.sqrt(momenta**2 + m_mu**2)
        beta = momenta / E
        velocities = beta * 30.0 # cm/ns
        
        ids = np.arange(1, num_muons + 1)
        
        return {
            'ids': ids,
            'positions': positions,
            'directions': directions,
            'momenta': momenta,
            'velocities': velocities
        }
