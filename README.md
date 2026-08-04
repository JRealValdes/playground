# playground

Playground repository for miscellaneous scripts.

Managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
uv sync
```

## Keep awake

Impide la suspensión de Windows con `SetThreadExecutionState`.

```bash
# Por defecto: cada 30s durante 60 min (sistema + pantalla)
uv run keep-awake

# Cada 45s durante 2 horas
uv run keep-awake --interval 45 --duration 120

# Cada 20s hasta Ctrl+C
uv run keep-awake -i 20 -d 0

# Sistema despierto pero permitiendo apagar la pantalla
uv run keep-awake --allow-display-off
```
