# ===== run.bat (для Windows) =====
# Сохраните этот файл как run.bat

@echo off
echo Starting Telegram Shop Bot...
python main.py
pause

# ===== run.sh (для Linux/Mac) =====
# Сохраните этот файл как run.sh
# Сделайте исполняемым: chmod +x run.sh

#!/bin/bash
echo "Starting Telegram Shop Bot..."
python3 main.py

# ===== install.bat (установка для Windows) =====
# Сохраните этот файл как install.bat

@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Installation complete!
echo Now edit .env file and run: run.bat
pause

# ===== install.sh (установка для Linux/Mac) =====
# Сохраните этот файл как install.sh
# Сделайте исполняемым: chmod +x install.sh

#!/bin/bash
echo "Installing dependencies..."
pip3 install -r requirements.txt
echo ""
echo "Installation complete!"
echo "Now edit .env file and run: ./run.sh"