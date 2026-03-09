import sys, os, json, time, requests, webbrowser, threading, zipfile, io, shutil
from pathlib import Path
from evdev import UInput, ecodes as e, list_devices, InputDevice, categorize
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QPushButton, QComboBox, QCheckBox, QSlider, QSizePolicy,
                             QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject

# --- 1. CONFIG & PATHS ---
CONFIG_DIR = Path.home() / ".config" / "helltux"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"
ICON_DIR = Path(__file__).parent / "icons"
ZIP_URL = "https://github.com/nvigneux/Helldivers-2-Stratagems-icons-svg/archive/refs/heads/master.zip"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    # Normalize path: replace spaces with underscores and force lowercase
    normalized = relative_path.replace(" ", "_").lower()
    return str(os.path.join(base_path, normalized))

# --- 2. ENGINE SETUP ---
UP, DN, LT, RT = e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT
SCAN_TO_KEY = {82:'0', 79:'1', 80:'2', 81:'3', 75:'4', 76:'5', 77:'6', 71:'7', 72:'8', 73:'9'}
REINFORCE_SCAN = 82 

try:
    cap = {e.EV_KEY: [UP, DN, LT, RT, e.KEY_LEFTCTRL]}
    ui_device = UInput(cap, name='HellTux-vDevice')
except:
    ui_device = None

# --- 3. MASTER STRATAGEM DATABASE ---

