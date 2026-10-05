# Hator Keyboard RGB & Screen Controller (Python)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Linux | Windows | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)]()

Библиотека и CLI-утилита для прямого управления RGB-подсветкой и встроенным TFT-экраном клавиатуры **Hator Icefall PRO** (а также совместимых моделей Hator на чипах I-CHIP) через стандартный USB/HID протокол без необходимости веб-драйвера или стороннего софта.

---

## 🚀 Установка через pip

### 1. Установка напрямую из GitHub:

```bash
# Базовая установка (управление подсветкой и встроенными режимами):
pip install git+https://github.com/vanyabudash2-netizen/icefallDOOM.git

# Полная установка (с поддержкой TFT-экрана, загрузки картинок и HUD-мониторинга):
pip install "hator-keyboard[all] @ git+https://github.com/vanyabudash2-netizen/icefallDOOM.git"
```

### 2. Установка из локального репозитория (для разработки):

```bash
git clone https://github.com/vanyabudash2-netizen/icefallDOOM.git
cd icefallDOOM

# Установка в режиме разработки:
pip install -e .

# Или со всеми зависимостями (Pillow, psutil):
pip install -e ".[all]"
```

После установки в системе будут доступны консольные команды **`hator`** и **`hator-keyboard`**.

---

## ⚙️ Настройка прав доступа в Linux (udev)

По умолчанию в Linux прямой доступ к устройствам `/dev/hidraw*` разрешён только `root`. Чтобы управлять подсветкой и экраном от обычного пользователя без `sudo`:

### Способ 1: Автоматически через CLI (рекомендуется)
```bash
hator setup-udev --install
```
*(команда запросит пароль `sudo` один раз для записи правила в `/etc/udev/rules.d/`)*

### Способ 2: Вручную
```bash
sudo cp 99-hator.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

---

## 💻 Использование из консоли (CLI)

После установки библиотеки через `pip` используйте команду `hator` (или `hator-keyboard` / `python -m hator_keyboard`):

```bash
# Показать справку по всем командам
hator --help

# Список всех доступных названий клавиш
hator list-keys

# Список встроенных эффектов
hator list-modes

# Включить готовый игровой профиль (WASD, стрелки, фон)
hator wasd --wasd red --arrows yellow --others "#001030"

# Включить постоянный статический цвет (hex или имя)
hator static "#00FFCC" --brightness 4

# Включить встроенный режим (например, волна)
hator mode wave --brightness 4 --speed 3

# Установить цвет конкретной клавиши
hator set-key esc red
hator set-key space "#FF00FF"

# Настроить время до отключения подсветки / сна (в минутах)
hator sleep-timeout --wired 10 --wireless-backlight 2 --wireless-sleep 10

# Выключить подсветку
hator off

# Сброс настроек клавиатуры к заводским
hator reset
```

### Управление TFT-экраном (128x128)

```bash
# Разбудить экран, переключить на Home и синхронизировать время
hator screen-wake

# Синхронизировать системную дату и время
hator screen-sync

# Переключить экран на главный экран (Home)
hator screen-home

# Переключить экран на страницу картинки или GIF
hator screen-pic
hator screen-gif

# Загрузить изображение на экран клавиатуры (PNG, JPG, BMP, WebP с автоподгонкой 128x128)
hator screen-image ./avatar.png

# Вывести дашборд системного мониторинга (CPU, RAM, Temp, Clock)
hator screen-hud

# Запустить живой мониторинг в реальном времени (обновление каждые 3 секунды)
hator screen-hud-live -i 3
```

---

## 🐍 Использование как Python-библиотеки

### 1. Индивидуальная подсветка клавиш (WASD, стрелки, группы)

```python
from hator_keyboard import HatorKeyboard

with HatorKeyboard() as kbd:
    # Яркость: 0 (выкл) .. 4 (макс)
    kbd.set_brightness(4)

    # Заливаем всю клавиатуру мягким темно-синим цветом
    kbd.set_all_keys((0, 15, 45))

    # Выделяем блок WASD красным
    kbd.fill_group("wasd", "red")

    # Стрелки - желтым
    kbd.fill_group("arrows", "#FFFF00")

    # Отдельные клавиши
    kbd.set_key_color("space", "green")
    kbd.set_key_color("esc", (0, 255, 255))
    kbd.set_key_color("enter", "magenta")

    # Сохраняем в память клавиатуры
    kbd.apply()
```

### 2. Включение встроенных режимов

```python
from hator_keyboard import HatorKeyboard

with HatorKeyboard() as kbd:
    # Режимы: 'wave', 'cloud', 'neon', 'swirl', 'breathing', 'static', 'spectrum', 'off' и др.
    kbd.set_mode("wave", brightness=4, speed=3)
```

### 3. Установка единого цвета всей клавиатуры

```python
from hator_keyboard import HatorKeyboard

with HatorKeyboard() as kbd:
    kbd.set_static_color("#FF5500", brightness=4)
```

### 4. Потоковая анимация в реальном времени (до 30+ FPS)

```python
import time
import math
from hator_keyboard import HatorKeyboard, KEY_MAP

with HatorKeyboard() as kbd:
    start = time.time()
    while time.time() - start < 10.0:  # 10 секунд плавной волны
        t = time.time() * 4.0
        frame = [0] * kbd.TOTAL_BYTES
        for name, idx in KEY_MAP.items():
            val = (math.sin(idx * 0.2 + t) + 1) / 2
            frame[idx * 3 + 0] = int(255 * val)        # R
            frame[idx * 3 + 1] = int(50 * (1 - val))   # G
            frame[idx * 3 + 2] = int(255 * (1 - val))  # B

        kbd.stream_frame(frame)
        time.sleep(0.03)

    kbd.close_stream()
