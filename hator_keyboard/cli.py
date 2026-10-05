"""
Command-line interface (CLI) for Hator Keyboard RGB Controller.
"""

import sys
import time
import math
import argparse
import subprocess
from pathlib import Path

from .constants import KEY_MAP, GROUPS, MODES, UDEV_RULES_CONTENT
from .keyboard import HatorKeyboard


def setup_udev_action(args):
    """Handle setup-udev command."""
    if args.print:
        print(UDEV_RULES_CONTENT.strip())
        return

    if args.install:
        rules_path = Path("/etc/udev/rules.d/99-hator.rules")
        try:
            print(f"Попытка записи правил udev в {rules_path}...")
            # Try direct write first (works if run as root or in user group)
            rules_path.write_text(UDEV_RULES_CONTENT)
            print("Файл правил успешно записан напрямую.")
            subprocess.run(["udevadm", "control", "--reload-rules"], check=False)
            subprocess.run(["udevadm", "trigger"], check=False)
            print("Правила udev успешно применены!")
            return
        except PermissionError:
            # Fall back to sudo
            print("Требуются повышенные привилегии. Вызов sudo...")
            try:
                proc = subprocess.run(
                    ["sudo", "tee", str(rules_path)],
                    input=UDEV_RULES_CONTENT.encode("utf-8"),
                    stdout=subprocess.DEVNULL,
                    check=True
                )
                subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)
                subprocess.run(["sudo", "udevadm", "trigger"], check=True)
                print(f"Правила udev успешно установлены в {rules_path} и применены!")
                return
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Не удалось автоматически установить правила: {e}", file=sys.stderr)
                print("Выполните установку вручную следующими командами:\n")

    print("Настройка прав доступа (udev) для Linux:")
    print("1. Создайте файл правил /etc/udev/rules.d/99-hator.rules:")
    print("   echo '" + UDEV_RULES_CONTENT.strip().replace("'", "'\\''") + "' | sudo tee /etc/udev/rules.d/99-hator.rules")
    print("2. Перезагрузите правила udev:")
    print("   sudo udevadm control --reload-rules && sudo udevadm trigger")
    print("\nЛибо используйте флаг автоматической установки:")
    print("   hator setup-udev --install")
    print("\nПосле этого клавиатура будет доступна обычному пользователю без sudo.")


