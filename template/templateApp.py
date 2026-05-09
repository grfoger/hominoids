import mesa
from mesa.visualization import SolaraViz, make_space_component

# 1. АГЕНТ
class WalkerAgent(mesa.Agent):
    def __init__(self, model):
        # В Mesa 3.x unique_id генерируется автоматически
        super().__init__(model)
        self.steps = 0

    def step(self):
        # Получаем список соседей
        neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(neighborhood)
        self.model.grid.move_agent(self, new_position)
        self.steps += 1

# 2. МОДЕЛЬ
class TorusModel(mesa.Model):
    def __init__(self, num_agents=5, width=10, height=10):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        
        for _ in range(num_agents):
            agent = WalkerAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        # Активация всех агентов
        self.agents.shuffle_do("step")

# 3. ВИЗУАЛИЗАЦИЯ
def agent_portrayal(agent):
    return {"color": "tab:red", "size": 50, "marker": "o"}

model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 5,
        "label": "Количество агентов",
        "min": 1,
        "max": 20,
        "step": 1,
    },
}

# СОЗДАЕМ ИНСТАНС МОДЕЛИ (как в вашем рабочем примере с муравьями)
initial_model = TorusModel()

# СБОРКА СТРАНИЦЫ
# Мы передаем initial_model первым аргументом (позиционно)
Page = SolaraViz(
    model=initial_model, 
    components=[
        make_space_component(agent_portrayal=agent_portrayal)
    ],
    model_params=model_params,
    name="Random Walk on Torus",
)