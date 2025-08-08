import os
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import REGIONS
from core.hosts_manager import (
    initialize_hosts_file,
    get_active_regions_from_hosts,
    update_hosts_file,
)
from core.region_latency_monitor import ping_all_regions, terminate_all_pings

ERROR_COLOR = "#ee4444"
ERROR_MESSAGE = "Administrator privileges required. Please run this application as an administrator."
SUCCESS_MESSAGE = "Please restart Dead by Daylight for the changes to take effect."


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_stylesheet(path):
    with open(resource_path(path), "r", encoding="utf-8") as file:
        stylesheet = file.read()

    image_path = resource_path("images/chevron-down.png").replace("\\", "/")
    stylesheet = stylesheet.replace(
        "url(images/chevron-down.png)", f"url({image_path})"
    )

    return stylesheet


def format_active_regions_status(active_regions):
    total_regions = len(REGIONS)

    if len(active_regions) in (0, total_regions):
        return "All regions available."
    else:
        return ", ".join(f"{r} ({REGIONS[r]['region']})" for r in active_regions)


def run_gui():
    icon_path = resource_path("icons/app_icon.ico")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))

    window = QWidget()
    window.setWindowTitle("DBD Region Selector")
    window.setWindowIcon(QIcon(icon_path))

    window.setWindowFlags(
        Qt.WindowType.Window
        | Qt.WindowType.WindowTitleHint
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowCloseButtonHint
        | Qt.WindowType.CustomizeWindowHint
    )

    window.setFixedSize(600, 640)

    # Load QSS Stylesheet
    qss = load_stylesheet("style/dark_theme.qss")
    app.setStyleSheet(qss)

    layout = QVBoxLayout()

    # Title and Version
    title = QLabel("DBD Region Selector")
    title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    title.setObjectName("titleLabel")

    version = QLabel("v1.0.1")
    version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    version.setObjectName("versionLabel")

    layout.addWidget(title)
    layout.addWidget(version)

    # Initialize hosts file on startup
    initialize_hosts_file()

    # Region Selection Box
    region_group = QGroupBox("Select Region")
    region_layout = QVBoxLayout()

    region_dropdown = QComboBox()
    for region_name, region_data in REGIONS.items():
        display_text = f"{region_name} ({region_data['region']})"
        region_dropdown.addItem(display_text, userData=region_name)
    region_layout.addWidget(region_dropdown)

    button_layout = QHBoxLayout()
    set_button = QPushButton("Set Region")
    default_button = QPushButton("Set Default")
    button_layout.addWidget(set_button)
    button_layout.addWidget(default_button)
    region_layout.addLayout(button_layout)

    region_group.setLayout(region_layout)
    layout.addWidget(region_group)
    layout.addSpacing(10)

    # Current Region Information
    selected_group = QGroupBox("Selected Region")
    selected_group.setFlat(False)
    selected_layout = QVBoxLayout()

    active_regions = get_active_regions_from_hosts()
    active_text = format_active_regions_status(active_regions)

    current_label = QLabel(active_text)
    current_label.setObjectName("currentLabel")
    selected_layout.addWidget(current_label)

    restart_label = QLabel("")
    restart_label.setObjectName("restartLabel")
    restart_label.setVisible(False)
    selected_layout.addWidget(restart_label)

    def show_error(message=ERROR_MESSAGE):
        restart_label.setStyleSheet(f"color: {ERROR_COLOR};")
        restart_label.setText(message)
        restart_label.setVisible(True)

    def show_success(message=SUCCESS_MESSAGE):
        restart_label.setStyleSheet("")
        restart_label.setText(message)
        restart_label.setVisible(True)

    selected_group.setLayout(selected_layout)
    layout.addWidget(selected_group)
    layout.addSpacing(10)

    # Ping Section
    ping_group = QGroupBox("Ping")
    ping_layout = QVBoxLayout()

    ping_output = QTextEdit()
    ping_output.setReadOnly(True)
    ping_output.setObjectName("pingOutput")
    ping_layout.addWidget(ping_output)

    ping_output.setHtml("<i>Measuring latencies and packet loss...</i>")

    ping_group.setLayout(ping_layout)
    layout.addWidget(ping_group)

    window.setLayout(layout)

    # Start pinging
    results = ping_all_regions()

    def update_ping_display():
        lines = []
        for region_name, region_data in results.items():
            latency_ms = region_data["latency_ms"]
            packet_loss_percentage = region_data["packet_loss_percentage"]
            status = region_data["status"]

            color = {
                "good": "#4caf50",
                "ok": "#ffc107",
                "bad": "#e53935",
            }.get(status, "#dddddd")

            if latency_ms is None:
                line = f"<span style='color:{color};'>{region_data['region']}: N/A ms, N/A % packet loss</span>"
            else:
                line = f"<span style='color:{color};'>{region_data['region']}: {latency_ms:.0f}ms, {packet_loss_percentage:.2f}% packet loss</span>"
            lines.append(line)

        ping_output.setHtml("<br>".join(lines))

    # Timer to update ping results in GUI
    timer = QTimer()
    timer.timeout.connect(update_ping_display)
    timer.start(5000)

    # Set Region Button Logic
    def on_set_region():
        selected_region_name = region_dropdown.currentData()

        try:
            update_hosts_file(active_region=selected_region_name, comment_all=False)
        except PermissionError:
            show_error()
            return

        updated = get_active_regions_from_hosts()
        updated_text = format_active_regions_status(updated)
        current_label.setText(updated_text)
        show_success()

    set_button.clicked.connect(on_set_region)

    # Set Default Button Logic
    def on_set_default():
        try:
            update_hosts_file(comment_all=True)
        except PermissionError:
            show_error()
            return

        current_label.setText("All regions available.")
        show_success()

    default_button.clicked.connect(on_set_default)

    # Terminate persistent ping subprocesses spawned by region latency monitor threads
    def on_app_exit():
        terminate_all_pings()

    app.aboutToQuit.connect(on_app_exit)

    window.show()
    sys.exit(app.exec())