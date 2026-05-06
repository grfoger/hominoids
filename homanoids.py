import mesa
import matplotlib.pyplot as plt
import numpy as np

# ---------- Модель ----------
class HominoidAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.unique_id = model.next_id()
        self.energy = self.random.randint(5, 15)

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        food_here = [obj for obj in cell_contents if isinstance(obj, Food)]
        if food_here:
            food = food_here[0]
            self.energy += food.amount
            food.remove()                # безопасное удаление

    def reproduce(self):
        if self.energy >= 20:
            self.energy -= 10
            offspring = HominoidAgent(self.model)
            self.model.grid.place_agent(offspring, self.pos)

    def step(self):
        self.move()
        self.eat()
        self.reproduce()
        self.energy -= 1
        if self.energy <= 0:
            self.remove()                # безопасное удаление

class Food(mesa.Agent):
    def __init__(self, model, amount=3):
        super().__init__(model)
        self.unique_id = model.next_id()
        self.amount = amount

    def step(self):
        pass

class HominoidSociety(mesa.Model):
    def __init__(self, width=20, height=20, initial_population=10):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.current_id = 0

        for _ in range(initial_population):
            agent = HominoidAgent(self)
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            self.grid.place_agent(agent, (x, y))

        for _ in range(width * height // 2):
            food = Food(self, amount=2)
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            self.grid.place_agent(food, (x, y))

        self.food_regeneration_prob = 0.05

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def step(self):
        self.agents.shuffle_do("step")
        if self.random.random() < self.food_regeneration_prob:
            for _ in range(3):
                food = Food(self, amount=2)
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                cell_contents = self.grid.get_cell_list_contents([(x, y)])
                if not any(isinstance(obj, Food) for obj in cell_contents):
                    self.grid.place_agent(food, (x, y))

# ---------- Визуализация (matplotlib) ----------
def run_visualization(model, steps=500, interval=0.1):
    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-0.5, model.width - 0.5)
    ax.set_ylim(-0.5, model.height - 0.5)
    ax.set_xticks(np.arange(0, model.width, 1))
    ax.set_yticks(np.arange(0, model.height, 1))
    ax.grid(True, linestyle='-', alpha=0.3)
    ax.set_title("Хоминоиды: модель развития общества")

    # Собираем позиции с проверкой на None
    agents_pos = [a.pos for a in model.agents if isinstance(a, HominoidAgent) and a.pos is not None]
    food_pos = [a.pos for a in model.agents if isinstance(a, Food) and a.pos is not None]

    agents_x, agents_y = zip(*agents_pos) if agents_pos else ([], [])
    food_x, food_y = zip(*food_pos) if food_pos else ([], [])

    scatter_agents = ax.scatter(agents_x, agents_y, c='red', s=50, label='Хоминоиды')
    scatter_food = ax.scatter(food_x, food_y, c='green', s=30, label='Еда', marker='s')
    ax.legend(loc='upper right')

    for step_num in range(steps):
        model.step()

        agents_pos = [a.pos for a in model.agents if isinstance(a, HominoidAgent) and a.pos is not None]
        food_pos = [a.pos for a in model.agents if isinstance(a, Food) and a.pos is not None]

        if agents_pos:
            axs, ays = zip(*agents_pos)
            scatter_agents.set_offsets(np.column_stack([axs, ays]))
        else:
            scatter_agents.set_offsets(np.empty((0, 2)))

        if food_pos:
            fxs, fys = zip(*food_pos)
            scatter_food.set_offsets(np.column_stack([fxs, fys]))
        else:
            scatter_food.set_offsets(np.empty((0, 2)))

        ax.set_title(f"Шаг {step_num+1} | Хоминоидов: {len(agents_pos)}")
        plt.pause(interval)

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    model = HominoidSociety(width=20, height=20, initial_population=10)
    run_visualization(model, steps=500, interval=0.1)