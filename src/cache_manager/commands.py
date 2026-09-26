"""Rich-powered CLI commands for TickerTape cache management."""

from __future__ import annotations

import argparse
import asyncio
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm
from rich.table import Table

from cache_manager import core

default_console = Console()


def handle_status(args: argparse.Namespace, console: Console = default_console) -> None:
    """Display rich tables summarizing cached sitemaps and the ISIN database."""
    with console.status("[bold cyan]Scanning cache directory..."):
        status = core.get_cache_status(cache_dir=args.cache_dir)

    console.print(
        Panel(
            f"[bold]Cache Directory:[/] [cyan]{status['cache_dir']}[/]",
            title="[bold yellow]TickerTape Cache Manager[/]",
            expand=False,
        )
    )

    # Sitemaps Table
    sitemap_table = Table(
        title="Sitemaps Cache (JSON)",
        header_style="bold magenta",
        show_lines=True,
    )
    sitemap_table.add_column("Category", style="cyan", no_wrap=True)
    sitemap_table.add_column("Status", justify="center")
    sitemap_table.add_column("Records", justify="right")
    sitemap_table.add_column("File Size", justify="right")
    sitemap_table.add_column("Last Fetched (UTC)", style="dim")

    for cat, info in status["sitemaps"].items():
        if info.get("cached"):
            if "error" in info:
                status_text = "[bold red]Corrupted[/]"
                count_text = "[dim]-[/]"
                size_text = "[dim]-[/]"
                date_text = "[dim]-[/]"
            else:
                status_text = "[bold green]Cached[/]"
                count_text = f"[bold]{info['count']:,}[/]"
                size_text = f"{info['size_kb']} KB"
                date_text = info.get("fetched_at", "N/A")
        else:
            status_text = "[dim red]Missing[/]"
            count_text = "[dim]-[/]"
            size_text = "[dim]-[/]"
            date_text = "[dim]Never[/]"

        sitemap_table.add_row(cat, status_text, count_text, size_text, date_text)

    console.print(sitemap_table)

    # SQLite ISIN Database Table
    db = status["isin_db"]
    db_table = Table(
        title="ISIN Lookup Engine (SQLite)",
        header_style="bold blue",
        show_lines=True,
    )
    db_table.add_column("Property", style="bold")
    db_table.add_column("Value")

    db_status = "[bold green]Ready[/]" if db["exists"] else "[bold red]Not Initialized[/]"
    db_table.add_row("Database Status", db_status)
    db_table.add_row("Indexed Funds", f"[bold cyan]{db['records']:,}[/] records")
    db_table.add_row("File Size", f"{db['size_kb']} KB")
    db_table.add_row("File Path", f"[dim]{db['path']}[/]")

    console.print(db_table)


