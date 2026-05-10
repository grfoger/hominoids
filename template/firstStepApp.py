import solara
import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.datacollection import DataCollector

# ─────────────────────────────────────────────────────────────
# КЛАСС ЕДЫ (Банан)
# ─────────────────────────────────────────────────────────────
class FoodItem:
    def __init__(self, name, calories, load, desirability):
        self.name = name
        self.calories = calories
        self.load = load          # условная нагрузка
        self.desirability = desirability

# Прототип банана для копирования при сборе
BANANA_PROTO = FoodItem("Банан", calories=10, load=5, desirability=75)

# 1. АГЕНТ
class WalkerAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.steps = 0

        # Физические свойства:
        self.endurance = self.random.randint(1, 10) # Выносливость
        self.maxStamina = 50 + self.endurance * 2   # Запас энергии / стамина
        self.maxHealth = 50 + self.endurance * 2    # Здоровье
        self.inventory = []                         # Инвентарь, массив с объектами

        # Текущие показатели
        self.satiety = 100                          # Сытость
        self.currentStamina = self.maxStamina
        self.currentHealth = self.maxHealth
        self.needSleep = 0                          # Накопление невысыпания
        self.sleeping = False                       # Спит в текущий момент?

        # Скиллы
        self.gatherer = self.random.randint(1, 10)  # Навык собирательства

        # Ментальные характеристики
        self.hardworking = self.random.randint(1, 10)   # Трудолюбие

    def step(self):
        # 1. Этап принятия решения
        chosen_action = self.decide_action()

        # 2. Этап исполнения
        self.execute_action(chosen_action)

        # 3. Универсальные обновления в конце шага
        if chosen_action != "sleep":
            self.needSleep += 1

        self.satiety = max(0, self.satiety - 1)
        self.steps += 1


