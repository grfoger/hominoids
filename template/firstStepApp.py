import solara
import mesa
from mesa.visualization import SolaraViz, make_space_component

# 1. АГЕНТ
class WalkerAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.steps = 0

        # Физические свойства:
        self.endurance = self.random.randint(1, 10)
        self.maxStamina = 50 + self.endurance * 2
        self.maxHealth = 50 + self.endurance * 2

        # Текущие показатели
        self.satiety = 100
        self.currentStamina = self.maxStamina
        self.currentHealth = self.maxHealth

        # Скиллы
        self.gatherer = self.random.randint(1, 10)

        # Ментальные характеристики
        self.hardworking = self.random.randint(1, 10)

    def step(self):
        if self.currentStamina > 0 and self.random.random() < 0.5:
            neighborhood = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            new_position = self.random.choice(neighborhood)
            self.model.grid.move_agent(self, new_position)
            self.currentStamina = max(0, self.currentStamina - 1)
        else:
            self.currentStamina += 5
            if self.currentStamina > self.maxStamina:
                self.currentStamina = self.maxStamina

        self.steps += 1

# 2. МОДЕЛЬ
class TorusModel(mesa.Model):
    def __init__(self, num_agents=5, width=10, height=10):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.step_counter = 0  # ← Добавлено для реактивности UI

        for _ in range(num_agents):
            agent = WalkerAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
        self.step_counter += 1

# 3. ВИЗУАЛИЗАЦИЯ
def agent_portrayal(agent):
    # Возвращаем dict (работает, но с предупреждением о депрекации — это нормально)
    return {
        "color": "tab:red",
        "size": 50,
        "marker": "o"
    }

@solara.component
def AgentStats(model):
    # Просто читаем данные из модели.
    # SolaraViz должен вызывать этот компонент после каждого model.step()

    # Отладка: проверяем, вызывается ли компонент
    print(f"[DEBUG] AgentStats вызван. Шаг: {model.step_counter}, Агентов: {len(list(model.agents))}")

    agents = list(model.agents)
    if not agents:
        return solara.Text("Нет агентов")

    avg_stamina = sum(a.currentStamina for a in agents) / len(agents)
    avg_health = sum(a.currentHealth for a in agents) / len(agents)
    avg_satiety = sum(a.satiety for a in agents) / len(agents)

    with solara.Card("📊 Статистика агентов", style={"max-width": "600px"}):
        with solara.Row(style={"margin-bottom": "10px", "font-weight": "bold"}):
            solara.Text(f"👥 Агентов: {len(agents)}")
            solara.Text(f"💪 Средняя энергия: {avg_stamina:.1f}")
            solara.Text(f"❤️ Среднее здоровье: {avg_health:.1f}")
            solara.Text(f"🍎 Средняя сытость: {avg_satiety:.1f}")

        solara.Text("─" * 50, style={"margin": "5px 0", "color": "#888"})

        with solara.Row(style={"font-weight": "bold", "background-color": "#f0f0f0", "padding": "5px"}):
            solara.Text("№", style={"width": "30px"})
            solara.Text("Здоровье", style={"width": "80px"})
            solara.Text("Энергия", style={"width": "80px"})
            solara.Text("Сытость", style={"width": "70px"})

        for agent in agents[:10]:
            with solara.Row(style={"padding": "2px 5px"}):
                solara.Text(f"{agent.unique_id}", style={"width": "30px"})
                solara.Text(f"{agent.currentHealth}", style={"width": "80px"})
                solara.Text(f"{agent.currentStamina}", style={"width": "80px"})
                solara.Text(f"{agent.satiety}", style={"width": "70px"})

        if len(agents) > 10:
            solara.Text(f"... и ещё {len(agents) - 10} агентов", style={"font-style": "italic", "margin-top": "5px"})

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
        make_space_component(agent_portrayal=agent_portrayal),
        AgentStats,
    ],
    model_params=model_params,
    name="Random Walk on Torus",
)