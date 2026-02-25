# Installation
## Requirements
- python3.11 (`brew install python@3.11`)

## Installation
1. create venv
```shell
python3.11 -m venv venv
````
2. activate venv

**Windows**
```shell
venv\Scripts\activate
```

**Mac & Linux**
```shell
source venv/bin/activate
````

3. Start game
```shell
python -m ui.game
```

4. Train ai
```shell
python -m minesweeper.ai
```