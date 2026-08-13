import mesa
from mesa.datacollection import DataCollector
from config import AGENT
from actions import ACTION_REGISTRY

# TODO, заменить магические числа на константы из config.py

# ─────────────────────────────────────────────────────────────
# УРОВНИ ЖЕЛАНИЯ (Desire Levels)
# ─────────────────────────────────────────────────────────────
PRIORITY = {
    "impossible":     0.0,      # 0%
    "never":          0.005,    # ~0.1%
    "unlikely":       0.263,    # ~5%
    "just_for_lulz":  1.25,     # ~20%
    "why_not":        5.0,      # ~50% (базовый вес)
    "probably":       11.67,    # ~70%
    "necessary":      28.33,    # ~85%
    "at_all_costs":   995.0,    # ~99.5%
}

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

# ─────────────────────────────────────────────────────────────
# 1. АГЕНТ
# ─────────────────────────────────────────────────────────────
class WalkerAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.steps = 0

        # Ментальные характеристики (определяем раньше, т.к. нужны для maxSocialHunger)
        self.sociality = self._roll_trait(1, 10)     # Социальность
        self.hardworking = self._roll_trait(1, 10)   # Трудолюбие
        self.gatherer = self._roll_trait(1, 10)      # Навык собирательства

        # Физические свойства:
        self.endurance = self._roll_trait(1, 10)     # Выносливость
        self.maxStamina = 50 + self.endurance * 2    # Запас энергии / стамина
        self.maxSocialHunger = 80 + self.sociality * 3  # Максимум жажды общения
        self.maxHealth = 50 + self.endurance * 2     # Здоровье
        self.maxCapacity = 50 + self.endurance * 2   # Сколько может переносить
        self.inventory = []                          # Инвентарь, массив с объектами

        # Текущие показатели
        self.chosen_action = "rest"                  # При рождении планируем отдохнуть
        self.current_action = "rest"                 # При рождении отдыхаем
        self.satiety = AGENT.initial_satiety         # Сытость
        self.stamina = self.maxStamina
        self.socialHunger = 0                        # При рождении не жаждем общения
        self.health = self.maxHealth
        self.needSleep = 0                           # Накопление невысыпания
        self.sleeping = False                        # Спит в текущий момент?
        self.capacity = self.maxCapacity             # Сколько ещё может вещей набрать

    def _roll_trait(self, min_val, max_val):
        val = int(round(self.random.triangular(min_val, max_val)))
        return max(min_val, min(max_val, val))

    def step(self):
        # 1. Принимаем решение
        chosen_action = self.decide_action()
        # 2. Исполняем
        self.execute_action(chosen_action)

        # 3. Универсальные обновления в конце шага
        if chosen_action != "sleep":   # Если мы не спим, то
            self.needSleep += 1         # невысыпание растёт
            self.sleeping = False           # Статус: не спим

        self.satiety = max(0, self.satiety - 1)

        if chosen_action != "communicate":  # Если мы не общались, то хотим общаться
            self.socialHunger = min(self.maxSocialHunger, self.socialHunger + 5)

        self.steps += 1

    # ─────────────────────────────────────────────────────────────
    # 🧠 ЭТАП РЕШЕНИЯ
    # ─────────────────────────────────────────────────────────────
    def decide_action(self, weight_mods=None):
        desires = {
            "communicate": PRIORITY["why_not"],
            "sleep":       PRIORITY["why_not"],
            "gather":      PRIORITY["why_not"],
            "move":        PRIORITY["why_not"],
            "rest":        PRIORITY["why_not"],
            "eat":         PRIORITY["why_not"]
        }

        # --- Сытость ---
        has_food = any(hasattr(item, 'calories') for item in self.inventory)
        if self.satiety <= 5:
            desires["eat"] = PRIORITY["at_all_costs"]
        elif self.satiety <= 20:
            desires["eat"] = PRIORITY["necessary"]
        else:
            desires["eat"] = PRIORITY["unlikely"]

        if not has_food:
            desires["eat"] = PRIORITY["impossible"] # Есть нечего
            # Если есть нечего, желание искать еду растёт
            if self.satiety <= 5:
                desires["gather"] = PRIORITY["at_all_costs"]
            elif self.satiety <= 20:
                desires["gather"] = PRIORITY["necessary"]

        # --- Сон ---
        if self.needSleep == 0:
            desires["sleep"] = PRIORITY["never"]
        elif self.needSleep >= 16 or self.sleeping:
            desires["sleep"] = PRIORITY["at_all_costs"]
        else:
            desires["sleep"] = PRIORITY["unlikely"]

        # --- Отдых (Стамина) ---
        if self.stamina <= 5:
            desires["rest"] = PRIORITY["at_all_costs"]
        elif self.stamina <= 10:
            desires["rest"] = PRIORITY["necessary"]
        elif self.stamina <= 30:
            desires["rest"] = PRIORITY["probably"]
        else:
            desires["rest"] = PRIORITY["unlikely"]

        # --- Общение (Социальный голод) ---
        if self.socialHunger >= self.maxSocialHunger:
            desires["communicate"] = PRIORITY["at_all_costs"]
        elif self.socialHunger == 0:
            desires["communicate"] = PRIORITY["never"]
        elif self.socialHunger >= 0.8 * self.maxSocialHunger:
            desires["communicate"] = PRIORITY["necessary"]
        elif self.socialHunger >= 0.5 * self.maxSocialHunger:
            desires["communicate"] = PRIORITY["why_not"]
        elif self.socialHunger < 0.3 * self.maxSocialHunger:
            desires["communicate"] = PRIORITY["unlikely"]

        # Трудолюбие
        hw = self.hardworking
        if hw > 6:
            desires["gather"] *= (1 + (hw - 6) * 0.1)
        elif hw < 5:
            desires["gather"] *= (1 - (5 - hw) * 0.1)

        # Социальность
        sc = self.sociality
        if sc > 6:
            desires["communicate"] *= (1 + (sc - 6) * 0.1)
        elif sc < 5:
            desires["communicate"] *= (1 - (5 - sc) * 0.1)

        # Внешние модификаторы (для будущей координации)
        if weight_mods:
            for action, mult in weight_mods.items():
                if action in desires:
                    desires[action] *= mult

        # Проверка контекста (нет соседей -> communicate = never)
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        has_neighbors = any(self.model.grid.get_cell_list_contents(neighbors))
        if not has_neighbors:
            desires["communicate"] = PRIORITY["never"]

        # Бросок
        total_weight = sum(desires.values())
        if total_weight == 0:
            return "rest"

        ranges = []
        current = 1.0
        for action, w in desires.items():
            if w <= 0:
                continue
            span = (w / total_weight) * 100.0
            ranges.append((current, current + span, action))
            current += span

        roll = self.random.uniform(1.0, 100.0)

        # Выбор
        chosen = "rest"
        for low, high, action in ranges:
            if low <= roll <= high:
                chosen = action
                break

        # 🔍 ОТЛАДКА для агента #1
        if self.unique_id == 1:
            print(f"\n[Agent 1] Step {self.steps} | Roll: {roll:.2f}")
            print(f"  Stamina: {self.stamina}, Satiety: {self.satiety}, socialHunger: {self.socialHunger}")
            print(f"  Desires: { {k: round(v,2) for k,v in desires.items()} }")
            print(f"  Ranges: {[(f'{a}:{round(l,1)}-{round(h,1)}') for l,h,a in ranges]}")
            print(f"  Chosen action is: {chosen}")

        return chosen

    # ─────────────────────────────────────────────────────────────
    # ⚙️ ЭТАП ИСПОЛНЕНИЯ: диспетчер действий
    # ─────────────────────────────────────────────────────────────
    def execute_action(self, action_name):
        action = ACTION_REGISTRY.get(action_name)

        # Неизвестное действие → отдых (защита)
        if action is None:
            ACTION_REGISTRY["rest"].execute(self)
            return

        # Групповое действие без партнёра → fallback
        if action.is_group and not action.can_execute(self):
            action.fallback(self)
            return

        action.execute(self)

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