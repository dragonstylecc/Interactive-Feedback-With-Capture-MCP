# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import locale
import argparse
import platform
import threading
import subprocess
import urllib.request
from typing import TypedDict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame, QScrollArea, QFileDialog, QSizePolicy, QDialog, QMenu, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QIcon, QKeyEvent, QPalette, QColor, QPixmap, QImage, QAction

class FeedbackResult(TypedDict):
    interactive_feedback: str
    images: list[str]


def _read_local_version() -> str:
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except Exception:
        return "unknown"


_PYPI_PACKAGE = "interactive-feedback-with-capture"
_GITHUB_REPO = "dragonstylecc/Interactive-Feedback-With-Capture-MCP"


def _fetch_latest_version() -> str | None:
    """Check latest version from PyPI, fallback to GitHub releases."""
    for url in (
        f"https://pypi.org/pypi/{_PYPI_PACKAGE}/json",
        f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest",
    ):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "interactive-feedback-mcp",
            })
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
            if "info" in data:
                return data["info"]["version"]
            tag = data.get("tag_name", "")
            return tag.lstrip("v") if tag else None
        except Exception:
            continue
    return None

def _detect_lang() -> str:
    try:
        settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        saved = settings.value("ui_language", "")
        if saved in ("zh", "en"):
            return saved
    except Exception:
        pass
    lang = locale.getdefaultlocale()[0] or ""
    return "zh" if lang.startswith("zh") else "en"


