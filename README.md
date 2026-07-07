### 0. Установить uv (один раз)
irm https://astral.sh/uv/install.ps1 | iex   # PowerShell (Windows)
# или: curl -LsSf https://astral.sh/uv/install.sh | sh   (macOS/Linux)

### 1. Инициализировать проект (один раз, если ещё не сделано)
uv init

### 2. Установить зависимости
uv add "mesa[rec]" solara

### 3. Запустить
uv run solara run app.py

# для опытов:
uv run solara run .\template\firstStepApp.py

# обновить зависимости:
uv lock --upgrade
uv sync

