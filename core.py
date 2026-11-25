#!/usr/bin/env python3
"""
Core storage, IPC, and lightweight process supervisor for Quick Launcher.
Backward-compatible with existing items.tsv (3 to 9 columns).
"""
import csv
import hashlib
import json
import os
import re
import signal
import subprocess
import time
from datetime import datetime

CONFIG_DIR = os.path.expanduser("~/.config/quicklauncher")
CACHE_DIR = os.path.expanduser("~/.cache/quicklauncher")
PID_DIR = os.path.join(CACHE_DIR, "pids")
LOG_DIR = os.path.join(CACHE_DIR, "logs")
ITEMS_FILE = os.path.join(CONFIG_DIR, "items.tsv")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
SOCK_PATH = os.path.join(CACHE_DIR, f"ql-{os.getuid()}.sock")

MAX_LOG_BYTES = 256 * 1024  # Keep logs compact (~256 KB per server)

DEFAULT_SETTINGS = {
    "theme": "light",
    "language": "vi",
    "single_click": False,
    "keep_alive": True,
}


def load_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(fallback, dict) and isinstance(data, dict):
                merged = dict(fallback)
                merged.update(data)
                return merged
            return data
        except Exception:
            pass
    return dict(fallback) if isinstance(fallback, dict) else fallback


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_settings():
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


def ensure_items_file():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(ITEMS_FILE):
        open(ITEMS_FILE, "a", encoding="utf-8").close()


def _clean_field(val):
    return str(val or "").replace("\t", " ").replace("\n", " ").strip()


def load_items():
    """Read items.tsv via csv module while supporting legacy 3..9 column rows."""
    ensure_items_file()
    items = []
    with open(ITEMS_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for p in reader:
            if not p or (len(p) == 1 and not p[0].strip()):
                continue
            added_at, last_used, pinned, cwd, srv_cmd = "", "", False, "", ""
            if len(p) >= 9:
                name, r_flag, kind, target, added_at, last_used, p_flag, cwd, srv_cmd = p[:9]
                pinned = p_flag == "1"
            elif len(p) == 8:
                name, r_flag, kind, target, added_at, last_used, p_flag, cwd = p
                pinned = p_flag == "1"
            elif len(p) == 7:
                name, r_flag, kind, target, added_at, last_used, p_flag = p
                pinned = p_flag == "1"
            elif len(p) == 6:
                name, r_flag, kind, target, added_at, last_used = p
            elif len(p) == 5:
                name, r_flag, kind, target, added_at = p
            elif len(p) == 4:
                name, r_flag, kind, target = p
            elif len(p) == 3:
                name, r_flag, cmd = p
                if cmd.startswith("xdg-open"):
                    kind = "web"
                    target = cmd.split("'", 1)[-1].rstrip("'")
                else:
                    kind = "app"
                    target = cmd
            else:
                continue

            if kind not in ("web", "app", "service"):
                kind = "app"
            if kind == "service" and not srv_cmd and target and not re.match(r"^https?://", target, re.I):
                srv_cmd = target
                target = ""

            items.append({
                "name": name,
                "root": r_flag == "1",
                "kind": kind,
                "target": target,
                "added_at": added_at,
                "last_used": last_used,
                "pinned": pinned,
                "cwd": cwd,
                "srv_cmd": srv_cmd,
            })
    return items


def save_items(items):
    ensure_items_file()
    with open(ITEMS_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        for it in items:
            writer.writerow([
                _clean_field(it.get("name")),
                "1" if it.get("root") else "0",
                _clean_field(it.get("kind") or "app"),
                _clean_field(it.get("target")),
                _clean_field(it.get("added_at")),
                _clean_field(it.get("last_used")),
                "1" if it.get("pinned") else "0",
                _clean_field(it.get("cwd")),
                _clean_field(it.get("srv_cmd")),
            ])


def norm_target(target, kind):
    t = (target or "").strip().lower()
    if kind == "web":
        t = re.sub(r"^https?://", "", t).rstrip("/")
    return t


def split_targets(target):
    return [part.strip() for part in re.split(r"[;|]", target or "") if part.strip()]


def detect_project_defaults(folder_path):
    """Inspect a project folder to suggest display name, start command, and local URL."""
    folder = os.path.abspath(os.path.expanduser(folder_path))
    name = os.path.basename(folder.rstrip(os.sep)) or "Project"
    if not os.path.isdir(folder):
        return name, "", ""

    files = set(os.listdir(folder))
    cmd = ""
    local_url = ""

    if "run.sh" in files:
        cmd = "bash run.sh"
    elif "docker-compose.yml" in files or "docker-compose.yaml" in files or "compose.yaml" in files:
        cmd = "docker compose up"
    elif "manage.py" in files:
        cmd = "python3 manage.py runserver"
        local_url = "http://127.0.0.1:8000"
    elif "package.json" in files:
        local_url = "http://localhost:3000"
        try:
            with open(os.path.join(folder, "package.json"), "r", encoding="utf-8") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            if "dev" in scripts:
                cmd = "npm run dev"
            elif "start" in scripts:
                cmd = "npm start"
        except Exception:
            cmd = "npm run dev"
    elif "app.py" in files:
        cmd = "python3 app.py"
        local_url = "http://127.0.0.1:5000"
    elif "main.py" in files:
        cmd = "python3 main.py"
        local_url = "http://127.0.0.1:8000"

    return name, cmd, local_url


# ---------------- Lightweight Process Supervisor ----------------

def _slug(name):
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]


def pid_file_for(name):
    os.makedirs(PID_DIR, exist_ok=True)
    return os.path.join(PID_DIR, f"{_slug(name)}.pid")


def log_file_for(name):
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, f"{_slug(name)}.log")


