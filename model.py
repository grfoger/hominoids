import mesa
from mesa.discrete_space import HexGrid
from agent import Ant
class AntForaging(mesa.Model):
    """Ant foraging model on a Hexagonal Grid with PropertyLayers."""
    def __init__(
        self,
        width=30,
        height=30,
        num_ants=50,
        evaporation_rate=0.05,
        diffusion_rate=0.2,
    ):
        super().__init__()
        self.evaporation_rate = evaporation_rate
        self.diffusion_rate = diffusion_rate
        self.grid = HexGrid((width, height), torus=True, random=self.random)
        self.grid.create_property_layer("pheromone_food", default_value=0.0, dtype=float)
        self.grid.create_property_layer("pheromone_home", default_value=0.0, dtype=float)
        self.grid.create_property_layer("food", default_value=0, dtype=int)
        self.grid.create_property_layer("obstacles", default_value=0, dtype=int)
        self.grid.create_property_layer("home", default_value=0, dtype=int)
        self._init_environment()
        self._init_agents(num_ants)
    def _init_environment(self):
        """Setup initial food clusters and the central nest."""
        center = (self.grid.width // 2, self.grid.height // 2)
        # Прямой доступ к numpy-массиву слоя — самый надёжный способ
        self.grid.pheromone_home.data[center] = 1.0
        self.grid.home.data[center] = 1
        for _ in range(3):
            cx = self.random.randint(0, self.grid.width - 1)
            cy = self.random.randint(0, self.grid.height - 1)
            cluster_center = (cx, cy)
            blob = self.grid[cluster_center].get_neighborhood(
                radius=3, include_center=True
            )
            for cell in blob:
                cell.food = self.random.randint(50, 100)
    def _init_agents(self, num_ants):
        """Spawn ants at the nest."""
        center = (self.grid.width // 2, self.grid.height // 2)
        center_cell = self.grid[center]
        for _ in range(num_ants):
            ant = Ant(self)
            ant.cell = center_cell
    def step(self):
        self._update_pheromone_layer("pheromone_food")
        self._update_pheromone_layer("pheromone_home")
        self.agents.shuffle_do("step")
    def _update_pheromone_layer(self, layer_name):
        """Apply evaporation directly to the underlying numpy array."""
        layer = getattr(self.grid, layer_name)
        arr = layer.data
        arr *= 1.0 - self.evaporation_rate
        arr[arr < 0.001] = 0