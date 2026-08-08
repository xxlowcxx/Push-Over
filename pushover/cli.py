"""Push Over CLI."""
from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pushover import __codename__, __tagline__, __version__
from pushover.audit import log
from pushover.detect import detect
from pushover.paths import BURN_BOX_URL, PHOENIX, PLAYBOOKS, QUARANTINE, ROOT
from pushover.playbook import write_playbooks
from pushover.pull_adb import pull_adb
from pushover.pull_mtp import pull_mtp
from pushover.wrap import load_case, new_case, save_case, seal_case

console = Console()


def _banner() -> None:
    console.print(
        Panel.fit(
            f"[bold magenta]{__codename__}[/] v{__version__}\n"
            f"[dim]{__tagline__}[/]\n"
            f"[cyan]Owner: LowC · Powered by Siren Logix · Toolaid[/]",
            border_style="magenta",
        )
    )


@click.group()
@click.version_option(__version__, prog_name="pushover")
def main() -> None:
    """Push Over — multi-path Android service with secure wrap."""
    pass


@main.command("doctor")
def doctor_cmd() -> None:
    _banner()
    import shutil

    rows = [
        ("ROOT", str(ROOT), ROOT.is_dir()),
        ("quarantine", str(QUARANTINE), QUARANTINE.is_dir()),
        ("playbooks", str(PLAYBOOKS), True),
        ("PhoenixWrap", str(PHOENIX), PHOENIX.is_dir()),
        ("Burn Box URL", BURN_BOX_URL, True),
        ("adb", shutil.which("adb") or "missing", bool(shutil.which("adb"))),
        ("heimdall", shutil.which("heimdall") or "missing", bool(shutil.which("heimdall"))),
        ("mtp-detect", shutil.which("mtp-detect") or "missing", bool(shutil.which("mtp-detect"))),
        ("jmtpfs", shutil.which("jmtpfs") or "missing", bool(shutil.which("jmtpfs"))),
    ]
    t = Table(title="Push Over doctor")
    t.add_column("Component")
    t.add_column("Value")
    t.add_column("OK")
    for n, v, ok in rows:
        t.add_row(n, str(v), "[green]yes[/]" if ok else "[yellow]no[/]")
    console.print(t)
    write_playbooks()
    console.print(f"[dim]playbooks written under {PLAYBOOKS}[/]")
    console.print("[green]Modes:[/] auto owner mtp adb download — no FRP bypass module")


@main.command("detect")
def detect_cmd() -> None:
    _banner()
    snap = detect()
    t = Table(title="Device detect")
    t.add_column("Field")
    t.add_column("Value")
    t.add_row("mode", snap.mode)
    t.add_row("serial", snap.serial or "—")
    t.add_row("product", snap.product or "—")
    t.add_row("vid:pid", snap.vid_pid or "—")
    t.add_row("adb", snap.adb_state or "—")
    console.print(t)
    for n in snap.notes:
        console.print(f"  • {n}")
    if snap.lsusb_lines:
        console.print("[dim]lsusb hits:[/]")
        for ln in snap.lsusb_lines:
            if any(x in ln for x in ("04e8", "18d1", "Samsung", "Google", "05ac", "Apple")):
                console.print(f"  {ln}")


@main.command("owner")
@click.option("--tech", default="siren")
@click.option("--note", default="")
@click.option("--ownership-note", default="owned / authorized service")
def owner_cmd(tech: str, note: str, ownership_note: str) -> None:
    """Proper FRP path: sign into previous Google account, then pull."""
    _banner()
    write_playbooks()
    snap = detect()
    case = new_case(
        "owner",
        tech=tech,
        note=note or "owner FRP path",
        ownership_note=ownership_note,
        serial=snap.serial,
        product=snap.product,
    )
    console.print(f"[green]CASE[/] {case.id}")
    console.print(Panel(f"Read: {PLAYBOOKS / 'owner-frp.md'}", title="Owner path"))
    console.print(
        "1) On the phone, complete Google/OEM account sign-in (proper free-path).\n"
        "2) Enable File transfer / USB debugging if needed.\n"
        f"3) Run: [bold]pushover mtp --case {case.id}[/]  or  [bold]pushover adb --case {case.id}[/]"
    )
    console.print(f"Case saved. Quarantine: {QUARANTINE / case.id}")


@main.command("mtp")
@click.option("--tech", default="siren")
@click.option("--note", default="")
@click.option("--ownership-note", default="owned / authorized service")
@click.option("--case", "case_id", default=None, help="Resume existing case")
@click.option("--phoenix/--no-phoenix", default=False)
@click.option("--burn-box/--no-burn-box", default=False)
def mtp_cmd(tech, note, ownership_note, case_id, phoenix, burn_box) -> None:
    """Pull reachable MTP files into secure wrap."""
    _banner()
    snap = detect()
    if case_id:
        case = load_case(case_id)
    else:
        case = new_case(
            "mtp",
            tech=tech,
            note=note or "mtp pull",
            ownership_note=ownership_note,
            serial=snap.serial,
            product=snap.product,
        )
    console.print(f"[green]CASE[/] {case.id}  mode={snap.mode}")
    result = pull_mtp(case, use_phoenix=phoenix, use_burn_box=burn_box)
    console.print_json(json.dumps(result, indent=2))
    if result.get("pulled", 0) > 0:
        seal = seal_case(case)
        console.print(f"[green]SEALED[/] {seal}  items={len(case.items)}")
    else:
        save_case(case)
        console.print("[yellow]No files pulled yet — unlock phone / File transfer / close KDE MTP lock[/]")