def cleanup_service_artifacts(name):
    for fn in (pid_file_for, log_file_for):
        path = fn(name)
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass


def get_service_pid(name):
    pfile = pid_file_for(name)
    if not os.path.exists(pfile):
        return None
    try:
        with open(pfile, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        pid = int(raw.splitlines()[0])
        os.kill(pid, 0)
        return pid
    except Exception:
        try:
            os.unlink(pfile)
        except Exception:
            pass
        return None


def _trim_log_if_needed(lpath):
    try:
        if os.path.exists(lpath) and os.path.getsize(lpath) > MAX_LOG_BYTES:
            with open(lpath, "rb") as f:
                f.seek(-MAX_LOG_BYTES // 2, os.SEEK_END)
                tail = f.read()
            with open(lpath, "wb") as f:
                f.write(b"... [truncated older logs] ...\n" + tail)
    except Exception:
        pass


def read_service_log(name, max_lines=160):
    lpath = log_file_for(name)
    if not os.path.exists(lpath):
        return "(Chua co log / No logs yet)"
    try:
        with open(lpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:]) if lines else "(Log trong / Empty log)"
    except Exception as e:
        return f"Error reading log: {e}"


def clear_service_log(name):
    lpath = log_file_for(name)
    try:
        open(lpath, "w", encoding="utf-8").close()
    except Exception:
        pass


def start_service(item):
    name = item["name"]
    if get_service_pid(name):
        return True, ""

    cmd_str = (item.get("srv_cmd") or item.get("target") or "").strip()
    if not cmd_str:
        return False, "Empty server command."

    cwd = os.path.expanduser(item.get("cwd") or "")
    if cwd and not os.path.isdir(cwd):
        return False, f"Folder not found: {cwd}"

    lpath = log_file_for(name)
    _trim_log_if_needed(lpath)

    try:
        log_f = open(lpath, "a", encoding="utf-8")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_f.write(f"\n=== [{stamp}] START ({cwd or '~'}): {cmd_str} ===\n")
        log_f.flush()

        proc = subprocess.Popen(
            ["bash", "-lc", cmd_str],
            cwd=cwd or None,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_f.close()

        with open(pid_file_for(name), "w", encoding="utf-8") as pf:
            pf.write(f"{proc.pid}\n{stamp}\n")
        return True, ""
    except Exception as e:
        return False, str(e)


def stop_service(item):
    name = item["name"]
    pid = get_service_pid(name)
    if not pid:
        return True, ""
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGTERM)
        for _ in range(12):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except Exception as e:
        return False, str(e)

    try:
        os.unlink(pid_file_for(name))
    except Exception:
        pass

    try:
        with open(log_file_for(name), "a", encoding="utf-8") as lf:
            lf.write(f"=== [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] STOPPED ===\n")
    except Exception:
        pass
    return True, ""


def open_url(url):
    u = (url or "").strip()
    if not u:
        return False, "Empty URL"
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    try:
        subprocess.Popen(["xdg-open", u], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def open_folder(folder_path):
    cwd = os.path.expanduser(folder_path or "")
    if not cwd or not os.path.isdir(cwd):
        return False, f"Folder not found: {cwd}"
    try:
        subprocess.Popen(["xdg-open", cwd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def launch_item(item):
    parts = split_targets(item.get("target", ""))
    kind = item.get("kind", "app")
    use_root = bool(item.get("root"))
    cwd = os.path.expanduser(item.get("cwd") or "") or None
    if cwd and not os.path.isdir(cwd):
        cwd = None

    for part in parts:
        try:
            if kind == "web":
                url = part if re.match(r"^https?://", part, re.I) else "https://" + part
                cmd = ["xdg-open", url]
            else:
                cmd = ["bash", "-lc", part]

            if use_root:
                subprocess.Popen(["pkexec"] + cmd, cwd=cwd)
            else:
                subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
        except Exception as e:
            return False, f"{part}: {e}"
    return True, ""