STRATAGEM_DB = {
    "Main": [
        # Patriotic Administration Center
        {"name": "Machine Gun", "icon": "icons/Machine_Gun.svg", "seq": [DN, LT, DN, UP, RT]},
        {"name": "Anti-Materiel Rifle", "icon": "icons/Anti-Materiel_Rifle.svg", "seq": [DN, LT, RT, UP, DN]},
        {"name": "Stalwart", "icon": "icons/Stalwart.svg", "seq": [DN, LT, DN, UP, UP, LT]},
        {"name": "Expendable Anti-Tank", "icon": "icons/Expendable_Anti-Tank.svg", "seq": [DN, DN, LT, UP, RT]},
        {"name": "Recoilless Rifle", "icon": "icons/Recoilless_Rifle.svg", "seq": [DN, LT, RT, RT, LT]},
        {"name": "Flamethrower", "icon": "icons/Flamethrower.svg", "seq": [DN, LT, UP, DN, UP]},
        {"name": "Autocannon", "icon": "icons/Autocannon.svg", "seq": [DN, LT, DN, UP, UP, RT]},
        {"name": "Heavy Machine Gun", "icon": "icons/Heavy_Machine_Gun.svg", "seq": [DN, LT, UP, DN, DN]},
        {"name": "Airburst Rocket Launcher", "icon": "icons/Airburst_Rocket_Launcher.svg", "seq": [DN, UP, UP, LT, RT]},
        {"name": "Commando", "icon": "icons/Commando.svg", "seq": [DN, LT, UP, DN, RT]},
        {"name": "Railgun", "icon": "icons/Railgun.svg", "seq": [DN, RT, DN, UP, LT, RT]},
        {"name": "Spear", "icon": "icons/Spear.svg", "seq": [DN, DN, UP, DN, DN]},
        # Orbital Cannons
        {"name": "Orbital Precision Strike", "icon": "icons/Orbital_Precision_Strike.svg", "seq": [RT, RT, UP]},
        {"name": "Orbital Gatling Barrage", "icon": "icons/Orbital_Gatling_Barrage.svg", "seq": [RT, DN, LT, UP, UP]},
        {"name": "Orbital Airburst Strike", "icon": "icons/Orbital_Airburst_Strike.svg", "seq": [RT, RT, RT]},
        {"name": "Orbital 120MM HE Barrage", "icon": "icons/Orbital_120MM_HE_Barrage.svg", "seq": [RT, RT, DN, LT, RT, DN]},
        {"name": "Orbital 380MM HE Barrage", "icon": "icons/Orbital_380MM_HE_Barrage.svg", "seq": [RT, DN, UP, UP, LT, DN, DN]},
        {"name": "Orbital Walking Barrage", "icon": "icons/Orbital_Walking_Barrage.svg", "seq": [RT, DN, RT, DN, RT, DN]},
        {"name": "Orbital Laser", "icon": "icons/Orbital_Laser.svg", "seq": [RT, DN, UP, RT, DN]},
        {"name": "Orbital Railcannon Strike", "icon": "icons/Orbital_Railcannon_Strike.svg", "seq": [RT, UP, DN, DN, RT]},
        # Hangar (Eagle)
        {"name": "Eagle Strafing Run", "icon": "icons/Eagle_Strafing_Run.svg", "seq": [UP, RT, RT]},
        {"name": "Eagle Airstrike", "icon": "icons/Eagle_Airstrike.svg", "seq": [UP, RT, DN, RT]},
        {"name": "Eagle Cluster Bomb", "icon": "icons/Eagle_Cluster_Bomb.svg", "seq": [UP, RT, DN, DN, RT]},
        {"name": "Eagle Napalm Airstrike", "icon": "icons/Eagle_Napalm_Airstrike.svg", "seq": [UP, RT, DN, UP]},
        {"name": "Eagle Smoke Strike", "icon": "icons/Eagle_Smoke_Strike.svg", "seq": [UP, RT, UP, DN]},
        {"name": "Eagle 110MM Rocket Pods", "icon": "icons/Eagle_110MM_Rocket_Pods.svg", "seq": [UP, RT, UP, LT]},
        {"name": "Eagle 500KG Bomb", "icon": "icons/Eagle_500KG_Bomb.svg", "seq": [UP, RT, DN, DN, DN]},
        # Bridge & Engineering
        {"name": "Orbital Gas Strike", "icon": "icons/Orbital_Gas_Strike.svg", "seq": [RT, RT, DN, RT]},
        {"name": "Orbital EMS Strike", "icon": "icons/Orbital_EMS_Strike.svg", "seq": [RT, RT, LT, DN]},
        {"name": "Orbital Smoke Strike", "icon": "icons/Orbital_Smoke_Strike.svg", "seq": [RT, RT, DN, UP]},
        {"name": "HMG Emplacement", "icon": "icons/HMG_Emplacement.svg", "seq": [DN, UP, LT, RT, RT, LT]},
        {"name": "Shield Generator Relay", "icon": "icons/Shield_Generator_Relay.svg", "seq": [DN, DN, LT, RT, LT, RT]},
        {"name": "Tesla Tower", "icon": "icons/Tesla_Tower.svg", "seq": [DN, UP, RT, UP, LT, RT]},
        {"name": "Anti-Personnel Minefield", "icon": "icons/Anti-Personnel_Minefield.svg", "seq": [DN, LT, UP, RT]},
        {"name": "Supply Pack", "icon": "icons/Supply_Pack.svg", "seq": [DN, LT, DN, UP, UP, DN]},
        {"name": "Grenade Launcher", "icon": "icons/Grenade_Launcher.svg", "seq": [DN, LT, UP, LT, DN]},
        {"name": "Laser Cannon", "icon": "icons/Laser_Cannon.svg", "seq": [DN, LT, DN, UP, LT]},
        {"name": "Incendiary Mines", "icon": "icons/Incendiary_Mines.svg", "seq": [DN, LT, LT, DN]},
        {"name": "Guard Dog Rover", "icon": "icons/Guard_Dog_Rover.svg", "seq": [DN, UP, LT, UP, RT, RT]},
        {"name": "Ballistic Shield", "icon": "icons/Ballistic_Shield_Backpack.svg", "seq": [DN, LT, DN, DN, UP, LT]},
        {"name": "Arc Thrower", "icon": "icons/Arc_Thrower.svg", "seq": [DN, RT, DN, UP, LT, LT]},
        {"name": "Shield Generator Pack", "icon": "icons/Shield_Generator_Pack.svg", "seq": [DN, UP, LT, RT, LT, RT]},
        {"name": "Quasar Cannon", "icon": "icons/Quasar_Cannon.svg", "seq": [DN, DN, UP, LT, RT]},
        # Robotics
        {"name": "Machine Gun Sentry", "icon": "icons/Machine_Gun_Sentry.svg", "seq": [DN, UP, RT, RT, UP]},
        {"name": "Gatling Sentry", "icon": "icons/Gatling_Sentry.svg", "seq": [DN, UP, RT, LT]},
        {"name": "Mortar Sentry", "icon": "icons/Mortar_Sentry.svg", "seq": [DN, UP, RT, RT, DN]},
        {"name": "Guard Dog", "icon": "icons/Guard_Dog.svg", "seq": [DN, UP, LT, UP, RT, DN]},
        {"name": "Autocannon Sentry", "icon": "icons/Autocannon_Sentry.svg", "seq": [DN, UP, RT, UP, LT, UP]},
        {"name": "Rocket Sentry", "icon": "icons/Rocket_Sentry.svg", "seq": [DN, UP, RT, RT, LT]},
        {"name": "EMS Mortar Sentry", "icon": "icons/EMS_Mortar_Sentry.svg", "seq": [DN, UP, RT, DN, RT]},
        {"name": "Patriot Exosuit", "icon": "icons/Patriot_Exosuit.svg", "seq": [LT, DN, RT, UP, LT, DN, DN]},
        {"name": "Emancipator Exosuit", "icon": "icons/Emancipator_Exosuit.svg", "seq": [LT, DN, RT, UP, LT, DN, UP]}
    ],
    "Warbond": [
        {"name": "Orbital Napalm Barrage", "icon": "icons/Orbital_Napalm_Barrage.svg", "seq": [RT, RT, DN, UP, DN]},
        {"name": "Sterilizer", "icon": "icons/Sterilizer.svg", "seq": [DN, LT, DN, DN, UP, LT]},
        {"name": "Anti-Tank Mines", "icon": "icons/Anti-Tank_Mines.svg", "seq": [DN, LT, UP, UP]},
        {"name": "Gas Mines", "icon": "icons/Gas_Mine.svg", "seq": [DN, LT, LT, RT]},
        {"name": "StA-X3 WASP", "icon": "icons/sta-x3_w.a.s.p._launcher.svg", "seq": [DN, DN, UP, DN, RT]},
        {"name": "Portable Hellbomb", "icon": "icons/hellbomb_portable.svg", "seq": [DN, UP, LT, DN, UP, RT]},
        {"name": "Hover Pack", "icon": "icons/Hover_Pack.svg", "seq": [DN, UP, UP, DN, UP]},
        {"name": "Directional Shield", "icon": "icons/Directional_Shield.svg", "seq": [DN, LT, RT, UP, UP]},
        {"name": "Flame Sentry", "icon": "icons/Flame_Sentry.svg", "seq": [DN, UP, RT, DN, DN]},
        {"name": "Laser Sentry", "icon": "icons/Laser_Sentry.svg", "seq": [DN, UP, LT, UP, RT, UP]},
        {"name": "Warp Pack", "icon": "icons/Warp_Pack.svg", "seq": [RT, LT, UP, UP, DN]},
        {"name": "Speargun", "icon": "icons/Speargun.svg", "seq": [DN, DN, LT, RT, DN]},
        {"name": "Maxigun", "icon": "icons/Maxigun.svg", "seq": [DN, LT, UP, RT, RT]}
    ],
    "Mission": [
        {"name": "Reinforce", "icon": "icons/Reinforce.svg", "seq": [UP, DN, RT, LT, UP]},
        {"name": "SOS Beacon", "icon": "icons/SOS_Beacon.svg", "seq": [UP, DN, RT, UP]},
        {"name": "Resupply", "icon": "icons/Resupply.svg", "seq": [DN, DN, UP, RT]},
        {"name": "Eagle Rearm", "icon": "icons/Eagle_Rearm.svg", "seq": [UP, UP, LT, UP, RT]},
        {"name": "Hellbomb", "icon": "icons/Hellbomb.svg", "seq": [DN, UP, LT, DN, UP, RT, DN, UP]},
        {"name": "SEAF Artillery", "icon": "icons/SEAF_Artillery.svg", "seq": [RT, UP, UP, DN]},
        {"name": "Super Earth Flag", "icon": "icons/Super_Earth_Flag.svg", "seq": [DN, UP, DN, UP]},
        {"name": "SSSD Delivery", "icon": "icons/SSSD_Delivery.svg", "seq": [DN, DN, DN, UP, UP]},
        {"name": "Seismic Probe", "icon": "icons/Seismic_Probe.svg", "seq": [UP, UP, LT, RT, DN, DN]},
        {"name": "Upload Data", "icon": "icons/Upload_Data.svg", "seq": [LT, RT, UP, UP, UP]},
        {"name": "Tectonic Drill", "icon": "icons/Tectonic_Drill.svg", "seq": [DN, DN, LT, RT, DN, DN]},
        {"name": "Hive Breaker Drill", "icon": "icons/Hive_Breaker_Drill.svg", "seq": [DN, UP, LT, DN, UP, RT, DN, DN]},
        {"name": "Dark Fluid Vessel", "icon": "icons/Dark_Fluid_Vessel.svg", "seq": [DN, UP, LT, DN, UP, RT]},
        {"name": "Illumination Flare", "icon": "icons/Orbital_Illumination_Flare.svg", "seq": [RT, RT, LT, LT]},
        {"name": "One True Flag", "icon": "icons/One_True_Flag.svg", "seq": [DN, UP, DN, UP]},
        {"name": "Confiscate Assets", "icon": "icons/cargo_container.svg", "seq": [RT, LT, UP, DN, RT]}
    ]
}

