"""Mueve el ratón periódicamente para evitar que el ordenador se duerma."""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
from ctypes import wintypes
from datetime import datetime, timedelta


user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def get_cursor_pos() -> tuple[int, int]:
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        raise OSError("No se pudo leer la posición del ratón")
    return point.x, point.y


def set_cursor_pos(x: int, y: int) -> None:
    if not user32.SetCursorPos(x, y):
        raise OSError("No se pudo mover el ratón")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Mueve el ratón 1 píxel (alternando izquierda/derecha) "
            "cada cierto intervalo para mantener el PC despierto."
        ),
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=30,
        metavar="SECONDS",
        help="Segundos entre cada movimiento (default: 30)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60,
        metavar="MINUTES",
        help="Minutos totales despierto. 0 = indefinido hasta Ctrl+C (default: 60)",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval debe ser mayor que 0")
    if args.duration < 0:
        parser.error("--duration no puede ser negativo")

    return args


def format_elapsed(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main() -> int:
    args = parse_args()
    start = datetime.now()
    end = None if args.duration == 0 else start + timedelta(minutes=args.duration)
    direction = 1
    move_count = 0

    print()
    print("=== Keep Awake ===")
    print(f"Intervalo : cada {args.interval:g} segundo(s)")
    if end is None:
        print("Duración  : indefinida (Ctrl+C para parar)")
    else:
        print(f"Duración  : {args.duration:g} minuto(s) (hasta {end.strftime('%H:%M:%S')})")
    print("Pulsa Ctrl+C para detener antes de tiempo.")
    print()

    try:
        while True:
            now = datetime.now()
            if end is not None and now >= end:
                elapsed = format_elapsed((now - start).total_seconds())
                print(f"[{elapsed}] Tiempo total alcanzado. Deteniendo.")
                break

            x, y = get_cursor_pos()
            new_x = x + direction
            set_cursor_pos(new_x, y)

            move_count += 1
            direction_label = "derecha" if direction == 1 else "izquierda"
            elapsed = format_elapsed((datetime.now() - start).total_seconds())
            print(
                f"[{elapsed}] Movimiento #{move_count} → 1 px a la "
                f"{direction_label} (x: {x} → {new_x})"
            )
            direction = -direction

            if end is None:
                time.sleep(args.interval)
            else:
                remaining = (end - datetime.now()).total_seconds()
                if remaining <= 0:
                    continue
                time.sleep(min(args.interval, remaining))
    except KeyboardInterrupt:
        print()
        elapsed = format_elapsed((datetime.now() - start).total_seconds())
        print(f"[{elapsed}] Cancelado por el usuario.")
    finally:
        print()
        print(f"Listo. Total de movimientos: {move_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
