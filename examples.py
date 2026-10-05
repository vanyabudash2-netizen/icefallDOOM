"""
Примеры использования библиотеки hator_keyboard для управления подсветкой
"""

import time
import math
from hator_keyboard import HatorKeyboard, KEY_MAP


def example_simple_colors():
    """Пример 1: Установка цветов для отдельных клавиш (WASD, стрелки, модификаторы)"""
    print("--- Пример 1: Настройка индивидуальной подсветки клавиш ---")
    
    with HatorKeyboard() as kbd:
        # Устанавливаем максимальную яркость
        kbd.set_brightness(4)
        
        # 1. Заливаем всю клавиатуру мягким темно-синим фоном
        kbd.set_all_keys((0, 15, 45))
        
        # 2. Подсвечиваем клавиши WASD ярко-красным
        kbd.set_keys_color({
            "w": "red",
            "a": "red",
            "s": "red",
            "d": "red",
        })
        
        # 3. Подсвечиваем стрелки желтым
        kbd.fill_group("arrows", "yellow")
        
        # 4. Выделяем важные клавиши отдельными цветами
        kbd.set_key_color("space", "green")
        kbd.set_key_color("esc", "cyan")
        kbd.set_key_color("enter", "magenta")
        
        # 5. Сохраняем и применяем на клавиатуре
        kbd.apply()
        print("Подсветка успешно сохранена на клавиатуре!")


def example_builtin_modes():
    """Пример 2: Переключение встроенных эффектов (Волна, Дыхание, Спектр и др.)"""
    print("--- Пример 2: Переключение встроенных режимов ---")
    
    with HatorKeyboard() as kbd:
        # Включаем режим 'wave' (Волна)
        print("Включаем режим 'wave' (Волна)...")
        kbd.set_mode("wave", brightness=4, speed=3)
        time.sleep(3)
        
        # Включаем режим 'breathing' (Дыхание)
        print("Включаем режим 'breathing' (Дыхание)...")
        kbd.set_mode("breathing", brightness=4, speed=2)
        time.sleep(3)
        
        # Включаем статический бирюзовый цвет
        print("Включаем постоянный цвет (бирюзовый)...")
        kbd.set_static_color("#00FFAA", brightness=4)


def example_live_animation():
    """Пример 3: Потоковая плавная анимация в реальном времени (live streaming)"""
    print("--- Пример 3: Потоковая анимация волны (3 секунды) ---")
    
    with HatorKeyboard() as kbd:
        start_time = time.time()
        while time.time() - start_time < 3.0:
            t = time.time() * 3.0
            colors = [0] * kbd.TOTAL_BYTES
            
            for key_name, idx in KEY_MAP.items():
                # Синусоидальная бегущая волна
                val = (math.sin(idx * 0.15 + t) + 1.0) / 2.0
                r = int(210 * val) + 24
                g = int(40 * (1.0 - val)) + 15
                b = int(210 * (1.0 - val)) + 24
                
                colors[idx * 3] = r
                colors[idx * 3 + 1] = g
                colors[idx * 3 + 2] = b
            
            # Populate auxiliary position 65 next to Left Shift (64)
            colors[65 * 3] = colors[64 * 3]
            colors[65 * 3 + 1] = colors[64 * 3 + 1]
            colors[65 * 3 + 2] = colors[64 * 3 + 2]

            # Отправка кадра в реальном времени напрямую на светодиоды
            kbd.stream_frame(colors)
            time.sleep(0.02)  # ~50 кадров в секунду
            
        kbd.close_stream()
        print("Потоковая анимация завершена.")


def example_cpu_monitor():
    """Пример 4: Индикатор загрузки процессора на цифровом ряду (клавиши 1..0)"""
    print("--- Пример 4: Индикатор нагрузки процессора (нажмите Ctrl+C для выхода) ---")
    try:
        import psutil
    except ImportError:
        print("Для этого примера установите psutil: pip install psutil")
        return

    num_keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    
    with HatorKeyboard() as kbd:
        try:
            while True:
                cpu = psutil.cpu_percent(interval=0.5)
                # Количество горящих клавиш от 0 до 10
                active_count = int(round(cpu / 10.0))
                
                # Фоновый цвет для всех клавиш
                kbd.set_all_keys((5, 5, 20))
                
                # Подсвечиваем клавиши 1..0 в зависимости от нагрузки
                for i, key in enumerate(num_keys):
                    if i < active_count:
                        # Градиент: зеленый -> желтый -> красный
                        if i < 4:
                            color = (0, 255, 0)
                        elif i < 7:
                            color = (255, 200, 0)
                        else:
                            color = (255, 0, 0)
                        kbd.set_key_color(key, color)
                
                # Применяем в реальном времени
                kbd.stream_frame()
                print(f"Загрузка CPU: {cpu:5.1f}% | Активно диодов: {active_count:2d}/10", end="\r")
        except KeyboardInterrupt:
            kbd.close_stream()
            print("\nМониторинг остановлен.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and "demo" in sys.argv[1].lower():
        example_live_animation()
    else:
        example_simple_colors()
