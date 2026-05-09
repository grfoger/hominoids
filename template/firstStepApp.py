import mesa
from mesa.visualization import SolaraViz, make_space_component

# 1. АГЕНТ
class WalkerAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.steps = 0

        # Физические свойства:
        self.endurance = self.random.randint(1, 10)  # Выносливость от 1 до 10
        self.maxStamina = 50 + self.endurance * 2   # Максимальная стамина 50+2*Выносливость
        self.maxHealth = 50 + self.endurance * 2   # Максимальное здоровье 50+2*Выносливость

        # Текущие показатели
        self.satiety = 100  # При рождении сытость = 100 %
        self.currentStamina = self.maxStamina # При рождении запас стамины максимальный
        self.currentHealth = self.maxHealth # При рождении запас здоровья максимальный

        # Скиллы
        self.gatherer = self.random.randint(1, 10)  # Собиратель от 1 до 10

        # Ментальные характеристики
        self.hardworking = self.random.randint(1, 10)  # Трудолюбивость от 1 до 10

    def step(self):
        # 50% шанс двигаться, но только если стамина > 0
        if self.currentStamina > 0 and self.random.random() < 0.5:
            # Действие А: Движение
            neighborhood = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            new_position = self.random.choice(neighborhood)
            self.model.grid.move_agent(self, new_position)
            self.currentStamina = max(0, self.currentStamina - 1)
        else:
            # Действие Б: Отдых (либо выпало "стоять", либо стамина иссякла)
            self.currentStamina += 5
            # Ограничиваем стамину сверху, чтобы она не уходила в бесконечность
            if self.currentStamina > self.maxStamina:
                self.currentStamina = self.maxStamina

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

initial_model = TorusModel()

Page = SolaraViz(
    model=initial_model,
    components=[
        make_space_component(agent_portrayal=agent_portrayal)
    ],
    model_params=model_params,
    name="Random Walk on Torus",
)