# ─────────────────────────────────────────────────────────────
# 🧠 ЭТАП РЕШЕНИЯ: возвращает строку-идентификатор действия
# ─────────────────────────────────────────────────────────────
    def decide_action(self):
        # БАЗОВЫЕ ВЕСА (по умолчанию все равны 1)
        weights = {
            "sleep": 1,
            "gather": 1,
            "move": 1,
            "rest": 1,
            "eat": 1
        }

        # Проверка наличия еды в инвентаре
        # Считаем за еду любой объект, у которого есть атрибут calories
        has_food = any(hasattr(item, 'calories') for item in self.inventory)

        # Коррекция весов по сытости
        if self.satiety <= 5:
            target_food_weight = 10
        elif self.satiety <= 20:
            target_food_weight = 3
        else:
            target_food_weight = 1

        if has_food:
            weights["eat"] = target_food_weight
        else:
            weights["eat"] = 0
            weights["gather"] = target_food_weight  # Перенос веса на сбор, если в инвентаре нет еды

        # Коррекция весов сна
        if self.needSleep == 0: # Если мы выспались, то мы просыпаемся
            weights["sleep"] = 0
        if self.needSleep != 0:  # Если мы ещё не выспались...
            if self.needSleep >= 16 or self.sleeping:   # Если мы очень хотим спать или если мы уже спим...
                weights["sleep"] = 3

        # # 1. Определяем, обязан ли агент спать
        # must_sleep = False
        #
        # if self.needSleep == 0: # Если мы выспались, то мы просыпаемся
        #     self.sleeping = False
        #
        # if self.needSleep != 0:  # Если мы ещё не выспались...
        #     if self.needSleep >= 16 or self.sleeping:   # Если мы очень хотим спать или если мы уже спим...
        #         must_sleep = True # , то мы обязаны выбрать сон
        #
        # if must_sleep:
        #     # 🔹 ДЕЙСТВИЕ: СОН
        #     self.sleeping = True   # Засыпаем
        #     self.needSleep = max(0, self.needSleep - 2) # Невысыпание уменьшается на 2
        #     self.currentStamina = min(self.maxStamina, self.currentStamina + 10) # Растёт запас энергии
        #
        # else:
        #     # 🔹 ДЕЙСТВИЕ: ДВИЖЕНИЕ или ОТДЫХ (50/50)
        #     # Двигаться можно только если стамина > 0
        #     if self.currentStamina > 0 and self.random.random() < 0.5:
        #         neighborhood = self.model.grid.get_neighborhood(
        #             self.pos, moore=True, include_center=False
        #         )
        #         new_position = self.random.choice(neighborhood)
        #         self.model.grid.move_agent(self, new_position)
        #         self.currentStamina = max(0, self.currentStamina - 10) # Запас энергии уменьшается
        #     else: # действие отдыха
        #         self.currentStamina += 5   # восстанавливаем запас энергии
        #         if self.currentStamina > self.maxStamina:
        #             self.currentStamina = self.maxStamina
        #
        #     # Так как действие отличное от сна, needSleep растёт
        #     self.needSleep += 1
        #
        # # 2. В КОНЦЕ КАЖДОГО ШАГА: сытость уменьшается на 1 (мин 0)
        # self.satiety = max(0, self.satiety - 1)
        # self.steps += 1

        # ПРЕОБРАЗОВАНИЕ ВЕСОВ В ДИАПАЗОНЫ 1d100
        total_weight = sum(weights.values())
        if total_weight == 0:
            return "rest"  # Защита от деления на ноль

        # Строим диапазоны: [(lower, upper, action), ...]
        ranges = []
        current_start = 1.0
        for action, w in weights.items():
            if w <= 0:
                continue
            # Размер диапазона пропорционален весу относительно суммы всех весов
            span = (w / total_weight) * 100.0
            current_end = current_start + span
            ranges.append((current_start, current_end, action))
            current_start = current_end + 0.01  # Микро-зазор для избежания наложений границ

        # БРОСОК 1d100
        roll = self.random.uniform(1.0, 100.0)

        # ВЫБОР ДЕЙСТВИЯ по выпавшему диапазону
        for low, high, action in ranges:
            if low <= roll <= high:
                return action

        # Фоллбэк (на случай погрешностей float), я не понимаю, что это означает.
        return "rest"

    # ─────────────────────────────────────────────────────────────
    # ⚙️ ЭТАП ИСПОЛНЕНИЯ: диспетчер действий
    # ─────────────────────────────────────────────────────────────
    def execute_action(self, action_name):
        action_map = {
            "sleep": self._do_sleep,
            "gather": self._do_gather,
            "move": self._do_move,
            "rest": self._do_rest,
            # "eat": self._do_eat,      # ← Добавить новое действие: 1 строка
            # "trade": self._do_trade,  # ← Ещё одно: 1 строка
        }
        executor = action_map.get(action_name)
        if executor:
            executor()
        else:
            raise ValueError(f"Unknown action: {action_name}")

    # ─────────────────────────────────────────────────────────────
    # 🛠 ЛОГИКА КОНКРЕТНЫХ ДЕЙСТВИЙ (вынесена в отдельные методы)
    # ─────────────────────────────────────────────────────────────
    def _do_sleep(self):
        self.sleeping = True   # Засыпаем
        self.needSleep = max(0, self.needSleep - 2) # Невысыпание уменьшается
        self.currentStamina = min(self.maxStamina, self.currentStamina + 10) # Растёт запас энергии

    def _do_gather(self):
        # Да, эта проверка уже есть при выборе решения. Но я считаю, что иногда можно принимать обречённые на провал решения.
        if self.currentStamina < 10:
            self._do_rest()
            return

        self.currentStamina = max(0, self.currentStamina - 10) # Стамина уменьшается
        roll = self.random.randint(1, 100) + self.gatherer
        difficulty = 100 - self.model.get_abundance(self.pos)

        if roll > difficulty and self.freeCapacity >= 5:  # 5 = load банана
            from types import SimpleNamespace
            self.inventory.append(SimpleNamespace(name="Банан", calories=10, load=5, desirability=75))
            self.freeCapacity -= 5

    def _do_move(self):
        neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(neighborhood)
        self.model.grid.move_agent(self, new_position)
        self.currentStamina = max(0, self.currentStamina - 1)

    def _do_rest(self):
        self.currentStamina = min(self.maxStamina, self.currentStamina + 5)

# ─────────────────────────────────────────────────────────────
# 2. МОДЕЛЬ
# ─────────────────────────────────────────────────────────────
class TorusModel(mesa.Model):
    def __init__(self, num_agents=5, width=10, height=10):
        super().__init__()
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.step_counter = 0

        # Изобилие назначается от 50 до 100 для каждой клетки
        self.abundance_grid = [
            [self.random.randint(50, 100) for _ in range(width)]
            for _ in range(height)
        ]

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
                "ПотребностьСна": lambda a: a.needSleep,
                "Спит": lambda a: a.sleep,
                "ПредметовВИнвентаре": lambda a: len(a.inventory),
                "ОстатокГрузоподъёмности": lambda a: a.free_capacity,
            }
        )

        for _ in range(num_agents):
            agent = WalkerAgent(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))

    def get_abundance(self, pos):
        """Возвращает значение изобилия клетки в позиции (x, y)."""
        x, y = pos
        return self.abundance_grid[y][x]

    def step(self):
        self.agents.shuffle_do("step")
        self.step_counter += 1
        self.datacollector.collect(self)

# ─────────────────────────────────────────────────────────────
# 3. ВИЗУАЛИЗАЦИЯ
# ─────────────────────────────────────────────────────────────
def agent_portrayal(agent):
    return {
        "color": "tab:red",
        "size": 50,
        "marker": "o"
    }

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

# Таблица временно убрана, оставлены сетка и графики
Page = SolaraViz(
    model=initial_model,
    components=[
        make_space_component(agent_portrayal=agent_portrayal),
        make_plot_component(["Avg Stamina", "Avg Health", "Avg Satiety"]),
    ],
    model_params=model_params,
    name="Random Walk on Torus",
)