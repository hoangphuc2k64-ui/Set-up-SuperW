#!/usr/bin/env python3
"""
Quick Launcher & Local Server Supervisor (GTK3 - v2.1)
Sidebar:
  [1] Web & App Launcher
  [2] Project / Server Supervisor (flicker-free in-place updates)
"""
import os
import re
import socket
import threading
from datetime import datetime
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, GLib, Gtk, Pango

from core import (
    CACHE_DIR,
    SOCK_PATH,
    cleanup_service_artifacts,
    clear_service_log,
    detect_project_defaults,
    get_service_pid,
    launch_item,
    load_items,
    load_json,
    load_settings,
    norm_target,
    open_folder,
    open_url,
    read_service_log,
    save_items,
    save_json,
    save_settings,
    split_targets,
    start_service,
    stop_service,
)

SETTINGS = load_settings()

I18N = {
    "vi": {
        "title": "Quick Launcher",
        "nav_apps": "1  Web & App",
        "nav_srv": "2  Server",
        "search_app": "Tim ten, URL, lenh, hoac >chay nhanh...",
        "search_srv": "Tim du an, folder, lenh server...",
        "add_app": "+ Them",
        "add_srv": "+ Them du an",
        "edit": "Sua",
        "del": "- Xoa",
        "settings": "⚙ Cai dat",
        "start": "Bat",
        "stop": "Tat",
        "open_web": "Web",
        "open_dir": "Folder",
        "view_log": "Log",
        "running": "Dang chay",
        "stopped": "Da tat",
        "crashed": "Da dung (xem Log)",
        "dlg_app_add": "Them Web / Ung dung",
        "dlg_app_edit": "Sua Web / Ung dung",
        "dlg_srv_add": "Them Du an / Server",
        "dlg_srv_edit": "Sua Du an / Server",
        "cancel": "Huy",
        "save": "Luu",
        "folder": "1. Thu muc du an:",
        "browse": "Chon...",
        "choose_folder": "Chon thu muc du an",
        "name": "Ten hien thi:",
        "srv_name": "2. Ten du an:",
        "srv_cmd": "3. Lenh chay server:",
        "srv_url": "4. URL local (tuy chon):",
        "type": "Loai:",
        "web": "Website",
        "app": "Ung dung",
        "url": "URL (; hoac | cho combo):",
        "cmd": "Lenh (; hoac | cho combo):",
        "url_ph": "https://github.com ; https://mail.google.com",
        "cmd_ph": "code ; gnome-calculator",
        "srv_cmd_ph": "bash run.sh  hoac  python3 manage.py runserver",
        "srv_url_ph": "http://127.0.0.1:8000",
        "root": "Can quyen root (pkexec)",
        "pin": "Ghim len dau",
        "err": "Loi",
        "empty_app": "Ten va noi dung khong duoc de trong.",
        "empty_srv": "Thu muc, ten du an va lenh chay khong duoc de trong.",
        "del_ask": "Xoa '{}'?",
        "settings_title": "Cai dat",
        "theme": "Giao dien:",
        "light": "Sang",
        "dark": "Toi",
        "lang": "Ngon ngu:",
        "single_click": "Click don de mo Web/App",
        "keep_alive": "An xuong nen khi dong (mo Super+W tuc thi)",
        "close": "Dong",
        "added": "Them: {}",
        "last": "Mo: {}",
        "unknown": "Khong ro",
        "export": "Xuat JSON...",
        "import": "Nhap JSON...",
        "export_title": "Xuat file backup",
        "import_title": "Chon file backup",
        "exported": "Da xuat {} muc ra {}",
        "imported": "Da nhap {} moi, {} ghi de",
        "import_err": "Loi nhap file: {}",
        "ok": "Thanh cong",
        "overwrite": "'{}' da ton tai. Ghi de?",
        "dup": "Trung target voi '{}'. Van them?",
        "quick_saved": "Luu muc '{}' vao danh sach?",
        "log_title": "Log: {}",
        "refresh": "Lam moi",
        "clear_log": "Xoa log",
        "srv_pill": "{}/{} chay",
    },
    "en": {
        "title": "Quick Launcher",
        "nav_apps": "1  Web & App",
        "nav_srv": "2  Servers",
        "search_app": "Search name, URL, cmd, or >quick run...",
        "search_srv": "Search project, folder, or server command...",
        "add_app": "+ Add",
        "add_srv": "+ Add Project",
        "edit": "Edit",
        "del": "- Del",
        "settings": "⚙ Settings",
        "start": "Start",
        "stop": "Stop",
        "open_web": "Web",
        "open_dir": "Folder",
        "view_log": "Log",
        "running": "Running",
        "stopped": "Stopped",
        "crashed": "Exited (check Log)",
        "dlg_app_add": "Add Web / App",
        "dlg_app_edit": "Edit Web / App",
        "dlg_srv_add": "Add Project / Server",
        "dlg_srv_edit": "Edit Project / Server",
        "cancel": "Cancel",
        "save": "Save",
        "folder": "1. Project folder:",
        "browse": "Browse...",
        "choose_folder": "Select project folder",
        "name": "Display name:",
        "srv_name": "2. Project name:",
        "srv_cmd": "3. Start command:",
        "srv_url": "4. Local URL (optional):",
        "type": "Type:",
        "web": "Website",
        "app": "Application",
        "url": "URL (; or | for combo):",
        "cmd": "Command (; or | for combo):",
        "url_ph": "https://github.com ; https://mail.google.com",
        "cmd_ph": "code ; gnome-calculator",
        "srv_cmd_ph": "bash run.sh  or  python3 manage.py runserver",
        "srv_url_ph": "http://127.0.0.1:8000",
        "root": "Requires root (pkexec)",
        "pin": "Pin to top",
        "err": "Error",
        "empty_app": "Name and target cannot be empty.",
        "empty_srv": "Folder, project name, and command cannot be empty.",
        "del_ask": "Delete '{}'?",
        "settings_title": "Settings",
        "theme": "Theme:",
        "light": "Light",
        "dark": "Dark",
        "lang": "Language:",
        "single_click": "Single click to open Web/App",
        "keep_alive": "Keep running in background on close (instant Super+W)",
        "close": "Close",
        "added": "Added: {}",
        "last": "Last: {}",
        "unknown": "Unknown",
        "export": "Export JSON...",
        "import": "Import JSON...",
        "export_title": "Export backup",
        "import_title": "Import backup",
        "exported": "Exported {} item(s) to {}",
        "imported": "Imported {} new, {} overwritten",
        "import_err": "Import failed: {}",
        "ok": "Success",
        "overwrite": "'{}' already exists. Overwrite?",
        "dup": "'{}' already uses this target. Add anyway?",
        "quick_saved": "Save '{}' to launcher?",
        "log_title": "Logs: {}",
        "refresh": "Refresh",
        "clear_log": "Clear Log",
        "srv_pill": "{}/{} running",
    },
}


