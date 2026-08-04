"""Mantiene el ordenador despierto vía SetThreadExecutionState (API de Windows)."""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
from datetime import datetime, timedelta


kernel32 = ctypes.windll.kernel32

# https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
ES_SYSTEM_REQUIRED = 0x00000001


def set_execution_state(flags: int) -> int:
    """Informa a Windows de que el sistema (y opcionalmente la pantalla) deben seguir activos."""
    previous = kernel32.SetThreadExecutionState(flags)
    if previous == 0:
        raise OSError("SetThreadExecutionState falló")
    return previous


def prevent_sleep(*, keep_display: bool) -> None:
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if keep_display:
        flags |= ES_DISPLAY_REQUIRED
    set_execution_state(flags)


def allow_sleep() -> None:
    """Restaura el comportamiento normal de suspensión."""
    set_execution_state(ES_CONTINUOUS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Impide que Windows suspenda el PC usando SetThreadExecutionState.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=30,
        metavar="SECONDS",
        help="Segundos entre cada refresco del estado (default: 30)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60,
        metavar="MINUTES",
        help="Minutos totales despierto. 0 = indefinido hasta Ctrl+C (default: 60)",
    )
    parser.add_argument(
        "--allow-display-off",
        action="store_true",
        help="Permite apagar la pantalla; el sistema sigue sin suspenderse",
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
    tick_count = 0
    keep_display = not args.allow_display_off

    print()
    print("=== Keep Awake ===")
    print(f"Intervalo : cada {args.interval:g} segundo(s)")
    if end is None:
        print("Duración  : indefinida (Ctrl+C para parar)")
    else:
        print(f"Duración  : {args.duration:g} minuto(s) (hasta {end.strftime('%H:%M:%S')})")
    print(f"Pantalla  : {'encendida' if keep_display else 'puede apagarse'}")
    print("Pulsa Ctrl+C para detener antes de tiempo.")
    print()

    try:
        prevent_sleep(keep_display=keep_display)
        print("[00:00:00] Windows informado: no suspender.")

        while True:
            now = datetime.now()
            if end is not None and now >= end:
                elapsed = format_elapsed((now - start).total_seconds())
                print(f"[{elapsed}] Tiempo total alcanzado. Deteniendo.")
                break

            # Reafirmar periódicamente (más fiable en algunos equipos / Modern Standby)
            prevent_sleep(keep_display=keep_display)
            tick_count += 1
            elapsed = format_elapsed((datetime.now() - start).total_seconds())
            print(f"[{elapsed}] Refresco #{tick_count}: sistema mantenido despierto")

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
        try:
            allow_sleep()
            print("Comportamiento normal de suspensión restaurado.")
        except OSError as exc:
            print(f"No se pudo restaurar el estado de suspensión: {exc}", file=sys.stderr)
        print()
        print(f"Listo. Total de refrescos: {tick_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