_I18N = {
    "zh": {
        "message": "消息：",
        "copy": "📋 复制",
        "copy_tip": "复制消息到剪贴板",
        "placeholder": "在此输入反馈（Ctrl+Enter 提交，Ctrl+V 粘贴截图）",
        "capture": "📷 截取屏幕",
        "capture_tip": "最小化此窗口并截取全屏",
        "paste": "📋 粘贴剪贴板",
        "paste_tip": "从剪贴板粘贴图片（也可使用 Ctrl+V）",
        "browse": "📁 浏览...",
        "browse_tip": "浏览图片文件",
        "use_chinese": "使用中文",
        "use_chinese_tip": "自动在反馈末尾追加中文提示",
        "reload_rules": "重新读取Rules",
        "reload_rules_tip": "提醒 AI 重新读取 Cursor Rules",
        "quick_reply": "⚡ 快捷回复",
        "quick_reply_tip": "从预设中选择快捷回复",
        "settings_tip": "设置",
        "send": "发送反馈",
        "screenshots_count": "{n} 张截图已附加",
        "preview_tip": "点击预览原图",
        "preview_title": "图片预览",
        "submit_directly": "── 直接提交 ──",
        "select_images": "选择图片",
        "image_filter": "图片 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*)",
        # SettingsDialog
        "settings_title": "设置",
        "default_toggles": "默认开关",
        "chinese_default": "使用中文（默认开启）",
        "rules_default": "重新读取Rules（默认关闭）",
        "quick_replies": "快捷回复",
        "one_per_line": "每行一条回复",
        "reset_defaults": "恢复默认",
        "version_update": "版本与更新",
        "current_ver": "当前：v{v}",
        "check_updates": "检查更新",
        "checking": "检查中...",
        "update_now": "立即更新",
        "check_fail": "⚠ 无法检查（网络错误或尚未发布）",
        "up_to_date": "✅ 已是最新版本！",
        "new_version": "🆕 新版本 v{v} 可用！",
        "updating": "⏳ 更新中...",
        "upgrade_ok": "升级成功",
        "restart_hint": "⚠ 请重启 MCP 服务以应用更改",
        "update_fail": "❌ 更新失败：{e}",
        "save": "保存",
        "cancel": "取消",
        "ver_both": "当前：v{local}  |  最新：v{latest}",
        "update_ok_msg": "✅ {msg}\n⚠ 请重启 MCP 服务以应用更改。",
        "language": "界面语言",
        "lang_auto": "自动检测",
        "lang_restart": "⚠ 语言切换将在下次打开时生效",
    },
    "en": {
        "message": "Message:",
        "copy": "📋 Copy",
        "copy_tip": "Copy message to clipboard",
        "placeholder": "Enter your feedback here (Ctrl+Enter to submit, Ctrl+V to paste screenshot)",
        "capture": "📷 Capture Screen",
        "capture_tip": "Minimize this window and capture the full screen",
        "paste": "📋 Paste Clipboard",
        "paste_tip": "Paste an image from clipboard (you can also use Ctrl+V)",
        "browse": "📁 Browse...",
        "browse_tip": "Browse for image files",
        "use_chinese": "Use Chinese",
        "use_chinese_tip": "Auto-append Chinese language hint to feedback",
        "reload_rules": "Reload Rules",
        "reload_rules_tip": "Remind AI to re-read Cursor Rules",
        "quick_reply": "⚡ Quick Reply",
        "quick_reply_tip": "Choose from preset quick replies",
        "settings_tip": "Settings",
        "send": "&Send Feedback",
        "screenshots_count": "{n} screenshot(s) attached",
        "preview_tip": "Click to preview full image",
        "preview_title": "Image Preview",
        "submit_directly": "── Submit directly ──",
        "select_images": "Select Images",
        "image_filter": "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)",
        # SettingsDialog
        "settings_title": "Settings",
        "default_toggles": "Default Toggles",
        "chinese_default": "Use Chinese (default on)",
        "rules_default": "Reload Rules (default off)",
        "quick_replies": "Quick Replies",
        "one_per_line": "One reply per line",
        "reset_defaults": "Reset to defaults",
        "version_update": "Version & Update",
        "current_ver": "Current: v{v}",
        "check_updates": "Check for updates",
        "checking": "Checking...",
        "update_now": "Update now",
        "check_fail": "⚠ Unable to check (network error or not published yet)",
        "up_to_date": "✅ Already up to date!",
        "new_version": "🆕 New version v{v} available!",
        "updating": "⏳ Updating...",
        "upgrade_ok": "Upgrade successful",
        "restart_hint": "⚠ Restart MCP server to apply changes",
        "update_fail": "❌ Update failed: {e}",
        "save": "Save",
        "cancel": "Cancel",
        "ver_both": "Current: v{local}  |  Latest: v{latest}",
        "update_ok_msg": "✅ {msg}\n⚠ Restart MCP server to apply changes.",
        "language": "UI Language",
        "lang_auto": "Auto detect",
        "lang_restart": "⚠ Language change takes effect on next launch",
    },
}

_LANG = _detect_lang()