@main.command("adb")
@click.option("--tech", default="siren")
@click.option("--note", default="")
@click.option("--ownership-note", default="owned / authorized service")
@click.option("--case", "case_id", default=None)
@click.option("--phoenix/--no-phoenix", default=False)
@click.option("--burn-box/--no-burn-box", default=False)
def adb_cmd(tech, note, ownership_note, case_id, phoenix, burn_box) -> None:
    """Pull via authorized ADB."""
    _banner()
    snap = detect()
    if snap.mode not in ("adb",) and snap.adb_state != "device":
        console.print(f"[yellow]ADB not ready (mode={snap.mode}, state={snap.adb_state})[/]")
        console.print("Enable USB debugging and authorize this computer, or use: pushover owner")
    if case_id:
        case = load_case(case_id)
    else:
        case = new_case(
            "adb",
            tech=tech,
            note=note or "adb pull",
            ownership_note=ownership_note,
            serial=snap.serial,
            product=snap.product,
        )
    result = pull_adb(case, use_phoenix=phoenix, use_burn_box=burn_box)
    console.print_json(json.dumps(result, indent=2))
    if result.get("pulled", 0) > 0:
        seal = seal_case(case)
        console.print(f"[green]SEALED[/] {seal}")
    else:
        save_case(case)


@main.command("download")
@click.option("--tech", default="siren")
@click.option("--note", default="")
@click.option("--confirm-flash", is_flag=True, help="Acknowledge wipe risk; prints playbook path")
def download_cmd(tech: str, note: str, confirm_flash: bool) -> None:
    """Samsung Download / clean OS playbook (no silent flash)."""
    _banner()
    write_playbooks()
    snap = detect()
    case = new_case(
        "download",
        tech=tech,
        note=note or "download playbook",
        ownership_note="owned / authorized flash",
        serial=snap.serial,
        product=snap.product,
    )
    pb = PLAYBOOKS / "samsung-download.md"
    console.print(f"[green]CASE[/] {case.id}")
    console.print(f"Detect mode: {snap.mode}")
    if not confirm_flash:
        console.print(
            "[yellow]Flash can wipe the device.[/] Re-run with "
            "[bold]--confirm-flash[/] after pulling files if needed."
        )
        console.print(f"Playbook: {pb}")
        return
    console.print(Panel(pb.read_text(encoding="utf-8")[:2000], title=str(pb)))
    console.print(
        "[green]Playbook armed.[/] Push Over does not auto-flash firmware "
        "(safety). Follow playbook with heimdall/Odin, then owner login if FRP asks."
    )
    log("download_playbook", case.id, confirmed=True)


@main.command("auto")
@click.option("--tech", default="siren")
@click.option("--note", default="")
@click.option("--ownership-note", default="owned / authorized service")
@click.option("--phoenix/--no-phoenix", default=False)
@click.option("--burn-box/--no-burn-box", default=False)
@click.pass_context
def auto_cmd(ctx, tech, note, ownership_note, phoenix, burn_box) -> None:
    """Detect device and run the best safe path."""
    _banner()
    snap = detect()
    console.print(f"Detected mode: [bold]{snap.mode}[/]")
    for n in snap.notes[:6]:
        console.print(f"  • {n}")

    if snap.mode == "adb":
        ctx.invoke(
            adb_cmd,
            tech=tech,
            note=note or "auto adb",
            ownership_note=ownership_note,
            case_id=None,
            phoenix=phoenix,
            burn_box=burn_box,
        )
    elif snap.mode == "mtp":
        ctx.invoke(
            mtp_cmd,
            tech=tech,
            note=note or "auto mtp",
            ownership_note=ownership_note,
            case_id=None,
            phoenix=phoenix,
            burn_box=burn_box,
        )
    elif snap.mode == "download":
        console.print("[yellow]Download mode — pull is usually impossible; use flash playbook after optional prior backup.[/]")
        ctx.invoke(download_cmd, tech=tech, note=note or "auto download", confirm_flash=False)
    elif snap.mode == "adb_unauthorized":
        console.print("Authorize ADB on the phone, or use [bold]pushover owner[/] for FRP account path.")
        ctx.invoke(owner_cmd, tech=tech, note=note, ownership_note=ownership_note)
    else:
        console.print("No ready Android path. Plug device, set File transfer, or run [bold]pushover owner[/].")
        ctx.invoke(owner_cmd, tech=tech, note=note, ownership_note=ownership_note)


@main.command("seal")
@click.argument("case_id")
def seal_cmd(case_id: str) -> None:
    case = load_case(case_id)
    path = seal_case(case)
    console.print(f"[green]SEALED[/] {path} items={len(case.items)}")


@main.command("show")
@click.argument("case_id")
def show_cmd(case_id: str) -> None:
    case = load_case(case_id)
    from dataclasses import asdict

    console.print_json(json.dumps(asdict(case), indent=2))


if __name__ == "__main__":
    main()
