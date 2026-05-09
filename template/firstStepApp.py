import solara
import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.datacollection import DataCollector

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
        self.needSleep = 0
        self.sleep = False

        # Скиллы
        self.gatherer = self.random.randint(1, 10)

        # Ментальные характеристики
        self.hardworking = self.random.randint(1, 10)

    def step(self):

        # 1. Определяем, обязан ли агент спать
        must_sleep = False

        if self.needSleep == 0: # Если мы выспались, то мы просыпаемся
            self.sleep = False

        if self.needSleep != 0:  # Если мы ещё не выспались...
            if self.needSleep >= 16 or self.sleep:   # Если мы очень хотим спать или если мы уже спим...
                must_sleep = True # , то мы обязаны выбрать сон

        if must_sleep:
            # 🔹 ДЕЙСТВИЕ: СОН
            self.needSleep = max(0, self.needSleep - 2)
            self.currentStamina = min(self.maxStamina, self.currentStamina + 10)

        else:
            # 🔹 ДЕЙСТВИЕ: ДВИЖЕНИЕ или ОТДЫХ (50/50)
            # Двигаться можно только если стамина > 0
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

            # Так как действие отличное от сна, needSleep растёт
            self.needSleep += 1

        # 2. В КОНЦЕ КАЖДОГО ШАГА: сытость уменьшается на 1 (мин 0)
        self.satiety = max(0, self.satiety - 1)
        self.steps += 1

# 2. МОДЕЛЬ
class TorusModel(mesa.Model):
    def __init__(self, num_agents=5, width=10, height=10):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.step_counter = 0

        # 🔥 DataCollector: собирает данные автоматически после каждого step()
        self.datacollector = DataCollector(
            model_reporters={
                "Step": lambda m: m.step_counter,
                "Avg Stamina": lambda m: sum(a.currentStamina for a in m.agents) / len(m.agents) if m.agents else 0,
                "Avg Health": lambda m: sum(a.currentHealth for a in m.agents) / len(m.agents) if m.agents else 0,
                "Avg Satiety": lambda m: sum(a.satiety for a in m.agents) / len(m.agents) if m.agents else 0,
            },
            agent_reporters={
                "ID": lambda a: a.unique_id,
                "Здоровье": lambda a: a.currentHealth,
                "Энергия": lambda a: a.currentStamina,
                "Сытость": lambda a: a.satiety,
            }
        )

        for _ in range(num_agents):
            agent = WalkerAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))

    def step(self):
        self.agents.shuffle_do("step")
        self.step_counter += 1
        # 🔥 Ключевая строка: собираем данные после каждого шага
        self.datacollector.collect(self)

# 3. ВИЗУАЛИЗАЦИЯ
def agent_portrayal(agent):
    return {
        "color": "tab:red",
        "size": 50,
        "marker": "o"
    }

# 4 КАСТОМНЫЙ КОМПОНЕНТ: Таблица с данными агентов
@solara.component
def AgentTable(model):
    agents = list(model.agents)
    if not agents:
        with solara.Card("📋 Данные агентов (F5 для обновление занчений)", style={"max-width": "700px"}):
            solara.Text("⏳ Ожидание агентов...")
        return

    # Формируем данные
    table_data = [
        {
            "ID": agent.unique_id,
            "Здоровье": agent.currentHealth,
            "Энергия": agent.currentStamina,
            "Сытость": agent.satiety,
        }
        for agent in agents[:10]
    ]

    # 🔥 Преобразуем список в pandas DataFrame (требование solara.DataFrame)
    df = pd.DataFrame(table_data)

    with solara.Card("📋 Данные агентов (F5 для обновление занчений)", style={"max-width": "700px"}):
        solara.Text(f"Шаг симуляции: **{model.step_counter}**", style={"font-weight": "bold", "margin-bottom": "10px"})
        solara.DataFrame(df)

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

# 🔥 СБОРКА ИНТЕРФЕЙСА
Page = SolaraViz(
    model=initial_model,
    components=[
        make_space_component(agent_portrayal=agent_portrayal),
        make_plot_component(["Avg Stamina", "Avg Health", "Avg Satiety"]),
        AgentTable,  # ← Добавляем нашу таблицу
    ],
    model_params=model_params,
    name="Random Walk on Torus",
)