# --- 4. ASSET & MACRO LOGIC ---
is_chatting = False
class CommSignals(QObject):
    chat_toggled = pyqtSignal(bool)
signals = CommSignals()

def download_and_extract():
    if not ICON_DIR.exists(): ICON_DIR.mkdir(parents=True)
    temp_extract_dir = Path("/tmp/helltux_temp")
    headers = {'User-Agent': 'HellTux-Diver'}
    try:
        r = requests.get(ZIP_URL, headers=headers, timeout=15)
        r.raise_for_status()
        if temp_extract_dir.exists(): shutil.rmtree(temp_extract_dir)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(temp_extract_dir)
        found_svgs = list(temp_extract_dir.rglob("*.svg"))
        if len(found_svgs) > 0:
            for svg_path in found_svgs:
                # Force lowercase AND underscores for absolute consistency
                clean_name = svg_path.name.replace(" ", "_").lower()
                shutil.copy2(svg_path, ICON_DIR / clean_name)
            shutil.rmtree(temp_extract_dir)
            print(f"Assets Synced (Case-Insensitive): {len(found_svgs)} icons.")
    except Exception as e: print(f"Asset Error: {e}")

def run_macro(sequence):
    if not ui_device or is_chatting: return
    ui_device.write(e.EV_KEY, e.KEY_LEFTCTRL, 1); ui_device.syn(); time.sleep(0.1)
    for move in sequence:
        ui_device.write(e.EV_KEY, move, 1); ui_device.syn(); time.sleep(0.06)
        ui_device.write(e.EV_KEY, move, 0); ui_device.syn(); time.sleep(0.06)
    ui_device.write(e.EV_KEY, e.KEY_LEFTCTRL, 0); ui_device.syn()

