# Файл с константами
# TODO пересмотреть имена и необходимость данных констант
from types import SimpleNamespace

# Базовые характеристики агентов
AGENT = SimpleNamespace(
    trait_min=1,
    trait_max=10,
    base_stamina=50,
    stamina_multiplier=2,
    base_health=50,
    health_multiplier=2,
    initial_satiety=100,
    max_satiety=100,
)

# Механика сна
SLEEP = SimpleNamespace(
    need_threshold=16,      # Порог принудительного сна
    recovery_rate=2,        # Единиц needSleep за шаг
    stamina_gain=10,        # Единиц стамины за шаг
)

# Пороги и веса для принятия решений
ACTIONS = SimpleNamespace(
    # Сытость → вес еды/сбора
    satiety_critical=5,
    satiety_low=20,
    weight_eat_critical=10,
    weight_eat_low=3,
    weight_eat_default=1,

    # Стамина → вес отдыха
    stamina_critical=5,
    stamina_low=10,
    stamina_medium=30,
    weight_rest_critical=9,
    weight_rest_low=5,
    weight_rest_medium=3,

    # Трудолюбие → модификатор сбора
    hw_neutral_low=5,
    hw_neutral_high=6,
    hw_modifier_step=0.1,
)

# Собирательство
GATHER = SimpleNamespace(
    stamina_cost=10,
    min_stamina_req=10,
    dice_sides=100,
    difficulty_base=100,
)

# Предметы
BANANA = SimpleNamespace(
    name="Банан",
    calories=10,
    load=5,
    desirability=75,
)

# Параметры модели
MODEL = SimpleNamespace(
    default_width=10,
    default_height=10,
    default_agents=5,
    abundance_min=50,
    abundance_max=100,
)