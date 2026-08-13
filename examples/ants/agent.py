from enum import Enum, auto
from mesa.discrete_space import CellAgent
class AntState(Enum):
    FORAGING = auto()
    RETURNING = auto()
class Ant(CellAgent):
    """Ant agent navigating HexGrid using pheromones."""
    def __init__(self, model):
        super().__init__(model)
        self.state = AntState.FORAGING
        self.carrying_food = False
        self.wiggle_bias = self.random.uniform(-0.1, 0.1)
    def step(self):
        if self.state == AntState.FORAGING:
            self._step_foraging()
        elif self.state == AntState.RETURNING:
            self._step_returning()
    def _step_foraging(self):
        if self.cell.food > 0:
            self._pickup_food()
            return
        current_val = self.cell.pheromone_home
        self.cell.pheromone_home = min(float(current_val) + 1.0, 10.0)
        self._move_towards_gradient("pheromone_food", randomness=0.3)
    def _step_returning(self):
        if self.cell.home == 1:
            self._drop_food()
            return
        current_val = self.cell.pheromone_food
        self.cell.pheromone_food = min(float(current_val) + 2.0, 10.0)
        self._move_towards_gradient("pheromone_home", randomness=0.1)
    def _pickup_food(self):
        self.cell.food = int(self.cell.food) - 1
        self.carrying_food = True
        self.state = AntState.RETURNING
    def _drop_food(self):
        self.carrying_food = False
        self.state = AntState.FORAGING
    def _move_towards_gradient(self, layer_name, randomness=0.1):
        if self.random.random() < randomness:
            target = self.cell.neighborhood.select_random_cell()
            self.move_to(target)
            return
        best_cell = self.cell
        best_val = -1.0
        for neighbor in self.cell.neighborhood:
            val = float(getattr(neighbor, layer_name))
            if val > best_val:
                best_val = val
                best_cell = neighbor
        if best_cell is not self.cell:
            self.move_to(best_cell)
        else:
            target = self.cell.neighborhood.select_random_cell()
            self.move_to(target)