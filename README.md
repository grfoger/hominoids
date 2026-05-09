### 1. Создать и активировать своё виртуальное окружение
python -m venv .venv
.venv\Scripts\activate   # или source .venv/bin/activate

### 2. Установить все зависимости
pip install mesa[rec]

### 3. Запустить
solara run app.py 


# возможно фигня:
pip install --upgrade solara mesa
# для моих опытов:
solara run .\template\firstStepApp.py