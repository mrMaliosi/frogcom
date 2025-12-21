#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.markup import escape

console = Console()


STEP_RE = re.compile(r"---\s*STEP\s*(\d+|final)\s*---")
TRACE_RE = re.compile(r"TRACE START:\s*(.+)")


def extract_json_block(lines: List[str], start_idx: int) -> tuple[Optional[Dict[str, Any]], int]:
    """
    Берёт строки от start_idx до ПЕРВОГО разделителя (STEP/TRACE),
    которые выглядят как JSON-объект, и парсит их целиком.
    """
    buf: List[str] = []
    i = start_idx

    while i < len(lines):
        line = lines[i]
        # стоп, если начался следующий STEP или TRACE
        if STEP_RE.match(line.strip()) or "TRACE START:" in line:
            break
        buf.append(line)
        i += 1

    # выкинуть ведущие/хвостовые пустые строки
    while buf and not buf[0].strip():
        buf.pop(0)
    while buf and not buf[-1].strip():
        buf.pop()

    if not buf:
        return None, i

    text = "\n".join(buf)
    try:
        return json.loads(text), i
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON error in block starting at line {start_idx+1}: {e}[/]")
        return None, i


def parse_trace_file(text: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    blocks: List[Dict[str, Any]] = []
    current_trace_id: Optional[str] = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # TRACE START
        if "TRACE START:" in line:
            m = TRACE_RE.search(line)
            current_trace_id = m.group(1).strip() if m else None

            # пропускаем любую "рамку" ==== и пустые строки до реального JSON
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("{"):
                i += 1

            obj, i = extract_json_block(lines, i)
            if obj:
                blocks.append({"trace_id": current_trace_id, "kind": "start", "data": obj})
            continue

        # STEP
        m_step = STEP_RE.match(line.strip())
        if m_step:
            step_num = m_step.group(1)

            i += 1
            # аналогично: пропустить пустые/рамочные строки до JSON
            while i < len(lines) and not lines[i].lstrip().startswith("{"):
                i += 1

            obj, i = extract_json_block(lines, i)
            if obj:
                obj["step_num"] = step_num
                blocks.append({"trace_id": current_trace_id, "kind": "step", "data": obj})
            continue

        i += 1

    return blocks


def shorten(text: str, limit: int = 200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def print_trace(blocks: List[Dict[str, Any]]) -> None:
    if not blocks:
        console.print("[red]Нет распарсенных блоков[/]")
        return

    console.print(blocks[0])

    start = blocks[0]
    trace_id = start["trace_id"]
    data = start["data"]

    prompt = data.get("user_prompt", "N/A")
    ts = data.get("timestamp", "N/A")
    orch = data.get("orchestration_enabled", False)

    console.print(Panel.fit(
        f"[bold cyan]TRACE ID[/]: {escape(str(trace_id))}\n"
        f"[blue]Time[/]: {ts}\n"
        f"[yellow]Orchestration[/]: {'✅ Enabled' if orch else '❌ Disabled'}",
        title="TRACE START",
        border_style="cyan",
    ))

    console.print(Panel(
        escape(str(prompt)),
        title="USER PROMPT",
        border_style="green",
    ))

    step_blocks = [b for b in blocks if b["kind"] == "step"]
    if step_blocks:
        table = Table(title="Шаги", box=box.ROUNDED)
        table.add_column("Шаг", style="cyan", no_wrap=True)
        table.add_column("Тип", style="magenta")
        table.add_column("Время", style="green")
        table.add_column("Превью", style="white")

        for b in step_blocks:
            s = b["data"]
            step_num = str(s.get("step_num", s.get("step", "?")))
            stype = s.get("type", "unknown")
            ts = s.get("timestamp", "N/A")

            if stype == "primary_response":
                content = s.get("response", "")
            elif stype == "secondary_guidance":
                content = s.get("guidance", "")
            elif stype == "final_response":
                content = s.get("final_response", "")
            else:
                content = str(s)

            table.add_row(
                step_num,
                stype,
                ts,
                escape(content),
            )

        console.print(table)

    final = next(
        (
            b for b in step_blocks
            if b["data"].get("step") == "final"
            or b["data"].get("step_num") == "final"
        ),
        None,
    )
    if final:
        s = final["data"]
        content = s.get("final_response") or s.get("response") or ""
        console.print(Panel(
            escape(content),
            title="FINAL RESPONSE",
            border_style="yellow",
        ))


def main() -> None:
    if len(sys.argv) != 2:
        console.print("[red]Usage: python logs_parser.py <file>[/]")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        console.print(f"[red]Файл не найден: {path}[/]")
        sys.exit(1)

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    blocks = parse_trace_file(text)
    console.print(f"[green]Найдено блоков: {len(blocks)}[/]")
    print_trace(blocks)


if __name__ == "__main__":
    main()
