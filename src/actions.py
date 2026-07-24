# actions.py
from config import AGENT

# ─────────────────────────────────────────────────────────────
# 🎭 СИСТЕМА ДЕЙСТВИЙ (Command/Strategy)
# ─────────────────────────────────────────────────────────────
class Action:
    """Базовый класс действия."""
    name = "base"
    is_group = False  # одиночное по умолчанию

    def can_execute(self, agent) -> bool:
        """Можно ли выполнить действие сейчас?"""
        return True

    def execute(self, agent):
        """Основная логика действия."""
        raise NotImplementedError

    def fallback(self, agent):
        """Что делать, если действие нельзя выполнить."""
        ACTION_REGISTRY["rest"].execute(agent)


class RestAction(Action):
    name = "rest"

    def execute(self, agent):
        agent.current_action = "rest"
        agent.stamina = min(agent.maxStamina, agent.stamina + 5)


class SleepAction(Action):
    name = "sleep"

    def execute(self, agent):
        agent.current_action = "sleep"
        agent.sleeping = True
        agent.needSleep = max(0, agent.needSleep - 2)
        agent.stamina = min(agent.maxStamina, agent.stamina + 10)


class MoveAction(Action):
    name = "move"

    def execute(self, agent):
        agent.current_action = "move"
        neighborhood = agent.model.grid.get_neighborhood(
            agent.pos, moore=True, include_center=False
        )
        new_position = agent.random.choice(neighborhood)
        agent.model.grid.move_agent(agent, new_position)
        agent.stamina = max(0, agent.stamina - 5)


class GatherAction(Action):
    name = "gather"

    def can_execute(self, agent) -> bool:
        """Сбор требует минимум 10 стамины и 5 свободной грузоподъёмности."""
        return agent.stamina >= 10 and agent.capacity >= 5

    def execute(self, agent):
        agent.current_action = "gather"

        # Проверка возможности выполнения
        if not self.can_execute(agent):
            self.fallback(agent)
            return

        agent.stamina = max(0, agent.stamina - 10)
        roll = agent.random.randint(1, 100) + agent.gatherer
        difficulty = 100 - agent.model.get_abundance(agent.pos)

        # Успешный сбор
        if roll > difficulty:
            from types import SimpleNamespace
            agent.inventory.append(SimpleNamespace(
                name="Банан", calories=10, load=5, desirability=75
            ))
            agent.capacity -= 5


class EatAction(Action):
    name = "eat"

    def can_execute(self, agent) -> bool:
        """Еда требует наличия съестного в инвентаре."""
        return any(hasattr(item, 'calories') for item in agent.inventory)

    def execute(self, agent):
        agent.current_action = "eat"

        # Если есть нечего → отдыхаем
        if not self.can_execute(agent):
            self.fallback(agent)
            return

        # Поиск еды с максимальной желательностью
        food_items = [item for item in agent.inventory if hasattr(item, 'calories')]
        max_des = max(item.desirability for item in food_items)
        chosen = agent.random.choice(
            [item for item in food_items if item.desirability == max_des]
        )

        # Съедаем выбранный предмет
        agent.inventory.remove(chosen)
        agent.capacity = min(agent.capacity + chosen.load, agent.maxCapacity)
        agent.satiety = min(agent.satiety + chosen.calories, AGENT.max_satiety)


class CommunicateAction(Action):
    name = "communicate"
    is_group = True  # ← помечаем как групповое

    def can_execute(self, agent) -> bool:
        """Общение требует хотя бы одного соседа в соседних клетках."""
        neighbors = agent.model.grid.get_neighborhood(
            agent.pos, moore=True, include_center=False
        )
        return any(agent.model.grid.get_cell_list_contents(neighbors))

    def execute(self, agent):
        agent.current_action = "communicate"
        agent.socialHunger = max(0, agent.socialHunger - 50)


# 🔥 Реестр всех действий (единая точка правки)
ACTION_REGISTRY = {
    "rest":        RestAction(),
    "sleep":       SleepAction(),
    "move":        MoveAction(),
    "gather":      GatherAction(),
    "eat":         EatAction(),
    "communicate": CommunicateAction(),
}