def tr(key):
    lang = SETTINGS.get("language", "vi")
    return I18N.get(lang, I18N["vi"]).get(key, key)


def msg_dialog(parent, mtype, title, text, buttons=Gtk.ButtonsType.OK):
    d = Gtk.MessageDialog(transient_for=parent, flags=0, message_type=mtype, buttons=buttons, text=title)
    d.format_secondary_text(text)
    res = d.run()
    d.destroy()
    return res


def small_attrs():
    attrs = Pango.AttrList()
    attrs.insert(Pango.attr_scale_new(0.84))
    return attrs


def apply_theme():
    Gtk.Settings.get_default().set_property(
        "gtk-application-prefer-dark-theme", SETTINGS.get("theme") == "dark"
    )


def apply_css():
    css = b"""
    .sidebar-box {
        border-right: 1px solid alpha(@borders, 0.7);
        padding-right: 8px;
    }
    .nav-btn {
        padding: 9px 12px;
        border-radius: 8px;
        font-weight: 600;
    }
    .nav-btn-active {
        background-color: alpha(@theme_selected_bg_color, 0.22);
        color: @theme_selected_bg_color;
    }
    .srv-pill {
        padding: 4px 10px;
        border-radius: 999px;
        background-color: alpha(@theme_fg_color, 0.08);
        font-size: 12px;
        font-weight: 600;
    }
    .srv-pill-active {
        background-color: alpha(#2ecc71, 0.18);
        color: #27ae60;
    }
    .bar-run {
        min-width: 4px;
        min-height: 28px;
        border-radius: 3px;
        background-color: #2ecc71;
    }
    .bar-stop {
        min-width: 4px;
        min-height: 28px;
        border-radius: 3px;
        background-color: alpha(@theme_fg_color, 0.22);
    }
    .bar-warn {
        min-width: 4px;
        min-height: 28px;
        border-radius: 3px;
        background-color: #e67e22;
    }
    .txt-run {
        color: #27ae60;
        font-weight: 600;
    }
    .txt-warn {
        color: #d35400;
        font-weight: 600;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def make_left_nav_button(label_text):
    btn = Gtk.Button()
    btn.set_relief(Gtk.ReliefStyle.NONE)
    btn.get_style_context().add_class("nav-btn")
    lbl = Gtk.Label(label=label_text)
    lbl.set_xalign(0.0)
    lbl.set_halign(Gtk.Align.START)
    btn.add(lbl)
    return btn, lbl


class AppItemDialog(Gtk.Dialog):
    def __init__(self, parent, item=None):
        super().__init__(title=tr("dlg_app_edit") if item else tr("dlg_app_add"), transient_for=parent, flags=0)
        self.set_default_size(400, 240)
        self.add_buttons(tr("cancel"), Gtk.ResponseType.CANCEL, tr("save"), Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)

        grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        box.add(grid)

        grid.attach(Gtk.Label(label=tr("name"), xalign=0), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry()
        grid.attach(self.name_entry, 1, 0, 2, 1)

        grid.attach(Gtk.Label(label=tr("type"), xalign=0), 0, 1, 1, 1)
        self.kind_combo = Gtk.ComboBoxText()
        self.kind_combo.append("web", tr("web"))
        self.kind_combo.append("app", tr("app"))
        self.kind_combo.set_active_id("web")
        self.kind_combo.connect("changed", self.on_kind_changed)
        grid.attach(self.kind_combo, 1, 1, 2, 1)

        self.target_label = Gtk.Label(label=tr("url"), xalign=0)
        grid.attach(self.target_label, 0, 2, 1, 1)
        self.target_entry = Gtk.Entry()
        grid.attach(self.target_entry, 1, 2, 2, 1)

        self.pin_check = Gtk.CheckButton(label=tr("pin"))
        grid.attach(self.pin_check, 0, 3, 2, 1)

        self.root_check = Gtk.CheckButton(label=tr("root"))
        grid.attach(self.root_check, 0, 4, 3, 1)

        if item:
            self.name_entry.set_text(item.get("name", ""))
            self.kind_combo.set_active_id(item.get("kind", "web"))
            self.target_entry.set_text(item.get("target", ""))
            self.pin_check.set_active(bool(item.get("pinned")))
            self.root_check.set_active(bool(item.get("root")))

        self.on_kind_changed(self.kind_combo)
        self.show_all()
        self.root_check.set_visible(self.kind_combo.get_active_id() == "app")

    def on_kind_changed(self, combo):
        is_app = combo.get_active_id() == "app"
        self.target_label.set_text(tr("cmd") if is_app else tr("url"))
        self.target_entry.set_placeholder_text(tr("cmd_ph") if is_app else tr("url_ph"))
        self.root_check.set_visible(is_app)
        if not is_app:
            self.root_check.set_active(False)

    def values(self):
        is_app = self.kind_combo.get_active_id() == "app"
        return (
            self.name_entry.get_text().strip(),
            "app" if is_app else "web",
            self.target_entry.get_text().strip(),
            self.root_check.get_active() if is_app else False,
            self.pin_check.get_active(),
        )


class ServerItemDialog(Gtk.Dialog):
    """Folder-first flow: 1. Folder -> 2. Name -> 3. Command -> 4. Optional local URL."""

    def __init__(self, parent, item=None):
        super().__init__(title=tr("dlg_srv_edit") if item else tr("dlg_srv_add"), transient_for=parent, flags=0)
        self.set_default_size(460, 270)
        self.add_buttons(tr("cancel"), Gtk.ResponseType.CANCEL, tr("save"), Gtk.ResponseType.OK)

        box = self.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)

        grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        box.add(grid)

        grid.attach(Gtk.Label(label=tr("folder"), xalign=0), 0, 0, 1, 1)
        self.cwd_entry = Gtk.Entry()
        self.cwd_entry.set_placeholder_text("~/projects/toeic")
        self.cwd_entry.connect("focus-out-event", lambda _w, _e: self._autofill_from_folder())
        grid.attach(self.cwd_entry, 1, 0, 1, 1)

        browse_btn = Gtk.Button(label=tr("browse"))
        browse_btn.connect("clicked", self.on_browse)
        grid.attach(browse_btn, 2, 0, 1, 1)

        grid.attach(Gtk.Label(label=tr("srv_name"), xalign=0), 0, 1, 1, 1)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("TOEIC Server")
        grid.attach(self.name_entry, 1, 1, 2, 1)

        grid.attach(Gtk.Label(label=tr("srv_cmd"), xalign=0), 0, 2, 1, 1)
        self.cmd_entry = Gtk.Entry()
        self.cmd_entry.set_placeholder_text(tr("srv_cmd_ph"))
        grid.attach(self.cmd_entry, 1, 2, 2, 1)

        grid.attach(Gtk.Label(label=tr("srv_url"), xalign=0), 0, 3, 1, 1)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text(tr("srv_url_ph"))
        grid.attach(self.url_entry, 1, 3, 2, 1)

        self.pin_check = Gtk.CheckButton(label=tr("pin"))
        grid.attach(self.pin_check, 0, 4, 2, 1)

        if item:
            self.cwd_entry.set_text(item.get("cwd", ""))
            self.name_entry.set_text(item.get("name", ""))
            self.cmd_entry.set_text(item.get("srv_cmd", ""))
            self.url_entry.set_text(item.get("target", ""))
            self.pin_check.set_active(bool(item.get("pinned")))

        self.show_all()

    def _autofill_from_folder(self):
        folder = self.cwd_entry.get_text().strip()
        if not folder:
            return
        suggested_name, suggested_cmd, suggested_url = detect_project_defaults(folder)
        if not self.name_entry.get_text().strip():
            self.name_entry.set_text(suggested_name)
        if not self.cmd_entry.get_text().strip() and suggested_cmd:
            self.cmd_entry.set_text(suggested_cmd)
        if not self.url_entry.get_text().strip() and suggested_url:
            self.url_entry.set_text(suggested_url)

    def on_browse(self, _btn):
        d = Gtk.FileChooserDialog(
            title=tr("choose_folder"),
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        d.add_buttons(tr("cancel"), Gtk.ResponseType.CANCEL, tr("save"), Gtk.ResponseType.OK)
        cur = os.path.expanduser(self.cwd_entry.get_text().strip() or "~")
        if os.path.isdir(cur):
            d.set_current_folder(cur)
        res = d.run()
        folder = d.get_filename()
        d.destroy()
        if res == Gtk.ResponseType.OK and folder:
            self.cwd_entry.set_text(folder)
            self._autofill_from_folder()

    def values(self):
        return (
            self.cwd_entry.get_text().strip(),
            self.name_entry.get_text().strip(),
            self.cmd_entry.get_text().strip(),
            self.url_entry.get_text().strip(),
            self.pin_check.get_active(),
        )


class LogDialog(Gtk.Dialog):
    def __init__(self, parent, item):
        super().__init__(title=tr("log_title").format(item["name"]), transient_for=parent, flags=0)
        self.item = item
        self.set_default_size(640, 400)
        self.add_buttons(
            tr("clear_log"), Gtk.ResponseType.APPLY,
            tr("refresh"), Gtk.ResponseType.YES,
            tr("close"), Gtk.ResponseType.CLOSE,
        )

        box = self.get_content_area()
        box.set_border_width(10)
        scroller = Gtk.ScrolledWindow()
        box.pack_start(scroller, True, True, 0)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroller.add(self.textview)

        self.connect("response", self.on_response)
        self.load_text()
        self.show_all()

    def load_text(self):
        buf = self.textview.get_buffer()
        buf.set_text(read_service_log(self.item["name"]))
        end_iter = buf.get_end_iter()
        self.textview.scroll_to_iter(end_iter, 0.0, False, 0.0, 1.0)

    def on_response(self, _dlg, resp_id):
        if resp_id == Gtk.ResponseType.YES:
            self.load_text()
            self.stop_emission_by_name("response")
        elif resp_id == Gtk.ResponseType.APPLY:
            clear_service_log(self.item["name"])
            self.load_text()
            self.stop_emission_by_name("response")


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title=tr("settings_title"), transient_for=parent, flags=0)
        self.parent_win = parent
        self.set_default_size(390, 340)
        self.add_buttons(tr("close"), Gtk.ResponseType.CLOSE)

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(12)

        grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        box.add(grid)

        grid.attach(Gtk.Label(label=tr("theme"), xalign=0), 0, 0, 1, 1)
        self.theme_combo = Gtk.ComboBoxText()
        self.theme_combo.append("light", tr("light"))
        self.theme_combo.append("dark", tr("dark"))
        self.theme_combo.set_active_id(SETTINGS.get("theme", "light"))
        self.theme_combo.connect("changed", self.on_theme)
        grid.attach(self.theme_combo, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label=tr("lang"), xalign=0), 0, 1, 1, 1)
        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("vi", "Tieng Viet")
        self.lang_combo.append("en", "English")
        self.lang_combo.set_active_id(SETTINGS.get("language", "vi"))
        self.lang_combo.connect("changed", self.on_lang)
        grid.attach(self.lang_combo, 1, 1, 1, 1)

        self.single_check = Gtk.CheckButton(label=tr("single_click"))
        self.single_check.set_active(bool(SETTINGS.get("single_click")))
        self.single_check.connect("toggled", self.on_single)
        grid.attach(self.single_check, 0, 2, 2, 1)

        self.keep_check = Gtk.CheckButton(label=tr("keep_alive"))
        self.keep_check.set_active(bool(SETTINGS.get("keep_alive", True)))
        self.keep_check.connect("toggled", self.on_keep)
        grid.attach(self.keep_check, 0, 3, 2, 1)

        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 4, 2, 1)

        exp_btn = Gtk.Button(label=tr("export"))
        exp_btn.connect("clicked", self.on_export)
        grid.attach(exp_btn, 0, 5, 2, 1)

        imp_btn = Gtk.Button(label=tr("import"))
        imp_btn.connect("clicked", self.on_import)
        grid.attach(imp_btn, 0, 6, 2, 1)

        self.show_all()

    def on_theme(self, combo):
        SETTINGS["theme"] = combo.get_active_id()
        save_settings(SETTINGS)
        apply_theme()

    def on_lang(self, combo):
        SETTINGS["language"] = combo.get_active_id()
        save_settings(SETTINGS)
        if self.parent_win:
            self.parent_win.apply_i18n()

    def on_single(self, chk):
        SETTINGS["single_click"] = chk.get_active()
        save_settings(SETTINGS)
        if self.parent_win:
            self.parent_win.apply_click_mode()

    def on_keep(self, chk):
        SETTINGS["keep_alive"] = chk.get_active()
        save_settings(SETTINGS)

    def _file_dlg(self, title, action, default_name=None):
        d = Gtk.FileChooserDialog(title=title, transient_for=self, action=action)
        d.add_buttons(tr("cancel"), Gtk.ResponseType.CANCEL, tr("save"), Gtk.ResponseType.OK)
        if default_name:
            d.set_current_name(default_name)
            d.set_do_overwrite_confirmation(True)
        flt = Gtk.FileFilter()
        flt.set_name("JSON")
        flt.add_pattern("*.json")
        d.add_filter(flt)
        res = d.run()
        path = d.get_filename()
        d.destroy()
        return path if res == Gtk.ResponseType.OK and path else None

    def on_export(self, _btn):
        path = self._file_dlg(tr("export_title"), Gtk.FileChooserAction.SAVE, "quicklauncher_backup.json")
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        items = load_items()
        save_json(path, items)
        msg_dialog(self, Gtk.MessageType.INFO, tr("ok"), tr("exported").format(len(items), path))

    def on_import(self, _btn):
        path = self._file_dlg(tr("import_title"), Gtk.FileChooserAction.OPEN)
        if not path:
            return
        try:
            data = load_json(path, None)
            if not isinstance(data, list):
                raise ValueError("Invalid JSON list")
            existing = {i["name"]: i for i in load_items()}
            new_c = over_c = 0
            for entry in data:
                if not isinstance(entry, dict) or not entry.get("name"):
                    continue
                name = entry["name"]
                if name in existing:
                    over_c += 1
                else:
                    new_c += 1
                existing[name] = {
                    "name": name,
                    "root": bool(entry.get("root", False)),
                    "kind": entry.get("kind", "app"),
                    "target": entry.get("target", ""),
                    "added_at": entry.get("added_at", ""),
                    "last_used": entry.get("last_used", ""),
                    "pinned": bool(entry.get("pinned", False)),
                    "cwd": entry.get("cwd", ""),
                    "srv_cmd": entry.get("srv_cmd", ""),
                }
            save_items(list(existing.values()))
            if self.parent_win:
                self.parent_win.reload_from_disk()
            msg_dialog(self, Gtk.MessageType.INFO, tr("ok"), tr("imported").format(new_c, over_c))
        except Exception as e:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), tr("import_err").format(e))


class LauncherWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title=tr("title"))
        self.set_default_size(660, 480)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("key-press-event", self.on_key)
        self.connect("delete-event", self.on_delete_event)

        apply_theme()
        apply_css()

        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        root_box.set_border_width(10)
        self.add(root_box)

        # Left Sidebar (left-aligned labels, clean & minimal)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(145, -1)
        sidebar.get_style_context().add_class("sidebar-box")
        root_box.pack_start(sidebar, False, False, 0)

        self.nav_app_btn, self.nav_app_lbl = make_left_nav_button(tr("nav_apps"))
        self.nav_app_btn.connect("clicked", lambda _b: self.switch_tab("apps"))
        sidebar.pack_start(self.nav_app_btn, False, False, 0)

        self.nav_srv_btn, self.nav_srv_lbl = make_left_nav_button(tr("nav_srv"))
        self.nav_srv_btn.connect("clicked", lambda _b: self.switch_tab("servers"))
        sidebar.pack_start(self.nav_srv_btn, False, False, 0)

        sidebar.pack_start(Gtk.Box(), True, True, 0)

        self.set_btn, self.set_lbl = make_left_nav_button(tr("settings"))
        self.set_btn.connect("clicked", self.on_settings)
        sidebar.pack_end(self.set_btn, False, False, 0)

        # Right Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(110)
        root_box.pack_start(self.stack, True, True, 0)

        # --- Page 1: Web & App ---
        app_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.app_search = Gtk.SearchEntry()
        self.app_search.set_placeholder_text(tr("search_app"))
        self.app_search.connect("search-changed", lambda e: self.render_apps(e.get_text()))
        self.app_search.connect("activate", self.on_app_search_enter)
        app_page.pack_start(self.app_search, False, False, 0)

        app_scroll = Gtk.ScrolledWindow()
        app_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        app_page.pack_start(app_scroll, True, True, 0)

        self.app_list = Gtk.ListBox()
        self.app_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.app_list.connect("row-activated", lambda _lb, _r: self.launch_selected_app())
        app_scroll.add(self.app_list)

        app_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        app_page.pack_start(app_btns, False, False, 0)

        self.app_add_btn = Gtk.Button(label=tr("add_app"))
        self.app_add_btn.connect("clicked", self.on_add_app)
        app_btns.pack_start(self.app_add_btn, True, True, 0)

        self.app_edit_btn = Gtk.Button(label=tr("edit"))
        self.app_edit_btn.connect("clicked", self.on_edit_app)
        app_btns.pack_start(self.app_edit_btn, True, True, 0)

        self.app_del_btn = Gtk.Button(label=tr("del"))
        self.app_del_btn.connect("clicked", self.on_del_app)
        app_btns.pack_start(self.app_del_btn, True, True, 0)

        self.stack.add_named(app_page, "apps")

        # --- Page 2: Servers / Projects ---
        srv_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        srv_top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.srv_search = Gtk.SearchEntry()
        self.srv_search.set_placeholder_text(tr("search_srv"))
        self.srv_search.connect("search-changed", lambda e: self.rebuild_servers(e.get_text()))
        self.srv_search.connect("activate", self.on_srv_search_enter)
        srv_top_bar.pack_start(self.srv_search, True, True, 0)

        self.srv_pill = Gtk.Label(label="")
        self.srv_pill.get_style_context().add_class("srv-pill")
        srv_top_bar.pack_end(self.srv_pill, False, False, 0)
        srv_page.pack_start(srv_top_bar, False, False, 0)

        srv_scroll = Gtk.ScrolledWindow()
        srv_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        srv_page.pack_start(srv_scroll, True, True, 0)

        self.srv_list = Gtk.ListBox()
        self.srv_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.srv_list.set_activate_on_single_click(False)
        self.srv_list.connect("row-activated", lambda _lb, _r: self.toggle_selected_srv())
        srv_scroll.add(self.srv_list)

        srv_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        srv_page.pack_start(srv_btns, False, False, 0)

        self.srv_add_btn = Gtk.Button(label=tr("add_srv"))
        self.srv_add_btn.connect("clicked", self.on_add_srv)
        srv_btns.pack_start(self.srv_add_btn, True, True, 0)

        self.srv_edit_btn = Gtk.Button(label=tr("edit"))
        self.srv_edit_btn.connect("clicked", self.on_edit_srv)
        srv_btns.pack_start(self.srv_edit_btn, True, True, 0)

        self.srv_del_btn = Gtk.Button(label=tr("del"))
        self.srv_del_btn.connect("clicked", self.on_del_srv)
        srv_btns.pack_start(self.srv_del_btn, True, True, 0)

        self.stack.add_named(srv_page, "servers")

        self.items = []
        self.app_rows = []
        self.srv_rows = []
        self.srv_widgets = {}     # name -> {bar, sub, toggle_btn, cwd_short}
        self.srv_warn_names = set()
        self.current_tab = "apps"

        self.apply_click_mode()
        self.reload_from_disk()
        self.switch_tab("apps")

        # Gentle 5s poll only when visible AND currently on the Servers tab (in-place, zero flicker)
        GLib.timeout_add_seconds(5, self._poll_server_status)

    def _poll_server_status(self):
        if self.get_visible() and self.current_tab == "servers":
            self.refresh_server_states_in_place()
        return True

    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        self.stack.set_visible_child_name(tab_name)
        c_app = self.nav_app_btn.get_style_context()
        c_srv = self.nav_srv_btn.get_style_context()
        if tab_name == "apps":
            c_app.add_class("nav-btn-active")
            c_srv.remove_class("nav-btn-active")
            self.app_search.grab_focus()
        else:
            c_srv.add_class("nav-btn-active")
            c_app.remove_class("nav-btn-active")
            self.refresh_server_states_in_place()
            self.srv_search.grab_focus()

    def apply_click_mode(self):
        self.app_list.set_activate_on_single_click(bool(SETTINGS.get("single_click")))

    def apply_i18n(self):
        self.set_title(tr("title"))
        self.nav_app_lbl.set_text(tr("nav_apps"))
        self.nav_srv_lbl.set_text(tr("nav_srv"))
        self.set_lbl.set_text(tr("settings"))
        self.app_search.set_placeholder_text(tr("search_app"))
        self.srv_search.set_placeholder_text(tr("search_srv"))
        self.app_add_btn.set_label(tr("add_app"))
        self.app_edit_btn.set_label(tr("edit"))
        self.app_del_btn.set_label(tr("del"))
        self.srv_add_btn.set_label(tr("add_srv"))
        self.srv_edit_btn.set_label(tr("edit"))
        self.srv_del_btn.set_label(tr("del"))
        self.render_apps(self.app_search.get_text())
        self.rebuild_servers(self.srv_search.get_text(), preserve_selection=True)

    def _sort_group(self, subset):
        pinned = sorted([i for i in subset if i.get("pinned")], key=lambda i: i["name"].lower())
        used = sorted([i for i in subset if not i.get("pinned") and i.get("last_used")], key=lambda i: i["last_used"], reverse=True)
        unused = sorted([i for i in subset if not i.get("pinned") and not i.get("last_used")], key=lambda i: i["name"].lower())
        return pinned + used + unused

    def reload_from_disk(self):
        self.items = load_items()
        self.render_apps(self.app_search.get_text())
        self.rebuild_servers(self.srv_search.get_text(), preserve_selection=True)

    # ---------------- Tab 1: Web & App ----------------

    def render_apps(self, filter_text=""):
        q = filter_text.lower().strip()
        for child in self.app_list.get_children():
            self.app_list.remove(child)
        self.app_rows = []

        subset = [i for i in self.items if i.get("kind") in ("web", "app")]
        for idx, it in enumerate(self._sort_group(subset)):
            hay = f"{it['name']} {it['target']} {it['kind']}".lower()
            if q and q not in hay:
                continue

            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_border_width(6)

            num_lbl = Gtk.Label(label=f"{idx + 1}." if idx < 9 else "")
            num_lbl.set_width_chars(2)
            num_lbl.set_xalign(1.0)
            num_lbl.get_style_context().add_class("dim-label")
            hbox.pack_start(num_lbl, False, False, 0)

            hbox.pack_start(Gtk.Label(label="🌐" if it["kind"] == "web" else "📦"), False, False, 0)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_txt = ("📌 " if it.get("pinned") else "") + it["name"]
            vbox.pack_start(Gtk.Label(label=title_txt, xalign=0), False, False, 0)

            meta = tr("last").format(it["last_used"]) if it.get("last_used") else (
                tr("added").format(it["added_at"]) if it.get("added_at") else tr("unknown")
            )
            sub = Gtk.Label(label=meta, xalign=0)
            sub.get_style_context().add_class("dim-label")
            sub.set_attributes(small_attrs())
            vbox.pack_start(sub, False, False, 0)
            hbox.pack_start(vbox, True, True, 0)

            if it.get("root"):
                hbox.pack_start(Gtk.Label(label="🔒"), False, False, 0)

            row.add(hbox)
            row.item_data = it
            self.app_list.add(row)
            self.app_rows.append(row)

        self.app_list.show_all()
        if self.app_rows:
            self.app_list.select_row(self.app_rows[0])

    def _run_app_and_close(self, item):
        ok, err = launch_item(item)
        if not ok:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), err)
            return
        item["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_items(self.items)
        self.close_or_hide()

    def on_app_search_enter(self, _entry):
        txt = self.app_search.get_text().strip()
        if txt.startswith(">"):
            raw = txt[1:].strip()
            if not raw:
                return
            kind = "web" if re.match(r"^(https?://|www\.)", raw, re.I) else "app"
            quick = {"name": raw, "kind": kind, "target": raw, "root": False}
            ok, err = launch_item(quick)
            if not ok:
                msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), err)
                return
            if msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("quick_saved").format(raw), Gtk.ButtonsType.YES_NO) == Gtk.ResponseType.YES:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.items.append({**quick, "added_at": now, "last_used": now, "pinned": False, "cwd": "", "srv_cmd": ""})
                save_items(self.items)
            self.close_or_hide()
            return

        row = self.app_list.get_selected_row() or (self.app_rows[0] if self.app_rows else None)
        if row:
            self._run_app_and_close(row.item_data)

    def launch_selected_app(self):
        row = self.app_list.get_selected_row()
        if row:
            self._run_app_and_close(row.item_data)

    def _upsert_app(self, name, kind, target, root, pinned, old_name=None):
        if not name or not target:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), tr("empty_app"))
            return False
        if kind == "web":
            first = split_targets(target)[0]
            if not re.match(r"^https?://", first, re.I) and ";" not in target and "|" not in target:
                target = "https://" + target

        conflict = next((i for i in self.items if i["name"] == name and i["name"] != old_name), None)
        if conflict and msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("overwrite").format(name), Gtk.ButtonsType.YES_NO) != Gtk.ResponseType.YES:
            return False

        n_t = norm_target(target, kind)
        dup = next((i for i in self.items if i["name"] != old_name and i["kind"] == kind and norm_target(i["target"], kind) == n_t), None)
        if dup and not conflict and msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("dup").format(dup["name"]), Gtk.ButtonsType.YES_NO) != Gtk.ResponseType.YES:
            return False

        prev = next((i for i in self.items if i["name"] == (old_name or name)), None)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.items = [i for i in self.items if i["name"] not in (name, old_name)]
        self.items.append({
            "name": name,
            "root": root,
            "kind": kind,
            "target": target,
            "added_at": (prev.get("added_at") if prev else "") or now,
            "last_used": prev.get("last_used", "") if prev else "",
            "pinned": pinned,
            "cwd": "",
            "srv_cmd": "",
        })
        save_items(self.items)
        self.render_apps(self.app_search.get_text())
        return True

    def on_add_app(self, _btn):
        d = AppItemDialog(self)
        if d.run() == Gtk.ResponseType.OK:
            self._upsert_app(*d.values())
        d.destroy()

    def on_edit_app(self, _btn):
        row = self.app_list.get_selected_row()
        if not row:
            return
        it = row.item_data
        d = AppItemDialog(self, item=it)
        if d.run() == Gtk.ResponseType.OK:
            self._upsert_app(*d.values(), old_name=it["name"])
        d.destroy()

    def on_del_app(self, _btn):
        row = self.app_list.get_selected_row()
        if not row:
            return
        it = row.item_data
        if msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("del_ask").format(it["name"]), Gtk.ButtonsType.YES_NO) == Gtk.ResponseType.YES:
            self.items = [i for i in self.items if i["name"] != it["name"]]
            save_items(self.items)
            self.render_apps(self.app_search.get_text())

    # ---------------- Tab 2: Servers / Projects (Flicker-free) ----------------

    def _update_srv_pill(self):
        servers = [i for i in self.items if i.get("kind") == "service"]
        running_total = sum(1 for s in servers if get_service_pid(s["name"]))
        self.srv_pill.set_text(tr("srv_pill").format(running_total, len(servers)))
        ctx = self.srv_pill.get_style_context()
        if running_total > 0:
            ctx.add_class("srv-pill-active")
        else:
            ctx.remove_class("srv-pill-active")

    def _apply_row_state(self, name):
        meta = self.srv_widgets.get(name)
        if not meta:
            return
        pid = get_service_pid(name)
        is_run = pid is not None
        if is_run:
            self.srv_warn_names.discard(name)
        is_warn = (not is_run) and (name in self.srv_warn_names)

        bar_ctx = meta["bar"].get_style_context()
        sub_ctx = meta["sub"].get_style_context()
        for c in ("bar-run", "bar-stop", "bar-warn"):
            bar_ctx.remove_class(c)
        for c in ("txt-run", "txt-warn", "dim-label"):
            sub_ctx.remove_class(c)

        if is_run:
            bar_ctx.add_class("bar-run")
            sub_ctx.add_class("txt-run")
            state_txt = f"{tr('running')} (PID {pid})"
        elif is_warn:
            bar_ctx.add_class("bar-warn")
            sub_ctx.add_class("txt-warn")
            state_txt = tr("crashed")
        else:
            bar_ctx.add_class("bar-stop")
            sub_ctx.add_class("dim-label")
            state_txt = tr("stopped")

        meta["sub"].set_text(f"{state_txt}  —  {meta['cwd_short']}")
        meta["toggle_btn"].set_label(tr("stop") if is_run else tr("start"))

    def refresh_server_states_in_place(self):
        for name in list(self.srv_widgets.keys()):
            self._apply_row_state(name)
        self._update_srv_pill()

    def rebuild_servers(self, filter_text="", preserve_selection=False):
        selected_name = None
        if preserve_selection:
            r = self.srv_list.get_selected_row()
            if r:
                selected_name = r.item_data["name"]

        q = filter_text.lower().strip()
        for child in self.srv_list.get_children():
            self.srv_list.remove(child)
        self.srv_rows = []
        self.srv_widgets = {}

        servers = [i for i in self.items if i.get("kind") == "service"]
        sorted_srvs = sorted(
            self._sort_group(servers),
            key=lambda s: 0 if get_service_pid(s["name"]) else 1,
        )

        target_row = None
        for it in sorted_srvs:
            hay = f"{it['name']} {it.get('cwd', '')} {it.get('srv_cmd', '')} {it.get('target', '')}".lower()
            if q and q not in hay:
                continue

            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_border_width(7)

            bar = Gtk.Box()
            hbox.pack_start(bar, False, False, 0)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_txt = ("📌 " if it.get("pinned") else "") + it["name"]
            vbox.pack_start(Gtk.Label(label=title_txt, xalign=0), False, False, 0)

            cwd_short = it.get("cwd", "").replace(os.path.expanduser("~"), "~")
            sub = Gtk.Label(label="", xalign=0)
            sub.set_ellipsize(Pango.EllipsizeMode.END)
            sub.set_attributes(small_attrs())
            vbox.pack_start(sub, False, False, 0)
            hbox.pack_start(vbox, True, True, 0)

            toggle_btn = Gtk.Button(label=tr("start"))
            toggle_btn.connect("clicked", lambda _b, item=it: self._toggle_srv(item))
            hbox.pack_start(toggle_btn, False, False, 0)

            if it.get("target"):
                web_btn = Gtk.Button(label=tr("open_web"))
                web_btn.connect("clicked", lambda _b, u=it["target"]: self._open_srv_web(u))
                hbox.pack_start(web_btn, False, False, 0)

            log_btn = Gtk.Button(label=tr("view_log"))
            log_btn.connect("clicked", lambda _b, item=it: self._show_srv_log(item))
            hbox.pack_start(log_btn, False, False, 0)

            dir_btn = Gtk.Button(label=tr("open_dir"))
            dir_btn.connect("clicked", lambda _b, p=it.get("cwd", ""): self._open_srv_dir(p))
            hbox.pack_start(dir_btn, False, False, 0)

            row.add(hbox)
            row.item_data = it
            self.srv_list.add(row)
            self.srv_rows.append(row)
            self.srv_widgets[it["name"]] = {
                "bar": bar,
                "sub": sub,
                "toggle_btn": toggle_btn,
                "cwd_short": cwd_short,
            }
            self._apply_row_state(it["name"])

            if selected_name and it["name"] == selected_name:
                target_row = row

        self._update_srv_pill()
        self.srv_list.show_all()
        if target_row:
            self.srv_list.select_row(target_row)
        elif self.srv_rows:
            self.srv_list.select_row(self.srv_rows[0])

    def _verify_started(self, name):
        if not get_service_pid(name):
            self.srv_warn_names.add(name)
        self.refresh_server_states_in_place()
        return False

    def _toggle_srv(self, item):
        name = item["name"]
        if get_service_pid(name):
            ok, err = stop_service(item)
            self.srv_warn_names.discard(name)
        else:
            self.srv_warn_names.discard(name)
            ok, err = start_service(item)
            if ok:
                GLib.timeout_add(900, self._verify_started, name)
        if not ok:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), err)
            return
        item["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_items(self.items)
        self.refresh_server_states_in_place()

    def _open_srv_web(self, url):
        ok, err = open_url(url)
        if not ok:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), err)

    def _open_srv_dir(self, cwd):
        ok, err = open_folder(cwd)
        if not ok:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), err)

    def _show_srv_log(self, item):
        d = LogDialog(self, item)
        d.run()
        d.destroy()

    def on_srv_search_enter(self, _entry):
        row = self.srv_list.get_selected_row() or (self.srv_rows[0] if self.srv_rows else None)
        if row:
            self._toggle_srv(row.item_data)

    def toggle_selected_srv(self):
        row = self.srv_list.get_selected_row()
        if row:
            self._toggle_srv(row.item_data)

    def _upsert_srv(self, cwd, name, srv_cmd, local_url, pinned, old_name=None):
        if not cwd or not name or not srv_cmd:
            msg_dialog(self, Gtk.MessageType.ERROR, tr("err"), tr("empty_srv"))
            return False

        conflict = next((i for i in self.items if i["name"] == name and i["name"] != old_name), None)
        if conflict and msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("overwrite").format(name), Gtk.ButtonsType.YES_NO) != Gtk.ResponseType.YES:
            return False

        prev = next((i for i in self.items if i["name"] == (old_name or name)), None)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.items = [i for i in self.items if i["name"] not in (name, old_name)]
        self.items.append({
            "name": name,
            "root": False,
            "kind": "service",
            "target": local_url,
            "added_at": (prev.get("added_at") if prev else "") or now,
            "last_used": prev.get("last_used", "") if prev else "",
            "pinned": pinned,
            "cwd": cwd,
            "srv_cmd": srv_cmd,
        })
        save_items(self.items)
        self.rebuild_servers(self.srv_search.get_text(), preserve_selection=True)
        return True

    def on_add_srv(self, _btn):
        d = ServerItemDialog(self)
        if d.run() == Gtk.ResponseType.OK:
            self._upsert_srv(*d.values())
        d.destroy()

    def on_edit_srv(self, _btn):
        row = self.srv_list.get_selected_row()
        if not row:
            return
        it = row.item_data
        d = ServerItemDialog(self, item=it)
        if d.run() == Gtk.ResponseType.OK:
            self._upsert_srv(*d.values(), old_name=it["name"])
        d.destroy()

    def on_del_srv(self, _btn):
        row = self.srv_list.get_selected_row()
        if not row:
            return
        it = row.item_data
        if msg_dialog(self, Gtk.MessageType.QUESTION, tr("title"), tr("del_ask").format(it["name"]), Gtk.ButtonsType.YES_NO) == Gtk.ResponseType.YES:
            stop_service(it)
            cleanup_service_artifacts(it["name"])
            self.srv_warn_names.discard(it["name"])
            self.items = [i for i in self.items if i["name"] != it["name"]]
            save_items(self.items)
            self.rebuild_servers(self.srv_search.get_text())

    # ---------------- Global Window & Keyboard Controls ----------------

    def on_settings(self, _btn):
        d = SettingsDialog(self)
        d.run()
        d.destroy()

    def _move_selection(self, delta):
        lb = self.app_list if self.current_tab == "apps" else self.srv_list
        rows = self.app_rows if self.current_tab == "apps" else self.srv_rows
        if not rows:
            return
        cur = lb.get_selected_row()
        idx = rows.index(cur) if cur in rows else 0
        nxt = max(0, min(len(rows) - 1, idx + delta))
        lb.select_row(rows[nxt])

    def on_key(self, _w, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_or_hide()
            return True

        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)

        if ctrl and event.keyval == Gdk.KEY_1:
            self.switch_tab("apps")
            return True
        if ctrl and event.keyval == Gdk.KEY_2:
            self.switch_tab("servers")
            return True

        active_search = self.app_search if self.current_tab == "apps" else self.srv_search
        if active_search.has_focus() and event.keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            self._move_selection(1 if event.keyval == Gdk.KEY_Down else -1)
            return True

        if not ctrl and not alt and not active_search.get_text():
            if event.keyval == Gdk.KEY_1:
                self.switch_tab("apps")
                return True
            if event.keyval == Gdk.KEY_2:
                self.switch_tab("servers")
                return True

        if alt and self.current_tab == "apps":
            num = event.keyval - Gdk.KEY_1
            if 0 <= num < 9 and num < len(self.app_rows):
                self._run_app_and_close(self.app_rows[num].item_data)
                return True
        return False

    def on_delete_event(self, _w, _event):
        if SETTINGS.get("keep_alive", True):
            self.hide_window()
            return True
        return False

    def close_or_hide(self):
        if SETTINGS.get("keep_alive", True):
            self.hide_window()
        else:
            self.destroy()

    def hide_window(self):
        self.app_search.set_text("")
        self.srv_search.set_text("")
        self.hide()

    def popup_window(self):
        apply_theme()
        self.reload_from_disk()
        self.show_all()
        self.set_position(Gtk.WindowPosition.CENTER)
        self.present()
        self.switch_tab("apps")


def try_signal_existing():
    if not os.path.exists(SOCK_PATH):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            s.connect(SOCK_PATH)
            s.sendall(b"TOGGLE")
            return True
    except Exception:
        try:
            os.unlink(SOCK_PATH)
        except Exception:
            pass
        return False


def start_ipc_server(win):
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(SOCK_PATH):
        os.unlink(SOCK_PATH)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    srv.listen(5)

    def _listen():
        while True:
            try:
                conn, _ = srv.accept()
                with conn:
                    if conn.recv(32) == b"TOGGLE":
                        GLib.idle_add(win.popup_window)
            except Exception:
                break

    threading.Thread(target=_listen, daemon=True).start()


def cleanup_socket():
    try:
        if os.path.exists(SOCK_PATH):
            os.unlink(SOCK_PATH)
    except Exception:
        pass


def main():
    if try_signal_existing():
        return
    win = LauncherWindow()
    start_ipc_server(win)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    try:
        Gtk.main()
    finally:
        cleanup_socket()


if __name__ == "__main__":
    main()
