import solara
import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.datacollection import DataCollector
from config import AGENT, SLEEP, ACTIONS, GATHER, BANANA, MODEL
# TODO, заменить магические числа на константы из config.py

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
        self.endurance = self._roll_trait(1, 10) # Выносливость
        self.maxStamina = 50 + self.endurance * 2   # Запас энергии / стамина
        self.maxHealth = 50 + self.endurance * 2    # Здоровье
        self.inventory = []                         # Инвентарь, массив с объектами
        self.maxCapacity = 50 + self.endurance * 2  # Сколько может переносить (смесь веса и объёма)

        # Текущие показатели
        self.current_action = "rest"               # При рождении мы отдыхаем
        self.satiety = AGENT.initial_satiety       # Сытость. Пример взятия константы из config.py
        self.stamina = self.maxStamina
        self.health = self.maxHealth
        self.needSleep = 0                          # Накопление невысыпания
        self.sleeping = False                       # Спит в текущий момент?
        self.capacity = self.maxCapacity        # Сколько ещё может вещей набрать, при рождении - максимум

        # Скиллы
        self.gatherer = self._roll_trait(1, 10)  # Навык собирательства

        # Ментальные характеристики
        self.hardworking = self._roll_trait(1, 10)   # Трудолюбие

    def _roll_trait(self, min_val, max_val):
        val = int(round(self.random.triangular(min_val, max_val)))
        return max(min_val, min(max_val, val))

    def step(self):
        # 1. Этап принятия решения
        chosen_action = self.decide_action()

        # 2. Этап исполнения
        self.execute_action(chosen_action)

        # 3. Универсальные обновления в конце шага
        if chosen_action != "sleep":  # Если мы не спали, то
            self.needSleep += 1       # невысыпание растёт
            self.sleeping = False     # Статус: не спим

        self.satiety = max(0, self.satiety - 1)  # Сытость уменьшается
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
            target_eating_weight = 10
        elif self.satiety <= 20:
            target_eating_weight = 3
        else:
            target_eating_weight = 1

        if has_food:
            weights["eat"] = target_eating_weight
        else:
            weights["eat"] = 0
            weights["gather"] = target_eating_weight  # Перенос веса на сбор, если в инвентаре нет еды

        # Коррекция весов сна
        if self.needSleep == 0: # Если мы выспались, то мы просыпаемся
            weights["sleep"] = 0
        if self.needSleep != 0:  # Если мы ещё не выспались...
            if self.needSleep >= 16 or self.sleeping:   # Если мы очень хотим спать или если мы уже спим...
                weights["sleep"] = 3

        # Коррекция весов отдыха
        if self.stamina <= 5:
            weights["rest"] = 9
        if self.stamina <= 10:
            weights["rest"] = 5
        if self.stamina <= 30:
            weights["rest"] = 3

        # Коррекция рабочих занятий из-за показателя трудолюбия
        hw = self.hardworking
        if hw > 6:
            # За каждую единицу выше 6 увеличиваем на 10% от текущего веса
            weights["gather"] *= (1 + (hw - 6) * 0.1)
        elif hw < 5:
            # За каждую единицу ниже 5 уменьшаем на 10% от текущего веса
            weights["gather"] *= (1 - (5 - hw) * 0.1)
        # Если hw == 5 или 6 → вес остаётся без изменений

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
            "eat": self._do_eat,
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
    def _do_eat(self):
        self.current_action = "eat"
        # Поиск еды в инвентаре
        food_items = [item for item in self.inventory if hasattr(item, 'calories')]
        if not food_items:
            self._do_rest()
            return
        # Выбор предмета с макс. desirability (случайный при равенстве)
        max_des = max(item.desirability for item in food_items)
        chosen = self.random.choice([item for item in food_items if item.desirability == max_des])
        # Удаление из инвентаря
        self.inventory.remove(chosen)
        # Облегчение
        self.capacity  = min(self.capacity + chosen.load, self.maxCapacity)
        # Повышение сытости (не выше лимита из конфига)
        self.satiety = min(self.satiety + chosen.calories, AGENT.max_satiety)

    def _do_sleep(self):
        self.current_action = "sleep"
        self.sleeping = True   # Засыпаем
        self.needSleep = max(0, self.needSleep - 2) # Невысыпание уменьшается
        self.stamina = min(self.maxStamina, self.stamina + 10) # Растёт запас энергии

    def _do_gather(self):
        self.current_action = "gather"
        # Да, эта проверка уже есть при выборе решения. Но я считаю, что иногда можно принимать обречённые на провал решения.
        if self.stamina < 10:
            self._do_rest()
            return

        self.stamina = max(0, self.stamina - 10) # Стамина уменьшается
        roll = self.random.randint(1, 100) + self.gatherer
        difficulty = 100 - self.model.get_abundance(self.pos)

        if roll > difficulty and self.capacity >= 5:  # 5 = load банана
            from types import SimpleNamespace
            self.inventory.append(SimpleNamespace(name="Банан", calories=10, load=5, desirability=75))
            self.capacity -= 5

    def _do_move(self):
        self.current_action = "move"
        neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(neighborhood)
        self.model.grid.move_agent(self, new_position)
        self.stamina = max(0, self.stamina - 5)

    def _do_rest(self):
        self.current_action = "rest"
        self.stamina = min(self.maxStamina, self.stamina + 5)

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
                "Avg Stamina": lambda m: sum(a.stamina for a in m.agents) / len(m.agents) if m.agents else 0,
                "Avg Health": lambda m: sum(a.health for a in m.agents) / len(m.agents) if m.agents else 0,
                "Avg Satiety": lambda m: sum(a.satiety for a in m.agents) / len(m.agents) if m.agents else 0,
            },
            agent_reporters={
                "ID": lambda a: a.unique_id,
                "Здоровье": lambda a: a.health,
                "Энергия": lambda a: a.stamina,
                "Сытость": lambda a: a.satiety,
                "ПотребностьСна": lambda a: a.needSleep,
                "Спит": lambda a: a.sleeping,
                "ПредметовВИнвентаре": lambda a: len(a.inventory),
                "ОстатокГрузоподъёмности": lambda a: a.capacity,
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
    styles = {
        "sleep":  {"color": "midnightblue", "marker": "v"},
        "eat":    {"color": "orange",        "marker": "p"},
        "gather": {"color": "forestgreen",   "marker": "^"},
        "move":   {"color": "tab:red",       "marker": ">"},
        "rest":   {"color": "gray",          "marker": "s"},
    }
    # Возвращаем только поддерживаемые ключи: color, size, marker
    return {
        "color": styles.get(agent.current_action, styles["rest"])["color"],
        "size": 50,
        "marker": styles.get(agent.current_action, styles["rest"])["marker"]
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