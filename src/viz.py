# ─────────────────────────────────────────────────────────────
# 3. ВИЗУАЛИЗАЦИЯ
# ─────────────────────────────────────────────────────────────
from mesa.visualization import SolaraViz, make_plot_component
import solara
import altair as alt
import pandas as pd
from mesa.visualization.utils import update_counter
from hommy import TorusModel

# карта стилей: действие -> (цвет, форма Vega-Lite)
# формы Vega ограничены набором: circle, square, cross, diamond,
# triangle-up/-down/-right/-left. Цвета — любые CSS-имена или hex.
ACTION_STYLE = {
    "sleep":  ("midnightblue", "triangle-down"),
    "eat":    ("orange",       "diamond"),
    "gather": ("forestgreen",  "triangle-up"),
    "move":   ("#d62728",      "triangle-right"),  # это matplotlib-ий tab:red в hex
    "rest":   ("gray",         "square"),
}
ORDER  = list(ACTION_STYLE.keys())
COLORS = [ACTION_STYLE[a][0] for a in ORDER]
SHAPES = [ACTION_STYLE[a][1] for a in ORDER]

def _agents_df(model):
    rows = []
    for a in model.agents:
        x, y = a.pos
        rows.append({
            "id": a.unique_id, "x": x, "y": y,
            "action": a.current_action,
            "health": a.health, "stamina": a.stamina, "satiety": a.satiety,
        })
    return pd.DataFrame(rows)

@solara.component
def HommiSpace(model):
    update_counter.get()          # без этой строки картинка застынет на 1-м кадре
    df = _agents_df(model)

    chart = (
        alt.Chart(df)
        .mark_point(size=200, filled=True, opacity=1)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-0.5, model.grid.width - 0.5])),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.5, model.grid.height - 0.5])),
            # фиксируем domain+range, чтобы у действия ВСЕГДА был один цвет/форма,
            # даже если в этом кадре какого-то действия нет
            color=alt.Color("action:N", scale=alt.Scale(domain=ORDER, range=COLORS)),
            shape=alt.Shape("action:N", scale=alt.Scale(domain=ORDER, range=SHAPES)),
            tooltip=[
                alt.Tooltip("id:N",      title="Хомми"),
                alt.Tooltip("action:N",  title="Занятие"),
                alt.Tooltip("health:Q",  title="Здоровье"),
                alt.Tooltip("stamina:Q", title="Энергия"),
                alt.Tooltip("satiety:Q", title="Сытость"),
            ],
        )
        .properties(width=400, height=400)
    )
    solara.FigureAltair(chart)

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

# 🔧 Создаём экземпляр модели (работает с вашей версией Mesa)
initial_model = TorusModel()

Page = SolaraViz(
    model=initial_model,
    components=[HommiSpace,
                make_plot_component(["Avg Stamina", "Avg Health", "Avg Satiety"])],
    model_params=model_params,
    name="Hommi Sandbox",
)