def handle_build(args: argparse.Namespace, console: Console = default_console) -> None:
    """Build or refresh caches with interactive spinners and progress bars."""
    if args.target == "sitemap":
        with console.status(
            f"[bold cyan]Fetching & parsing XML sitemap for [bold yellow]'{args.category}'[/] (force={args.force})..."
        ):
            count = asyncio.run(
                core.build_sitemap_cache(
                    category=args.category,
                    force=args.force,
                    cache_dir=args.cache_dir,
                )
            )
        console.print(
            f"[bold green]✔[/] Successfully cached [bold]{count:,}[/] URLs for [cyan]'{args.category}'[/]!"
        )

    elif args.target == "index":
        console.print(
            Panel(
                f"[bold]Target:[/] Mutual Funds ISIN Database\n"
                f"[bold]Concurrency:[/] {args.concurrency} workers | [bold]Delay:[/] {args.delay}s | "
                f"[bold]Limit:[/] {args.limit or 'All'}",
                title="[bold green]Building ISIN Index[/]",
                expand=False,
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=35),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("[cyan]Crawling & indexing funds...", total=None)

            def on_progress(completed: int, total: int, successful: int, failed: int) -> None:
                if progress.tasks[task_id].total is None or progress.tasks[task_id].total != total:
                    progress.update(task_id, total=total)

                progress.update(
                    task_id,
                    completed=completed,
                    description=(
                        f"[cyan]Indexing:[/] [bold]{completed}/{total}[/] "
                        f"([green]✔ {successful}[/] [red]✖ {failed}[/])"
                    ),
                )

            indexed_count = asyncio.run(
                core.build_isin_index(
                    force=args.force,
                    concurrency=args.concurrency,
                    delay=args.delay,
                    limit=args.limit,
                    progress_callback=on_progress,
                    cache_dir=args.cache_dir,
                )
            )

        console.print(
            f"\n[bold green]✔[/] Indexing complete: [bold cyan]{indexed_count}[/] funds recorded in SQLite."
        )


def handle_clear(args: argparse.Namespace, console: Console = default_console) -> None:
    """Clear cache with safety confirmation."""
    if not args.yes:
        target_name = f"'{args.category}' sitemap" if args.category else f"all '{args.target}' cache"
        confirmed = Confirm.ask(
            f"[bold yellow]?[/] Are you sure you want to purge [bold red]{target_name}[/]?",
            console=console,
        )
        if not confirmed:
            console.print("[dim]Operation cancelled.[/]")
            return

    with console.status(f"[bold red]Purging cache target '{args.target}'..."):
        core.clear_cache(
            target=args.target,
            category=args.category,
            cache_dir=args.cache_dir,
        )

    console.print(f"[bold green]✔[/] Successfully purged [bold]{args.target}[/] cache.")


def create_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--cache-dir",
        default=".cache/tickertape",
        help="Path to cache directory (default: .cache/tickertape)",
    )

    parser = argparse.ArgumentParser(
        prog="cache-manager",
        parents=[parent_parser],
        description="CLI tool to manage and build TickerTape caches with Rich.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: status
    subparsers.add_parser(
        "status",
        parents=[parent_parser],
        help="Show overview of cached sitemaps and ISIN SQLite store",
    )

    # Subcommand: build
    build_parser = subparsers.add_parser(
        "build",
        parents=[parent_parser],
        help="Build or refresh cache entries",
    )
    build_parser.add_argument(
        "target",
        choices=["sitemap", "index"],
        help="Target to build: 'sitemap' (JSON URLs) or 'index' (ISIN SQLite DB)",
    )
    build_parser.add_argument(
        "--category",
        default="mf",
        choices=["mf", "stocks", "etf", "us-stocks", "us-etf"],
        help="Sitemap category (default: mf)",
    )
    build_parser.add_argument("--force", action="store_true", help="Bypass local cache and re-crawl")
    build_parser.add_argument("--concurrency", type=int, default=5, help="Concurrent workers (default: 5)")
    build_parser.add_argument("--delay", type=float, default=0.5, help="Per-worker delay in seconds (default: 0.5)")
    build_parser.add_argument("--limit", type=int, default=None, help="Max items to process (for testing)")

    # Subcommand: clear
    clear_parser = subparsers.add_parser(
        "clear",
        parents=[parent_parser],
        help="Clear cached sitemaps or SQLite database",
    )
    clear_parser.add_argument(
        "--target",
        choices=["all", "sitemap", "isin"],
        default="all",
        help="Cache target to remove (default: all)",
    )
    clear_parser.add_argument("--category", default=None, help="Specific sitemap category to delete")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    return parser


def main(argv: Optional[list[str]] = None, console: Console = default_console) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "status":
            handle_status(args, console=console)
        elif args.command == "build":
            handle_build(args, console=console)
        elif args.command == "clear":
            handle_clear(args, console=console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user. Exiting.[/]")
    except Exception as exc:
        console.print(f"[bold red]Error:[/] {exc}")


if __name__ == "__main__":
    main()