# --- 5. MAIN UI ---
class HellTux(QWidget):

    def __init__(self):
        super().__init__()
        download_and_extract()
        self.settings = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self.settings = {}

        # 2. Extract binds (so they're available for buttons)
        # Handle the case where the file might be the old format or new format
        self.active_binds = self.settings.get("binds", self.settings) 
        if "binds" not in self.settings:
            # If it's an old file, wrap it in the new structure
            self.settings = {"binds": self.active_binds, "last_device": ""}
        self.initUI()
        signals.chat_toggled.connect(self.update_status_ui)
        threading.Thread(target=self.evdev_listener, daemon=True).start()

    def initUI(self):
        self.setWindowTitle("HellTux")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: #000; color: #FFD700; border: 1px solid #FFD700;")
        layout = QVBoxLayout(self)
        
        # --- TOP CONTROL BAR (Vertical Stack) ---
        top_container = QVBoxLayout()
        
        # 1. Checkbox on its own row
        self.show_text_cb = QCheckBox("SHOW TEXT")
        # Load saved preference (Default to True if not found)
        self.show_text_cb.setChecked(self.settings.get("show_names", True))
        self.show_text_cb.setStyleSheet("color: #FFD700; font-weight: bold; border: none; margin-bottom: 5px;")
        self.show_text_cb.stateChanged.connect(self.toggle_text_visibility)
        top_container.addWidget(self.show_text_cb)

        # --- SCALE SLIDER ---
        scale_label = QLabel(f"UI SCALE: {self.settings.get('ui_scale', 100)}%")
        scale_label.setStyleSheet("color: #FFD700; font-size: 10px; border: none;")
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(100, 200) # 60% to 200% size
        self.scale_slider.setValue(self.settings.get('ui_scale', 100))
        self.scale_slider.valueChanged.connect(lambda v: [scale_label.setText(f"UI SCALE: {v}%"), self.apply_global_scale(v)])
        
        top_container.addWidget(scale_label)
        top_container.addWidget(self.scale_slider)

        # 2. Buttons on the row below
        btn_row = QHBoxLayout()
        wiki_btn = QPushButton("STRATAGEM WIKI")
        wiki_btn.setStyleSheet("background: #222; color: #0FF; border: 1px solid #0FF; font-weight: bold; padding: 5px;")
        wiki_btn.clicked.connect(lambda: webbrowser.open("https://helldivers.wiki.gg/wiki/Stratagems"))
        
        clear_btn = QPushButton("CLEAR ALL")
        clear_btn.setStyleSheet("background: #222; color: #F00; border: 1px solid #F00; font-weight: bold; padding: 5px;")
        clear_btn.clicked.connect(self.clear_all)
        
        btn_row.addWidget(wiki_btn)
        btn_row.addWidget(clear_btn)
        top_container.addLayout(btn_row)
        
        layout.addLayout(top_container)

        # --- STATUS & REINFORCE ---
        self.status = QLabel("DEMOCRACY READY")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #0F0; font-weight: bold; border: none; font-size: 16px;")
        layout.addWidget(self.status)

        # --- NUMPAD GRID ---
        grid = QGridLayout()
        self.btns = {}
        numpad_positions = {
            '7': (0, 0), '8': (0, 1), '9': (0, 2),
            '4': (1, 0), '5': (1, 1), '6': (1, 2),
            '1': (2, 0), '2': (2, 1), '3': (2, 2)
        }

        for k, pos in numpad_positions.items():
            btn = QPushButton(self)
            btn.setFixedSize(100, 100)
            btn.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")
            
            # Enable Right-Click
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, key=k: self.clear_single_bind(key))
            
            # --- Layering (Icon and Text) ---
            bg = QLabel(btn)
            bg.setFixedSize(100, 100)
            bg.setScaledContents(True)
            bg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            btn.bg = bg 
            
            txt = QLabel(btn)
            txt.setGeometry(0, 0, 100, 100)
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            txt.setWordWrap(True)
            txt.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent;")
            txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            btn.txt = txt 
            
            if k in self.active_binds:
                self.apply_visual(btn, k, self.active_binds[k])
            else:
                btn.txt.setText(f"{k}\nEMPTY")
            
            btn.clicked.connect(lambda ch, key=k: self.open_picker(key))
            grid.addWidget(btn, *pos)
            self.btns[k] = btn
        layout.addLayout(grid)

        # --- 4. REINFORCE (Now at the Bottom) ---
        reinf_btn = QPushButton("[0] REINFORCE (STATIC)")
        reinf_btn.setFixedSize(320, 45)
        reinf_btn.setStyleSheet("""
            background: #111; 
            border: 1px solid #FFD700; 
            color: #FFF; 
            font-weight: bold; 
            font-size: 13px;
            border-radius: 5px;
        """)
        # Optional: Add the icon to the static button too
        reinf_path = resource_path("icons/reinforce.svg")
        if os.path.exists(reinf_path):
            reinf_btn.setIcon(QIcon(reinf_path))
            reinf_btn.setIconSize(QSize(24, 24))
            
        layout.addWidget(reinf_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dev_label = QLabel("INPUT DEVICE:")
        dev_label.setStyleSheet("color: #FFD700; font-weight: bold; border: none; font-size: 10px; margin-top: 5px;")
        layout.addWidget(dev_label)

        self.dev_selector = QComboBox()
        # Force the dropdown to ignore its contents' width when calculating window size
        # self.dev_selector.setFixedWidth(250) 
        self.dev_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        # self.dev_selector.setTextElideMode(Qt.TextElideMode.ElideMiddle) # was trying to get the chosen device to Elide it's text
        self.dev_selector.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        # Force the popup list to resize to the width of its longest item
        self.dev_selector.view().setMinimumWidth(400) # Set this to a comfortable 'full' width
        self.dev_selector.setStyleSheet("""
            QComboBox { 
                background: #111; color: #FFD700; border: 1px solid #FFD700; 
                padding: 3px; font-size: 12px;
            }
            /* Style the popup list specifically */
            QComboBox QAbstractItemView { 
                background: #111; color: #FFD700; 
                selection-background-color: #333;
                outline: none;
                border: 1px solid #FFD700;
            }
        """)
        
        # Update the main window constraints to allow shrinking
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Populate with devices
        self.refresh_devices()

        # LOAD SAVED DEVICE
        saved_dev = self.settings.get('last_device', "")
        if saved_dev and isinstance(saved_dev, str):
            index = self.dev_selector.findText(saved_dev)
            if index == -1: 
                # If the exact "Name (eventX)" isn't found, try matching just the Name
                base_name = saved_dev.split(" (event")[0]
                for i in range(self.dev_selector.count()):
                    if self.dev_selector.itemText(i).startswith(base_name):
                        index = i
                        break
            if index >= 0:
                self.dev_selector.setCurrentIndex(index)

        self.dev_selector.currentIndexChanged.connect(self.restart_listener)
        layout.addWidget(self.dev_selector)

    def update_status_ui(self, chatting):
        self.status.setText("CHAT PAUSE" if chatting else "DEMOCRACY READY")
        self.status.setStyleSheet("color: #F00; font-weight: bold; border:none;" if chatting else "color: #0F0; font-weight: bold; border:none;")

    def save_settings(self):
        data = {
            "binds": self.active_binds,
            "last_device": self.dev_selector.currentText(),
            "show_names": self.show_text_cb.isChecked(),
            "ui_scale": self.scale_slider.value()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        self.settings = data

    def apply_global_scale(self, scale_val):
        base_size = 100
        new_size = int(base_size * (scale_val / 100))
        
        for btn in self.btns.values():
            btn.setFixedSize(new_size, new_size)
            btn.bg.setFixedSize(new_size, new_size)
            btn.txt.setGeometry(0, 0, new_size, new_size)
            
            # Refresh the background and font size
            btn.txt.setStyleSheet(f"""
                color: white; 
                font-weight: bold; 
                font-size: 12px; 
                background: rgba(0, 0, 0, 120);
            """)
        
        self.adjustSize()
        self.save_settings()

    def toggle_text_visibility(self):
        # Determine visibility based on checkbox state
        is_visible = self.show_text_cb.isChecked()
        
        # Loop through all 1-9 buttons and toggle their text layer
        for btn in self.btns.values():
            btn.txt.setVisible(is_visible)

        # Target ONLY the labels in the picker that are meant for text
        if hasattr(self, 'p') and self.p.isVisible():
            for label in self.p.findChildren(QLabel):
                # Only hide if it's NOT marked as an icon
                if label.property("is_icon") != True:
                    label.setVisible(is_visible)
        # Automatically save this preference
        self.save_settings()

    def refresh_devices(self):
        self.dev_map = {}
        for p in list_devices():
            try:
                d = InputDevice(p)
                caps = d.capabilities()
                name = d.name.lower()
                
                # Check for standard keyboard keys (like A-Z or Numpad)
                # Keyboards usually have KEY_A (30) or KEY_KP1 (79)
                has_kb_keys = False
                if e.EV_KEY in caps:
                    key_codes = caps[e.EV_KEY]
                    # Check if it has a broad range of keys or specific numpad keys
                    if 30 in key_codes or 79 in key_codes or len(key_codes) > 40:
                        has_kb_keys = True

                # Check for mouse movement
                has_mouse = e.EV_REL in caps or e.EV_ABS in caps
                
                # Block known "non-input" noise
                ignored = ["mic", "audio", "mono", "speaker", "headset", "webcam", "video", "power", "button"]
                if any(x in name for x in ignored):
                    continue

                if has_kb_keys or has_mouse:
                    # Append the path to the name to differentiate identical K70s
                    display_name = f"{d.name} ({p.split('/')[-1]})"
                    self.dev_map[display_name] = p
            except:
                continue

        self.dev_selector.clear()
        self.dev_selector.addItems(sorted(self.dev_map.keys()))

    def restart_listener(self):
        # Setting a flag to break the current loop
        self.listening = False
        time.sleep(0.2)

        # SAVE DEVICE TO SETTINGS
        current_name = self.dev_selector.currentText()
        if current_name:
            self.settings['last_device'] = current_name
            self.save_settings() # Helper to write to CONFIG_FILE

        threading.Thread(target=self.evdev_listener, daemon=True).start()

    def evdev_listener(self):
        global is_chatting
        self.listening = True
        
        current_name = self.dev_selector.currentText()
        if not current_name or current_name not in self.dev_map:
            return
        
        try:
            dev = InputDevice(self.dev_map[current_name])
            print(f"Listening to: {dev.name}")
            
            # Use non-blocking read or check the 'listening' flag
            for event in dev.read_loop():
                if not self.listening: break 
                
                if event.type == e.EV_KEY:
                    kev = categorize(event)
                    if kev.keystate == 1:
                        sc = kev.scancode
                    
                        # Chat Toggling
                        if sc == 28: # ENTER Key
                                is_chatting = not is_chatting
                                signals.chat_toggled.emit(is_chatting)
                                print(f"💬 Chat Mode: {'ON' if is_chatting else 'OFF'}")
                                continue # Don't process macros while toggling
                                
                        elif sc == 1: # Esc
                            if is_chatting:
                                is_chatting = False
                                signals.chat_toggled.emit(False)
                                print("Chat Mode: False (ESC)")
                            continue
                        
                        # Execute Macros
                        if sc == REINFORCE_SCAN: 
                            run_macro([UP, DN, RT, LT, UP])
                        elif sc in SCAN_TO_KEY:
                            key = SCAN_TO_KEY[sc]
                            if key in self.active_binds:
                                run_macro(self.active_binds[key]["seq"])
                    else:
                        continue

        except Exception as err:
            print(f"Device Error: {err}")

    def clear_single_bind(self, key):
        if key in self.active_binds:
            del self.active_binds[key]
            # Save the updated config
            with open(CONFIG_FILE, 'w') as f:
                # json.dump(self.active_binds, f)
                self.save_settings()
            
            # Reset visuals for this button
            btn = self.btns[key]
            btn.bg.clear()
            btn.txt.setText(f"{key}\nEMPTY")
            btn.txt.setGraphicsEffect(None) # Remove the text outline
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent;")
            btn.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")
            print(f"Cleared bind for Numpad {key}")

    def open_picker(self, key):
        self.p = QWidget()
        self.p.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.p.setStyleSheet("background: #0d0d0d; border: 2px solid #FFD700; border-radius: 10px;")
        
        main_layout = QVBoxLayout(self.p)

        # --- PICKER TOP BAR ---
        p_text_cb = QCheckBox("SHOW NAMES")
        p_text_cb.setChecked(self.show_text_cb.isChecked())
        p_text_cb.setStyleSheet("color: #FFD700; font-weight: bold; border: none;")
        p_text_cb.stateChanged.connect(lambda: [self.show_text_cb.setChecked(p_text_cb.isChecked()), self.toggle_text_visibility()]) # Link picker checkbox to main checkbox so they stay in sync
        main_layout.addWidget(p_text_cb)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(2) # Tighten space between categories

        # Apply the current scale to picker buttons
        scale_pct = self.scale_slider.value() / 100
        p_size = int(90 * scale_pct)

        self.picker_sections = {}

        for cat_name, items in STRATAGEM_DB.items():
            # Section Header
            header = QPushButton(f"▼ {cat_name.upper()}")
            header.setStyleSheet("""
                QPushButton { 
                    text-align: left; color: #FFD700; font-weight: bold; 
                    background: #222; border: 1px solid #444; padding: 5px; margin-top: 5px;
                }
            """)
            
            content_widget = QWidget()
            grid = QGridLayout(content_widget)
            
            # Load remembered collapsed state (Default to True/Visible)
            states = self.settings.get("collapsed_states", {})
            is_visible = states.get(cat_name, True)
            content_widget.setVisible(is_visible)
            header.setText(f"{'▼' if is_visible else '▶'} {cat_name.upper()}")
        
            for i, st in enumerate(items):
                b = QPushButton()
                b.setFixedSize(p_size, p_size)
                # b.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")

                # 1. THE ICON (Fills the whole 90x90 square)
                img = QLabel(b)
                img.setFixedSize(p_size, p_size)
                img.setProperty("is_icon", True) # TAG THIS AS AN ICON
                img.setScaledContents(True)
                path = resource_path(st['icon'])
                if os.path.exists(path):
                    img.setPixmap(QPixmap(path))
                else:
                    img.setText("ICON NOT FOUND")
                    img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

                # 2. THE TEXT OVERLAY (Now fills the whole 90x90 square)
                txt = QLabel(b)
                txt.setGeometry(0, 0, p_size, p_size)
                txt.setProperty("is_icon", False)
                txt.setWordWrap(True)
                txt.setText(st['name'])
                txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
                txt.setVisible(self.show_text_cb.isChecked())
                # Increased font size +2pt and made the background cover the whole button
                txt.setStyleSheet("""
                    color: white; 
                    font-weight: bold; 
                    font-size: 12px; 
                    background: rgba(0,0,0,120); 
                    border-radius: 5px;
                    padding: 2px;
                """)
                # txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

                b.clicked.connect(lambda ch, s=st: [self.assign(key, s), self.p.close()])
                grid.addWidget(b, i // 6, i % 6)

            # Toggle Logic
            header.clicked.connect(lambda ch, c=content_widget, h=header, n=cat_name: self.toggle_picker_section(c, h, n))
            
            container_layout.addWidget(header)
            container_layout.addWidget(content_widget)
            
        container_layout.addStretch(1)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        self.p.resize(int(635* scale_pct), 800)
        self.p.show()

    def toggle_picker_section(self, content, header, name):
        is_now_visible = not content.isVisible()
        content.setVisible(is_now_visible)
        header.setText(f"{'▼' if is_now_visible else '▶'} {name.upper()}")
        
        # Save state to settings
        if "collapsed_states" not in self.settings:
            self.settings["collapsed_states"] = {}
        self.settings["collapsed_states"][name] = is_now_visible
        self.save_settings()

    def load_picker_state(self, content, header, name):
        # Default to visible (True) if the key doesn't exist
        states = self.settings.get("collapsed_states", {})
        is_visible = states.get(name, True)
        
        content.setVisible(is_visible)
        header.setText(f"{'▼' if is_visible else '▶'} {name.upper()}")    

    def assign(self, key, strat):
        self.active_binds[key] = strat
        self.apply_visual(self.btns[key], key, strat)
        with open(CONFIG_FILE, 'w') as f: 
            # json.dump(self.active_binds, f)
            self.save_settings()

    def apply_visual(self, btn, key, strat):
        path = resource_path(strat['icon'])
        scale_val = self.scale_slider.value() / 100
        if os.path.exists(path):
            btn.bg.setPixmap(QPixmap(path))
            btn.bg.show()
            
            # --- THE TEXT + BACKGROUND LAYER ---
            # Using rgba(0,0,0,150) for a slightly darker, more readable tint
            btn.txt.setStyleSheet(f"""
                color: white; 
                font-weight: bold; 
                font-size: 12px; 
                background: rgba(0, 0, 0, 150);
                padding: 2px;
            """)            
            # Create a "Stroke/Outline" effect
            outline = QGraphicsDropShadowEffect()
            outline.setBlurRadius(2)
            outline.setXOffset(0)
            outline.setYOffset(0)
            outline.setColor(QColor(0, 0, 0, 255)) # Pure black outline
            btn.txt.setGraphicsEffect(outline)            
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: rgba(0,0,0,80);")        
        btn.txt.setText(f"{key}\n{strat['name']}")
        btn.txt.setVisible(self.show_text_cb.isChecked()) # Respect the Checkbox state
        btn.setStyleSheet("border: 1px solid #FFD700; border-radius: 5px;")

    def clear_all(self):
        self.active_binds = {}
        if CONFIG_FILE.exists(): CONFIG_FILE.unlink()
        for k, btn in self.btns.items():
            btn.bg.clear()
            btn.txt.setText(f"{k}\nEMPTY")
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent;")
            btn.setStyleSheet("background: #111; border: 1px solid #333;")

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except: return {}

if __name__ == '__main__':
    if not ui_device:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Fatal", "Permission Denied. Run: sudo usermod -aG input $USER")
        sys.exit(1)

    app = QApplication(sys.argv)
    
    # --- WAYLAND ICON SETTINGS ---
    # Points to icons/commander_tux-128.png
    app_icon_path = resource_path("icons/commander_tux-128.png")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))
        # Ensure Wayland recognizes the app for taskbar grouping
        app.setDesktopFileName("helltux") 

    win = HellTux()
    win.show()
    sys.exit(app.exec())