def _t(key: str, **kwargs) -> str:
    text = _I18N.get(_LANG, _I18N["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_dark_mode_palette(app: QApplication):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return darkPalette

class FeedbackTextEdit(QTextEdit):
    image_pasted = Signal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            parent = self.parent()
            while parent and not isinstance(parent, FeedbackUI):
                parent = parent.parent()
            if parent:
                parent._submit_feedback()
        elif event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            if clipboard.mimeData() and clipboard.mimeData().hasImage():
                image = clipboard.image()
                if not image.isNull():
                    self.image_pasted.emit(image)
                    return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class SettingsDialog(QDialog):
    """Settings dialog for managing quick replies and default toggles."""
    _check_done_signal = Signal(str, object)
    _update_done_signal = Signal(bool, str)

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self._check_done_signal.connect(self._on_check_done)
        self._update_done_signal.connect(self._on_update_done)
        self.settings = settings
        self.setWindowTitle(_t("settings_title"))
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setStyleSheet(
            "QDialog { background: #353535; color: #e0e0e0; }"
            "QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 8px; padding-top: 12px; color: #ccc; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            "QCheckBox { color: #e0e0e0; }"
            "QTextEdit { background: #2a2a2a; color: #e0e0e0; border: 1px solid #555; border-radius: 3px; }"
            "QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555; border-radius: 3px; padding: 5px 15px; }"
            "QPushButton:hover { background: rgba(42,130,218,0.3); }"
        )
        layout = QVBoxLayout(self)

        # --- Language ---
        lang_row = QHBoxLayout()
        lang_label = QLabel(_t("language") + ":")
        lang_label.setStyleSheet("color: #ccc;")
        lang_row.addWidget(lang_label)
        self._lang_combo = QComboBox()
        self._lang_combo.setStyleSheet(
            "QComboBox { background: #444; color: #e0e0e0; border: 1px solid #555; border-radius: 3px; padding: 3px 8px; }"
        )
        self._lang_combo.addItem(_t("lang_auto"), "")
        self._lang_combo.addItem("中文", "zh")
        self._lang_combo.addItem("English", "en")
        current_lang = settings.value("ui_language", "")
        idx = self._lang_combo.findData(current_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        layout.addLayout(lang_row)

        # --- Default toggles ---
        toggles_group = QGroupBox(_t("default_toggles"))
        toggles_layout = QVBoxLayout(toggles_group)
        self.default_chinese = QCheckBox(_t("chinese_default"))
        self.default_chinese.setChecked(settings.value("use_chinese", True, type=bool))
        toggles_layout.addWidget(self.default_chinese)
        self.default_rules = QCheckBox(_t("rules_default"))
        self.default_rules.setChecked(settings.value("reload_rules", False, type=bool))
        toggles_layout.addWidget(self.default_rules)
        layout.addWidget(toggles_group)

        # --- Quick replies ---
        replies_group = QGroupBox(_t("quick_replies"))
        replies_layout = QVBoxLayout(replies_group)
        self.replies_list = QTextEdit()
        self.replies_list.setPlaceholderText(_t("one_per_line"))
        raw = settings.value("quick_replies")
        if raw and isinstance(raw, list):
            self.replies_list.setPlainText("\n".join(raw))
        else:
            self.replies_list.setPlainText("\n".join(FeedbackUI._DEFAULT_QUICK_REPLIES))
        replies_layout.addWidget(self.replies_list)

        reset_btn = QPushButton(_t("reset_defaults"))
        reset_btn.clicked.connect(lambda: self.replies_list.setPlainText(
            "\n".join(FeedbackUI._DEFAULT_QUICK_REPLIES)))
        replies_layout.addWidget(reset_btn)
        layout.addWidget(replies_group)

        # --- Update section ---
        update_group = QGroupBox(_t("version_update"))
        update_layout = QVBoxLayout(update_group)
        local_ver = _read_local_version()
        self._ver_label = QLabel(_t("current_ver", v=local_ver))
        self._ver_label.setStyleSheet("color: #ccc;")
        update_layout.addWidget(self._ver_label)

        update_btn_row = QHBoxLayout()
        self._check_btn = QPushButton(_t("check_updates"))
        self._check_btn.clicked.connect(self._check_update)
        update_btn_row.addWidget(self._check_btn)

        self._update_btn = QPushButton(_t("update_now"))
        self._update_btn.setVisible(False)
        self._update_btn.setStyleSheet(
            "QPushButton { background: #2a82da; color: white; border: none; }"
            "QPushButton:hover { background: #3a92ea; }"
        )
        self._update_btn.clicked.connect(self._run_update)
        update_btn_row.addWidget(self._update_btn)
        update_btn_row.addStretch()
        update_layout.addLayout(update_btn_row)

        self._update_status = QLabel("")
        self._update_status.setStyleSheet("color: #aaa; font-size: 11px;")
        self._update_status.setWordWrap(True)
        update_layout.addWidget(self._update_status)
        layout.addWidget(update_group)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton(_t("save"))
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton(_t("cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _check_update(self):
        self._check_btn.setEnabled(False)
        self._check_btn.setText(_t("checking"))
        self._update_status.setText("")

        def _do_check():
            latest = _fetch_latest_version()
            local = _read_local_version()
            self._check_done_signal.emit(local, latest)

        threading.Thread(target=_do_check, daemon=True).start()

    def _on_check_done(self, local: str, latest: str | None):
        self._check_btn.setEnabled(True)
        self._check_btn.setText(_t("check_updates"))
        if latest is None:
            self._update_status.setText(_t("check_fail"))
            return
        self._ver_label.setText(_t("ver_both", local=local, latest=latest))
        if latest == local:
            self._update_status.setText(_t("up_to_date"))
            self._update_btn.setVisible(False)
        else:
            self._update_status.setText(_t("new_version", v=latest))
            self._update_btn.setVisible(True)
            self._latest = latest

    def _run_update(self):
        self._update_btn.setEnabled(False)
        self._update_status.setText(_t("updating"))

        def _do_update():
            script_dir = os.path.dirname(os.path.abspath(__file__))
            git_dir = os.path.join(script_dir, ".git")
            is_source = os.path.isdir(git_dir) or os.path.isdir(os.path.join(os.path.dirname(script_dir), ".git"))

            try:
                if is_source:
                    work_dir = script_dir if os.path.isdir(git_dir) else os.path.dirname(script_dir)
                    result = subprocess.run(
                        ["git", "pull", "--rebase"],
                        cwd=work_dir, capture_output=True, text=True, timeout=30,
                    )
                    ok = result.returncode == 0
                    msg = result.stdout.strip() or result.stderr.strip()
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--upgrade", _PYPI_PACKAGE],
                        capture_output=True, text=True, timeout=60,
                    )
                    ok = result.returncode == 0
                    msg = _t("upgrade_ok") if ok else (result.stderr.strip() or result.stdout.strip())
            except Exception as e:
                ok = False
                msg = str(e)

            self._update_done_signal.emit(ok, msg)

        threading.Thread(target=_do_update, daemon=True).start()

    def _on_update_done(self, ok: bool, msg: str):
        self._update_btn.setEnabled(True)
        if ok:
            self._update_status.setText(_t("update_ok_msg", msg=msg))
            self._update_btn.setVisible(False)
        else:
            self._update_status.setText(_t("update_fail", e=msg))

    def _save(self):
        self.settings.setValue("use_chinese", self.default_chinese.isChecked())
        self.settings.setValue("reload_rules", self.default_rules.isChecked())
        lines = [l.strip() for l in self.replies_list.toPlainText().split("\n") if l.strip()]
        self.settings.setValue("quick_replies", lines)
        lang = self._lang_combo.currentData()
        self.settings.setValue("ui_language", lang if lang else "")
        self.accept()


class ImagePreviewDialog(QDialog):
    """Full-size image preview dialog, click or press Escape to close."""
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_t("preview_title"))
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setStyleSheet("QDialog { background: #1a1a1a; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background: #1a1a1a;")

        screen = QApplication.primaryScreen().availableGeometry()
        max_w = int(screen.width() * 0.85)
        max_h = int(screen.height() * 0.85)
        if pixmap.width() > max_w or pixmap.height() > max_h:
            scaled = pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaled = pixmap
        label.setPixmap(scaled)
        label.setCursor(Qt.PointingHandCursor)
        label.mousePressEvent = lambda _: self.close()
        layout.addWidget(label)

        self.resize(scaled.width() + 2, scaled.height() + 2)


class ScreenshotThumbnail(QWidget):
    removed = Signal(int)

    def __init__(self, pixmap: QPixmap, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._full_pixmap = pixmap

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        thumb_label = QLabel()
        scaled = pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        thumb_label.setPixmap(scaled)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setCursor(Qt.PointingHandCursor)
        thumb_label.setToolTip(_t("preview_tip"))
        thumb_label.setStyleSheet("border: 1px solid #555; border-radius: 4px; padding: 2px;")
        thumb_label.mousePressEvent = lambda _: self._preview()
        layout.addWidget(thumb_label)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedHeight(22)
        remove_btn.setStyleSheet(
            "QPushButton { color: #ff6666; background: transparent; "
            "border: 1px solid #555; border-radius: 3px; font-size: 11px; }"
            "QPushButton:hover { background: rgba(255,102,102,0.25); }"
        )
        remove_btn.clicked.connect(lambda: self.removed.emit(self.index))
        layout.addWidget(remove_btn)

        self.setFixedWidth(166)

    def _preview(self):
        dialog = ImagePreviewDialog(self._full_pixmap, self)
        dialog.exec()

class FeedbackUI(QMainWindow):
    _update_available = Signal(str)

    def __init__(self, prompt: str, predefined_options: list[str] | None = None, window_id: str = "0"):
        super().__init__()
        self.setAcceptDrops(True)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.feedback_result = None
        self.screenshots: list[QPixmap] = []
        self._latest_version: str | None = None
        self._window_id = window_id

        self._local_version = _read_local_version()
        title = f"Interactive Feedback MCP v{self._local_version}"
        if window_id and window_id != "0":
            title += f" #{window_id}"
        self.setWindowTitle(title)

        self._update_available.connect(self._on_update_available)
        threading.Thread(target=self._bg_check_update, daemon=True).start()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "images", "feedback.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")

        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(800, 650)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        self.settings.endGroup()

        self._ensure_visible_on_screen()
        self._create_ui()

    def _ensure_visible_on_screen(self):
        """Ensure the window is within visible screen bounds and not minimized."""
        available = QApplication.primaryScreen().availableGeometry()
        geo = self.geometry()

        if (geo.right() < available.left() + 50
                or geo.left() > available.right() - 50
                or geo.bottom() < available.top() + 50
                or geo.top() > available.bottom() - 50
                or geo.width() < 200 or geo.height() < 200):
            self.resize(800, 650)
            x = available.x() + (available.width() - 800) // 2
            y = available.y() + (available.height() - 650) // 2
            self.move(x, y)

    def _force_foreground(self):
        """Force the window to the foreground, bypassing Windows focus-stealing prevention."""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.showNormal()
        self.activateWindow()
        self.raise_()

        if platform.system() == "Windows":
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

    def _bg_check_update(self):
        latest = _fetch_latest_version()
        if latest and latest != self._local_version:
            self._update_available.emit(latest)

    def _on_update_available(self, version: str):
        self._latest_version = version
        title = f"Interactive Feedback MCP v{self._local_version}  ⬆ v{version} available"
        if self._window_id and self._window_id != "0":
            title += f"  #{self._window_id}"
        self.setWindowTitle(title)

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.feedback_group = QGroupBox()
        feedback_layout = QVBoxLayout(self.feedback_group)

        prompt_header = QHBoxLayout()
        prompt_title = QLabel(_t("message"))
        prompt_title.setStyleSheet("font-weight: bold; color: #ccc; font-size: 12px;")
        prompt_header.addWidget(prompt_title)
        prompt_header.addStretch()
        copy_btn = QPushButton(_t("copy"))
        copy_btn.setFixedHeight(24)
        copy_btn.setStyleSheet(
            "QPushButton { color: #aaa; background: transparent; "
            "border: 1px solid #555; border-radius: 3px; font-size: 11px; padding: 0 8px; }"
            "QPushButton:hover { background: rgba(42,130,218,0.25); color: #fff; }"
        )
        copy_btn.setToolTip(_t("copy_tip"))
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.prompt))
        prompt_header.addWidget(copy_btn)
        feedback_layout.addLayout(prompt_header)

        self.description_text = QTextEdit()
        self.description_text.setMarkdown(self.prompt)
        self.description_text.setReadOnly(True)
        self.description_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.description_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.description_text.setStyleSheet(
            "QTextEdit { background: #2a2a2a; border: 1px solid #555; "
            "border-radius: 4px; padding: 8px; color: #e0e0e0; font-size: 13px; }"
            "QTextEdit code { background: #1a1a1a; color: #e8a040; padding: 1px 4px; border-radius: 2px; }"
        )
        self.description_text.document().setDocumentMargin(4)
        font_h = self.description_text.fontMetrics().height()
        self.description_text.setMinimumHeight(5 * font_h + 20)
        self.description_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        feedback_layout.addWidget(self.description_text, stretch=3)

        self.option_checkboxes = []
        if self.predefined_options and len(self.predefined_options) > 0:
            options_frame = QFrame()
            options_layout = QVBoxLayout(options_frame)
            options_layout.setContentsMargins(0, 10, 0, 10)

            for option in self.predefined_options:
                checkbox = QCheckBox(option)
                self.option_checkboxes.append(checkbox)
                options_layout.addWidget(checkbox)

            feedback_layout.addWidget(options_frame)

            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            feedback_layout.addWidget(separator)

        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.image_pasted.connect(self._on_image_pasted)
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 5
        self.feedback_text.setMinimumHeight(5 * row_height + padding)
        self.feedback_text.setPlaceholderText(_t("placeholder"))
        feedback_layout.addWidget(self.feedback_text, stretch=1)

        # --- Screenshot section ---
        screenshot_section = QFrame()
        screenshot_main_layout = QVBoxLayout(screenshot_section)
        screenshot_main_layout.setContentsMargins(0, 5, 0, 5)

        btn_layout = QHBoxLayout()
        capture_btn = QPushButton(_t("capture"))
        capture_btn.setToolTip(_t("capture_tip"))
        capture_btn.clicked.connect(self._capture_screen)
        paste_btn = QPushButton(_t("paste"))
        paste_btn.setToolTip(_t("paste_tip"))
        paste_btn.clicked.connect(self._paste_from_clipboard)
        browse_btn = QPushButton(_t("browse"))
        browse_btn.setToolTip(_t("browse_tip"))
        browse_btn.clicked.connect(self._browse_image)
        btn_layout.addWidget(capture_btn)
        btn_layout.addWidget(paste_btn)
        btn_layout.addWidget(browse_btn)
        btn_layout.addStretch()
        screenshot_main_layout.addLayout(btn_layout)

        self.screenshot_count_label = QLabel("")
        self.screenshot_count_label.setStyleSheet("color: #aaa; font-size: 12px;")
        self.screenshot_count_label.setVisible(False)
        screenshot_main_layout.addWidget(self.screenshot_count_label)

        self.screenshots_scroll = QScrollArea()
        self.screenshots_scroll.setWidgetResizable(True)
        self.screenshots_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.screenshots_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.screenshots_scroll.setFixedHeight(140)
        self.screenshots_scroll.setVisible(False)
        self.screenshots_scroll.setStyleSheet("QScrollArea { border: 1px solid #555; border-radius: 4px; }")

        self.thumbnails_container = QWidget()
        self.thumbnails_layout = QHBoxLayout(self.thumbnails_container)
        self.thumbnails_layout.setAlignment(Qt.AlignLeft)
        self.thumbnails_layout.setContentsMargins(4, 4, 4, 4)
        self.screenshots_scroll.setWidget(self.thumbnails_container)

        screenshot_main_layout.addWidget(self.screenshots_scroll)
        feedback_layout.addWidget(screenshot_section)

        toggle_bar = QHBoxLayout()
        self.chinese_toggle = QCheckBox(_t("use_chinese"))
        self.chinese_toggle.setToolTip(_t("use_chinese_tip"))
        self.chinese_toggle.setChecked(self.settings.value("use_chinese", True, type=bool))
        self.chinese_toggle.setStyleSheet("QCheckBox { color: #aaa; font-size: 11px; }")
        toggle_bar.addWidget(self.chinese_toggle)

        self.reload_rules_toggle = QCheckBox(_t("reload_rules"))
        self.reload_rules_toggle.setToolTip(_t("reload_rules_tip"))
        self.reload_rules_toggle.setChecked(self.settings.value("reload_rules", False, type=bool))
        self.reload_rules_toggle.setStyleSheet("QCheckBox { color: #aaa; font-size: 11px; }")
        toggle_bar.addWidget(self.reload_rules_toggle)

        toggle_bar.addStretch()
        feedback_layout.addLayout(toggle_bar)

        bottom_bar = QHBoxLayout()
        quick_reply_btn = QPushButton(_t("quick_reply"))
        quick_reply_btn.setToolTip(_t("quick_reply_tip"))
        quick_reply_btn.setStyleSheet(
            "QPushButton { color: #e0a030; background: transparent; "
            "border: 1px solid #555; border-radius: 3px; padding: 4px 12px; }"
            "QPushButton:hover { background: rgba(224,160,48,0.15); }"
        )
        quick_reply_btn.clicked.connect(self._show_quick_replies)
        bottom_bar.addWidget(quick_reply_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setToolTip(_t("settings_tip"))
        settings_btn.setStyleSheet(
            "QPushButton { color: #aaa; background: transparent; "
            "border: 1px solid #555; border-radius: 3px; font-size: 14px; }"
            "QPushButton:hover { background: rgba(42,130,218,0.25); color: #fff; }"
        )
        settings_btn.clicked.connect(self._open_settings)
        bottom_bar.addWidget(settings_btn)

        bottom_bar.addStretch()

        submit_button = QPushButton(_t("send"))
        submit_button.clicked.connect(self._submit_feedback)
        bottom_bar.addWidget(submit_button)

        feedback_layout.addLayout(bottom_bar)

        layout.addWidget(self.feedback_group)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasImage():
            image = mime.imageData()
            if image and not image.isNull():
                self._add_screenshot(QPixmap.fromImage(image))
        elif mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path and os.path.isfile(path):
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        self._add_screenshot(pixmap)

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.chinese_toggle.setChecked(self.settings.value("use_chinese", True, type=bool))
            self.reload_rules_toggle.setChecked(self.settings.value("reload_rules", False, type=bool))

    # --- Quick Reply ---

    _DEFAULT_QUICK_REPLIES = [
        "没问题，继续",
        "还需要调整",
        "确认，提交推送",
        "先检查下再说",
        "还有其他问题",
        "没有了，完成",
    ]

    def _get_quick_replies(self) -> list[str]:
        raw = self.settings.value("quick_replies")
        if raw and isinstance(raw, list):
            return raw
        return self._DEFAULT_QUICK_REPLIES

    def _show_quick_replies(self):
        replies = self._get_quick_replies()
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #353535; color: #e0e0e0; border: 1px solid #555; padding: 4px; }"
            "QMenu::item { padding: 6px 20px; }"
            "QMenu::item:selected { background: rgba(42,130,218,0.4); }"
            "QMenu::separator { height: 1px; background: #555; margin: 4px 8px; }"
        )
        for text in replies:
            action = QAction(text, menu)
            action.triggered.connect(lambda checked, t=text: self._apply_quick_reply(t))
            menu.addAction(action)
        menu.addSeparator()
        submit_action = QAction(_t("submit_directly"), menu)
        submit_action.setEnabled(False)
        menu.addAction(submit_action)
        for text in replies:
            action = QAction(f"⚡ {text}", menu)
            action.triggered.connect(lambda checked, t=text: self._apply_quick_reply(t, submit=True))
            menu.addAction(action)

        btn = self.sender()
        menu.exec(btn.mapToGlobal(btn.rect().topLeft()))

    def _apply_quick_reply(self, text: str, submit: bool = False):
        self.feedback_text.setPlainText(text)
        if submit:
            self._submit_feedback()

    # --- Screenshot methods ---

    def _capture_screen(self):
        self.showMinimized()
        QTimer.singleShot(600, self._do_capture_screen)

    def _do_capture_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            if not pixmap.isNull():
                self._add_screenshot(pixmap)
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime and mime.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self._add_screenshot(QPixmap.fromImage(image))

    def _on_image_pasted(self, image: QImage):
        pixmap = QPixmap.fromImage(image)
        if not pixmap.isNull():
            self._add_screenshot(pixmap)

    def _browse_image(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, _t("select_images"), "",
            _t("image_filter"),
        )
        for path in file_paths:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._add_screenshot(pixmap)

    def _add_screenshot(self, pixmap: QPixmap):
        max_size = 1600
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.screenshots.append(pixmap)
        self._update_thumbnails()

    def _remove_screenshot(self, index: int):
        if 0 <= index < len(self.screenshots):
            self.screenshots.pop(index)
            self._update_thumbnails()

    def _update_thumbnails(self):
        while self.thumbnails_layout.count():
            item = self.thumbnails_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, pixmap in enumerate(self.screenshots):
            thumb = ScreenshotThumbnail(pixmap, i)
            thumb.removed.connect(self._remove_screenshot)
            self.thumbnails_layout.addWidget(thumb)

        has_screenshots = len(self.screenshots) > 0
        self.screenshots_scroll.setVisible(has_screenshots)
        self.screenshot_count_label.setVisible(has_screenshots)
        if has_screenshots:
            self.screenshot_count_label.setText(_t("screenshots_count", n=len(self.screenshots)))

    @staticmethod
    def _pixmap_to_base64(pixmap: QPixmap) -> str:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return byte_array.toBase64().data().decode('ascii')

    # --- Submit / Close ---

    def _submit_feedback(self):
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []

        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    selected_options.append(self.predefined_options[i])

        final_feedback_parts = []
        if selected_options:
            final_feedback_parts.append("; ".join(selected_options))
        if feedback_text:
            final_feedback_parts.append(feedback_text)

        has_content = bool(final_feedback_parts) or len(self.screenshots) > 0
        if has_content and self.chinese_toggle.isChecked():
            final_feedback_parts.append("(请使用中文回复和思考)")
        if has_content and self.reload_rules_toggle.isChecked():
            final_feedback_parts.append("(请重新读取 Cursor Rules)")

        self.settings.setValue("use_chinese", self.chinese_toggle.isChecked())
        self.settings.setValue("reload_rules", self.reload_rules_toggle.isChecked())

        final_feedback = "\n\n".join(final_feedback_parts)

        images_b64 = [self._pixmap_to_base64(p) for p in self.screenshots]

        self.feedback_result = FeedbackResult(
            interactive_feedback=final_feedback,
            images=images_b64,
        )
        self.close()

    def closeEvent(self, event):
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()
        super().closeEvent(event)

    def run(self) -> FeedbackResult:
        self._force_foreground()
        QTimer.singleShot(100, self._force_foreground)
        QTimer.singleShot(500, self._force_foreground)
        QApplication.instance().exec()

        if not self.feedback_result:
            return FeedbackResult(interactive_feedback="", images=[])

        return self.feedback_result

def feedback_ui(prompt: str, predefined_options: list[str] | None = None, output_file: str | None = None, window_id: str = "0") -> FeedbackResult | None:
    app = QApplication.instance() or QApplication()
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
    ui = FeedbackUI(prompt, predefined_options, window_id=window_id)
    result = ui.run()

    if output_file and result:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(result, f)
        return None

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the feedback UI")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--predefined-options", default="", help="Pipe-separated list of predefined options (|||)")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    parser.add_argument("--window-id", default="0", help="Window identifier for multi-agent scenarios")
    args = parser.parse_args()

    predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None

    result = feedback_ui(args.prompt, predefined_options, args.output_file, window_id=args.window_id)
    if result:
        print(f"\nFeedback received:\n{result['interactive_feedback']}")
        if result.get('images'):
            print(f"Screenshots attached: {len(result['images'])}")
    sys.exit(0)
