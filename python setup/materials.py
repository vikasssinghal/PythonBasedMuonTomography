class Material:
    def __init__(self, name, radiation_length, density):
        """
        Represents a material with its physical properties for Multiple Coulomb Scattering.
        
        Args:
            name (str): Name of the material
            radiation_length (float): Radiation length X0 in cm
            density (float): Density in g/cm^3
        """
        self.name = name
        self.radiation_length = radiation_length  # in cm
        self.density = density  # in g/cm^3

# Reference material properties
MATERIALS = {
    'Air': Material('Air', 30516.0, 0.0012),
    'Water': Material('Water', 36.08, 1.0),
    'Plastic': Material('Plastic', 41.7, 1.05),
    'Aluminium': Material('Aluminium', 8.89, 2.7),
    'Concrete': Material('Concrete', 11.55, 2.3),
    'Iron': Material('Iron', 1.76, 7.87),
    'Copper': Material('Copper', 1.43, 8.96),
    'Lead': Material('Lead', 0.56, 11.34),
    'Tungsten': Material('Tungsten', 0.35, 19.3),
    'Uranium': Material('Uranium', 0.32, 18.95)
}