```

### 5. Загрузка картинки или рисование на TFT-экране

```python
from PIL import Image
from hator_keyboard import HatorKeyboard

with HatorKeyboard() as kbd:
    # Загрузка файла
    kbd.upload_screen_image("my_picture.png")

    # Или передача PIL Image напрямую:
    img = Image.new("RGB", (128, 128), color=(10, 20, 30))
    kbd.upload_screen_image(img)
```

---

## 🗺 Карта клавиш (Hator Icefall PRO 75%)

| Ряд | Доступные клавиши |
|---|---|
| **F-ряд** | `esc`, `f1`..`f12`, `home` |
| **Цифровой** | `tilde` (`~`), `1`..`0`, `-`, `=`, `backspace` |
| **QWERTY** | `tab`, `q`..`p`, `[`, `]`, `\`, `del` |
| **ASDF** | `caps`, `a`..`l`, `;`, `'`, `enter`, `pgup` |
| **ZXCV** | `shift_l`, `z`..`m`, `,`, `.`, `/`, `shift_r`, `up`, `pgdn` |
| **Нижний** | `ctrl_l`, `win`, `alt_l`, `space`, `alt_r`, `fn`, `ctrl_r`, `left`, `down`, `right` |

**Готовые группы клавиш:**
- `wasd` — `w`, `a`, `s`, `d`
- `arrows` — `up`, `down`, `left`, `right`
- `numbers` — `1`..`0`, `-`, `=`
- `fn_row` — `esc`, `f1`..`f12`, `home`
- `nav` — `home`, `del`, `pgup`, `pgdn`
- `modifiers` — `ctrl_l`, `win`, `alt_l`, `space`, `alt_r`, `fn`, `ctrl_r`, `shift_l`, `shift_r`

---

## 🔍 Протокол клавиатуры (реверс-инжиниринг)

Веб-приложение Hator использует стандарт **WebHID** для общения с микроконтроллером:
- **Vendor ID (VID):** `14234` (`0x379A`) / `10473` (`0x28E9`)
- **Product ID (PID):** `2336` (`0x0920` — проводной режим), `2337` (`0x0921` — 2.4G ресивер)
- **HID Usage Page:** `65415` (`0xFF87`), **Usage:** `32` (`0x0020`)
- **Report ID:** `6` (длина репорта: 64 байта = 1 байт Report ID + 63 байта пакета)

### Структура пакета управления (63 байта):
```text
Байт 0:      Код команды (CMD)
Байты 1-2:   Смещение (Offset) в буфере данных (little-endian: lo, hi)
Байт 3:      Длина блока данных в текущем пакете (до 56 байт)
Байты 4-5:   Контрольная сумма (16-битная сумма всех 63 байтов пакета)
Байт 6:      Резерв (0x00)
Байты 7..62: Полезная нагрузка (цвета RGB, настройки, команды экрана)
```

### Основные команды:
| Код | Имя команды | Описание |
|---|---|---|
| `0x14` | `CMD_GET_DDATA` | Чтение глобальных параметров подсветки (режим, яркость, скорость, таймауты) |
| `0x15` | `CMD_SET_DATA` | Запись глобальных параметров подсветки |
| `0x19` | `CMD_GET_LIGHT` | Чтение текущей матрицы цветов клавиш (384 байта: 128 клавиш × 3 байта RGB) |
| `0x1A` | `CMD_SET_LIGHT` | Сохранение матрицы цветов клавиш во флеш-память клавиатуры |
| `0x1D` | `CMD_LIVE_SYNC` | Потоковая отправка цветов светодиодов в реальном времени (для музыки / анимаций) |
| `0x1E` | `CMD_CLOSE_SYNC` | Выход из режима потоковой анимации |
| `0x20` | `CMD_RESET` | Сброс к заводским настройкам |
| `0x40` | `CMD_SCREEN_INFO` | Инициализирующий пакет управления TFT-экраном (Magic `0xA5 0x5A`) |
| `0x41` | `CMD_SCREEN_DATA` | Пакет передачи данных дисплея (RGB565, время, дата) |
| `0x42` | `CMD_SCREEN_FINISH`| Завершение пакета управления экраном |

---

## 📁 Структура проекта

```text
├── hator_keyboard/          # Исходный код пакета Python
│   ├── __init__.py          # Экспорт основного API библиотеки
│   ├── __main__.py          # Запуск через python -m hator_keyboard
│   ├── cli.py               # Консольная утилита (hator / hator-keyboard)
│   ├── constants.py         # Карты клавиш, коды команд, VID/PID
│   ├── keyboard.py          # Основной класс HatorKeyboard и протокол HID
│   ├── screen.py            # Модуль экрана TFT (HUD мониторинг, RGB565)
│   ├── py.typed             # Маркер поддержки типов (PEP 561)
│   └── udev/
│       └── 99-hator.rules   # Встроенные правила udev для пакета
├── examples.py              # Готовые примеры использования
├── 99-hator.rules           # Правила udev для ручной установки
├── pyproject.toml           # Метаданные пакета и конфигурация pip (PEP 517/621)
├── setup.py                 # Shim для обратной совместимости сборки
├── LICENSE                  # Лицензия MIT
└── README.md                # Документация проекта
```

---

## 📜 Лицензия

Проект распространяется под лицензией [MIT](LICENSE).