def main(argv=None):
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="hator",
        description="Управление подсветкой и экраном клавиатуры Hator Icefall PRO"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    # Command: list-keys
    subparsers.add_parser("list-keys", help="Показать список доступных названий клавиш")

    # Command: list-modes
    subparsers.add_parser("list-modes", help="Показать список встроенных режимов подсветки")

    # Command: mode
    p_mode = subparsers.add_parser("mode", help="Включить встроенный режим подсветки")
    p_mode.add_argument("name", help="Название режима (wave, static, breathing, etc.) или номер")
    p_mode.add_argument("-b", "--brightness", type=int, choices=range(0, 5), default=4, help="Яркость (0..4)")
    p_mode.add_argument("-s", "--speed", type=int, choices=range(0, 5), default=2, help="Скорость (0..4)")

    # Command: static
    p_static = subparsers.add_parser("static", help="Включить постоянную подсветку одним цветом")
    p_static.add_argument("color", help="Цвет (название: red, green, blue, etc. или hex: #FF5500)")
    p_static.add_argument("-b", "--brightness", type=int, choices=range(0, 5), default=4, help="Яркость (0..4)")

    # Command: off
    subparsers.add_parser("off", help="Выключить подсветку")

    # Command: wasd
    p_wasd = subparsers.add_parser("wasd", help="Игровой профиль: подсветить WASD и остальные клавиши")
    p_wasd.add_argument("--wasd", default="red", help="Цвет для клавиш WASD (по умолчанию: red)")
    p_wasd.add_argument("--arrows", default="yellow", help="Цвет для стрелок (по умолчанию: yellow)")
    p_wasd.add_argument("--others", default="#001533", help="Цвет для остальных клавиш (по умолчанию: темно-синий)")

    # Command: set-key
    p_key = subparsers.add_parser("set-key", help="Установить цвет конкретной клавиши")
    p_key.add_argument("key", help="Имя клавиши (esc, w, space, enter, etc.)")
    p_key.add_argument("color", help="Цвет (hex или имя)")

    # Command: demo
    subparsers.add_parser("demo", help="Запустить демонстрационную анимацию")

    # Command: setup-udev
    p_udev = subparsers.add_parser("setup-udev", help="Инструкция и настройка прав доступа udev в Linux")
    p_udev.add_argument("--install", action="store_true", help="Автоматически установить правила в /etc/udev/rules.d/ (потребуются права sudo)")
    p_udev.add_argument("--print", action="store_true", help="Вывести содержимое правил udev в stdout")

    # Command: sleep-timeout
    p_sleep = subparsers.add_parser("sleep-timeout", help="Настроить время до отключения подсветки / сна (в минутах)")
    p_sleep.add_argument("--wired", type=int, default=10, help="Время отключения подсветки по проводу (минут, по умолчанию: 10)")
    p_sleep.add_argument("--wireless-backlight", type=int, default=2, help="Время отключения подсветки по 2.4G/BT (минут, по умолчанию: 2)")
    p_sleep.add_argument("--wireless-sleep", type=int, default=10, help="Время глубокого сна по 2.4G/BT (минут, по умолчанию: 10)")

    # TFT Screen Commands
    subparsers.add_parser("screen-wake", help="Разбудить экран TFT, перейти на главный экран и синхронизировать время")
    subparsers.add_parser("screen-home", help="Переключить экран TFT на главный экран (Home)")
    subparsers.add_parser("screen-pic", help="Переключить экран TFT на страницу картинки")
    subparsers.add_parser("screen-gif", help="Переключить экран TFT на страницу GIF-анимации")
    subparsers.add_parser("screen-sync", help="Синхронизировать время и дату на экране TFT")

    p_img = subparsers.add_parser("screen-image", help="Загрузить изображение (PNG, JPG, BMP) на экран TFT")
    p_img.add_argument("path", help="Путь к файлу изображения")

    subparsers.add_parser("screen-hud", help="Вывести текущий системный монитор (CPU, RAM, Temp, Clock) на экран TFT")

    p_live = subparsers.add_parser("screen-hud-live", help="Запустить постоянный монитор системы в реальном времени")
    p_live.add_argument("-i", "--interval", type=int, default=3, help="Интервал обновления в секундах (по умолчанию: 3)")

    # Command: reset
    subparsers.add_parser("reset", help="Сбросить клавиатуру до заводских настроек (factory reset)")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    if args.command == "setup-udev":
        setup_udev_action(args)
        return

    if args.command == "list-keys":
        print("Доступные имена клавиш:")
        keys_sorted = sorted(KEY_MAP.items(), key=lambda x: x[1])
        seen = set()
        for name, idx in keys_sorted:
            if idx not in seen:
                aliases = [k for k, v in KEY_MAP.items() if v == idx]
                print(f"  [{idx:2d}] {' / '.join(aliases)}")
                seen.add(idx)
        print("\nГруппы клавиш:")
        for gname in GROUPS.keys():
            print(f"  @{gname}")
        return

    if args.command == "list-modes":
        print("Доступные режимы подсветки:")
        for mid, (mname, desc) in sorted(MODES.items()):
            print(f"  {mid:2d}: {mname:<12} ({desc})")
        return

    try:
        with HatorKeyboard() as kbd:
            if args.command == "sleep-timeout":
                kbd.set_sleep_timeout(
                    wired_minutes=args.wired,
                    wireless_backlight_minutes=args.wireless_backlight,
                    wireless_sleep_minutes=args.wireless_sleep,
                )
                print(f"Таймауты сна обновлены: провод={args.wired} мин, беспроводная подсветка={args.wireless_backlight} мин, беспроводной сон={args.wireless_sleep} мин.")

            elif args.command == "screen-wake":
                kbd.screen_wake()
                print("Экран TFT разбужен, переключен на главный экран и время синхронизировано.")

            elif args.command == "screen-home":
                kbd.screen_home()
                print("Экран TFT переключен на главный экран (Home).")

            elif args.command == "screen-pic":
                kbd.screen_picture()
                print("Экран TFT переключен на страницу картинки.")

            elif args.command == "screen-gif":
                kbd.screen_gif()
                print("Экран TFT переключен на страницу GIF.")

            elif args.command == "screen-sync":
                kbd.screen_sync_time()
                print("Время и дата успешно синхронизированы с экраном TFT.")

            elif args.command == "screen-image":
                print(f"Загрузка изображения '{args.path}' на экран клавиатуры...")
                kbd.upload_screen_image(args.path)
                print("Изображение успешно загружено и отображается на экране!")

            elif args.command == "screen-hud":
                print("Сбор системной информации и вывод на экран...")
                kbd.update_system_hud()
                print("Системный монитор успешно отображен на экране!")

            elif args.command == "screen-hud-live":
                print(f"Запущен системный монитор в реальном времени (интервал: {args.interval} сек).")
                print("Нажмите Ctrl+C для остановки...")
                try:
                    while True:
                        kbd.update_system_hud()
                        time.sleep(max(1, args.interval))
                except KeyboardInterrupt:
                    print("\nМонитор остановлен.")

            elif args.command == "reset":
                kbd.reset_keyboard()
                print("Клавиатура сброшена до заводских настроек (reset).")

            elif args.command == "off":
                kbd.turn_off()
                print("Подсветка выключена.")

            elif args.command == "mode":
                kbd.set_mode(args.name, brightness=args.brightness, speed=args.speed)
                print(f"Режим переключен на: {args.name} (яркость: {args.brightness}, скорость: {args.speed})")

            elif args.command == "static":
                kbd.set_static_color(args.color, brightness=args.brightness)
                print(f"Установлен статический цвет: {args.color} (яркость: {args.brightness})")

            elif args.command == "wasd":
                kbd.set_all_keys(args.others)
                kbd.fill_group("wasd", args.wasd)
                kbd.fill_group("arrows", args.arrows)
                kbd.set_key_color("space", "green")
                kbd.set_key_color("esc", "cyan")
                kbd.set_key_color("enter", "magenta")
                kbd.apply()
                print(f"Применен игровой профиль (WASD: {args.wasd}, Arrows: {args.arrows}, Остальные: {args.others})")

            elif args.command == "set-key":
                kbd.set_key_color(args.key, args.color)
                kbd.apply()
                print(f"Клавиша '{args.key}' установлена в цвет {args.color}")

            elif args.command == "demo":
                print("Запуск плавной RGB демо-анимации (нажмите Ctrl+C для выхода)...")
                try:
                    t = 0
                    while True:
                        colors = [0] * kbd.TOTAL_BYTES
                        for key_name, idx in KEY_MAP.items():
                            hue = (idx * 5 + t * 40) % 360
                            rad = math.radians(hue)
                            r = int(127 * (math.sin(rad) + 1))
                            g = int(127 * (math.sin(rad + 2 * math.pi / 3) + 1))
                            b = int(127 * (math.sin(rad + 4 * math.pi / 3) + 1))
                            colors[idx * 3] = r
                            colors[idx * 3 + 1] = g
                            colors[idx * 3 + 2] = b
                        kbd.stream_frame(colors)
                        t += 0.05
                        time.sleep(0.03)
                except KeyboardInterrupt:
                    print("\nДемо остановлено.")
                    kbd.close_stream()
    except (ConnectionError, PermissionError, TimeoutError, ValueError, ImportError) as err:
        print(f"\n[Ошибка] {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
