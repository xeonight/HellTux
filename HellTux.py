import sys, os, json, time, requests, webbrowser, threading, zipfile, io, shutil
from pathlib import Path
from evdev import UInput, ecodes as e, list_devices, InputDevice, categorize
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QPushButton, 
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
    "Standard": [
        {"name": "Machine Gun", "icon": "icons/Machine_Gun.svg", "seq": [DN, LT, DN, UP, RT]},
        {"name": "Anti-Materiel Rifle", "icon": "icons/Anti-Materiel_Rifle.svg", "seq": [DN, LT, RT, UP, DN]},
        {"name": "Stalwart", "icon": "icons/Stalwart.svg", "seq": [DN, LT, DN, UP, UP, LT]},
        {"name": "Expendable Anti-Tank", "icon": "icons/Expendable_Anti-Tank.svg", "seq": [DN, DN, LT, UP, RT]},
        {"name": "Recoilless Rifle", "icon": "icons/Recoilless_Rifle.svg", "seq": [DN, LT, RT, RT, LT]},
        {"name": "Flamethrower", "icon": "icons/Flamethrower.svg", "seq": [DN, LT, UP, DN, UP]},
        {"name": "Autocannon", "icon": "icons/Autocannon.svg", "seq": [DN, LT, DN, UP, UP, RT]},
        {"name": "Heavy Machine Gun", "icon": "icons/Heavy_Machine_Gun.svg", "seq": [DN, LT, UP, DN, DN]},
        {"name": "Railgun", "icon": "icons/Railgun.svg", "seq": [DN, RT, DN, UP, LT, RT]},
        {"name": "Spear", "icon": "icons/Spear.svg", "seq": [DN, DN, UP, DN, DN]},
        {"name": "Orbital Precision Strike", "icon": "icons/Orbital_Precision_Strike.svg", "seq": [RT, RT, UP]},
        {"name": "Orbital Gatling Barrage", "icon": "icons/Orbital_Gatling_Barrage.svg", "seq": [RT, DN, LT, UP, UP]},
        {"name": "Orbital Airburst Strike", "icon": "icons/Orbital_Airburst_Strike.svg", "seq": [RT, RT, RT]},
        {"name": "Orbital 120MM HE Barrage", "icon": "icons/Orbital_120MM_HE_Barrage.svg", "seq": [RT, RT, DN, LT, RT, DN]},
        {"name": "Orbital 380MM HE Barrage", "icon": "icons/Orbital_380MM_HE_Barrage.svg", "seq": [RT, DN, UP, UP, LT, DN, DN]},
        {"name": "Orbital Walking Barrage", "icon": "icons/Orbital_Walking_Barrage.svg", "seq": [RT, DN, RT, DN, RT, DN]},
        {"name": "Orbital Laser", "icon": "icons/Orbital_Laser.svg", "seq": [RT, DN, UP, RT, DN]},
        {"name": "Orbital Railcannon Strike", "icon": "icons/Orbital_Railcannon_Strike.svg", "seq": [RT, UP, DN, DN, RT]},
        {"name": "Orbital Gas Strike", "icon": "icons/Orbital_Gas_Strike.svg", "seq": [RT, RT, DN, RT]},
        {"name": "Orbital EMS Strike", "icon": "icons/Orbital_EMS_Strike.svg", "seq": [RT, RT, LT, DN]},
        {"name": "Orbital Smoke Strike", "icon": "icons/Orbital_Smoke_Strike.svg", "seq": [RT, RT, DN, UP]},
        {"name": "Orbital Napalm Barrage", "icon": "icons/Orbital_Napalm_Barrage.svg", "seq": [RT, RT, DN, UP, DN]},
        {"name": "Eagle Strafing Run", "icon": "icons/Eagle_Strafing_Run.svg", "seq": [UP, RT, RT]},
        {"name": "Eagle Airstrike", "icon": "icons/Eagle_Airstrike.svg", "seq": [UP, RT, DN, RT]},
        {"name": "Eagle Cluster Bomb", "icon": "icons/Eagle_Cluster_Bomb.svg", "seq": [UP, RT, DN, DN, RT]},
        {"name": "Eagle Napalm Airstrike", "icon": "icons/Eagle_Napalm_Airstrike.svg", "seq": [UP, RT, DN, UP]},
        {"name": "Eagle Smoke Strike", "icon": "icons/Eagle_Smoke_Strike.svg", "seq": [UP, RT, UP, DN]},
        {"name": "Eagle 110MM Rocket Pods", "icon": "icons/Eagle_110MM_Rocket_Pods.svg", "seq": [UP, RT, UP, LT]},
        {"name": "Eagle 500KG Bomb", "icon": "icons/Eagle_500KG_Bomb.svg", "seq": [UP, RT, DN, DN, DN]},
        {"name": "Supply Pack", "icon": "icons/Supply_Pack.svg", "seq": [DN, LT, DN, UP, UP, DN]},
        {"name": "Jump Pack", "icon": "icons/Jump_Pack.svg", "seq": [DN, UP, UP, DN, UP]},
        {"name": "Guard Dog Rover", "icon": "icons/Guard_Dog_Rover.svg", "seq": [DN, UP, LT, UP, RT, RT]},
        {"name": "Guard Dog", "icon": "icons/Guard_Dog.svg", "seq": [DN, UP, LT, UP, RT, DN]},
        {"name": "Ballistic Shield", "icon": "icons/Ballistic_Shield_Backpack.svg", "seq": [DN, LT, DN, DN, UP, LT]},
        {"name": "Shield Generator Pack", "icon": "icons/Shield_Generator_Pack.svg", "seq": [DN, UP, LT, RT, LT, RT]},
        {"name": "Arc Thrower", "icon": "icons/Arc_Thrower.svg", "seq": [DN, RT, DN, UP, LT, LT]},
        {"name": "Quasar Cannon", "icon": "icons/Quasar_Cannon.svg", "seq": [DN, DN, UP, LT, RT]},
        {"name": "Sterilizer", "icon": "icons/Sterilizer.svg", "seq": [DN, LT, DN, DN, UP, LT]},
        {"name": "Tesla Tower", "icon": "icons/Tesla_Tower.svg", "seq": [DN, UP, RT, UP, LT, RT]},
        {"name": "Anti-Personnel Minefield", "icon": "icons/Anti-Personnel_Minefield.svg", "seq": [DN, LT, UP, RT]},
        {"name": "Incendiary Mines", "icon": "icons/Incendiary_Mines.svg", "seq": [DN, LT, LT, DN]},
        {"name": "Anti-Tank Mines", "icon": "icons/Anti-Tank_Mines.svg", "seq": [DN, LT, UP, UP]},
        {"name": "Machine Gun Sentry", "icon": "icons/Machine_Gun_Sentry.svg", "seq": [DN, UP, RT, RT, UP]},
        {"name": "Gatling Sentry", "icon": "icons/Gatling_Sentry.svg", "seq": [DN, UP, RT, LT]},
        {"name": "Mortar Sentry", "icon": "icons/Mortar_Sentry.svg", "seq": [DN, UP, RT, RT, DN]},
        {"name": "Autocannon Sentry", "icon": "icons/Autocannon_Sentry.svg", "seq": [DN, UP, RT, UP, LT, UP]},
        {"name": "Rocket Sentry", "icon": "icons/Rocket_Sentry.svg", "seq": [DN, UP, RT, RT, LT]},
        {"name": "EMS Mortar Sentry", "icon": "icons/EMS_Mortar_Sentry.svg", "seq": [DN, UP, RT, DN, RT]},
        {"name": "Patriot Exosuit", "icon": "icons/Patriot_Exosuit.svg", "seq": [LT, DN, RT, UP, LT, DN, DN]},
        {"name": "Emancipator Exosuit", "icon": "icons/Emancipator_Exosuit.svg", "seq": [LT, DN, RT, UP, LT, DN, UP]}
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
        {"name": "Orbital Illumination Flare", "icon": "icons/Orbital_Illumination_Flare.svg", "seq": [RT, RT, LT, LT]}
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
            print(f"✅ Assets Synced (Case-Insensitive): {len(found_svgs)} icons.")
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
        self.active_binds = self.load_config()
        self.initUI()
        signals.chat_toggled.connect(self.update_status_ui)
        threading.Thread(target=self.evdev_listener, daemon=True).start()

    def initUI(self):
        self.setWindowTitle("HellTux")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: #000; color: #FFD700; border: 1px solid #FFD700;")
        layout = QVBoxLayout(self)
        
        # --- TOP CONTROL BAR ---
        ctrl_layout = QHBoxLayout()
        wiki_btn = QPushButton("WIKI")
        wiki_btn.setStyleSheet("background: #222; color: #0FF; border: 1px solid #0FF; font-weight: bold; padding: 5px;")
        wiki_btn.clicked.connect(lambda: webbrowser.open("https://helldivers.wiki.gg/wiki/Stratagems"))
        
        clear_btn = QPushButton("CLEAR ALL")
        clear_btn.setStyleSheet("background: #222; color: #F00; border: 1px solid #F00; font-weight: bold; padding: 5px;")
        clear_btn.clicked.connect(self.clear_all)
        
        ctrl_layout.addWidget(wiki_btn)
        ctrl_layout.addWidget(clear_btn)
        layout.addLayout(ctrl_layout)

        # --- STATUS & REINFORCE ---
        self.status = QLabel("DEMOCRACY READY")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #0F0; font-weight: bold; border: none; font-size: 16px;") # +2pt (14->16)
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
            txt.setStyleSheet("color: white; font-weight: bold; font-size: 11px; background: transparent;")
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

    def update_status_ui(self, chatting):
        self.status.setText("CHAT PAUSE" if chatting else "DEMOCRACY READY")
        self.status.setStyleSheet("color: #F00; font-weight: bold; border:none;" if chatting else "color: #0F0; font-weight: bold; border:none;")

    def evdev_listener(self):
        global is_chatting
        dev = None
        for p in list_devices():
            d = InputDevice(p)
            if e.KEY_A in d.capabilities().get(e.EV_KEY, []):
                dev = d; break
        if not dev: return
        for event in dev.read_loop():
            if event.type == e.EV_KEY:
                kev = categorize(event)
                if kev.keystate == 1:
                    sc = kev.scancode
                    if sc == 28: # Enter
                        is_chatting = not is_chatting
                        signals.chat_toggled.emit(is_chatting)
                    elif sc == 1 and is_chatting: # Esc
                        is_chatting = False
                        signals.chat_toggled.emit(False)
                    if is_chatting: continue
                    if sc == REINFORCE_SCAN: run_macro([UP, DN, RT, LT, UP])
                    elif sc in SCAN_TO_KEY:
                        key = SCAN_TO_KEY[sc]
                        if key in self.active_binds: run_macro(self.active_binds[key]["seq"])

    def clear_single_bind(self, key):
        if key in self.active_binds:
            del self.active_binds[key]
            # Save the updated config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.active_binds, f)
            
            # Reset visuals for this button
            btn = self.btns[key]
            btn.bg.clear()
            btn.txt.setText(f"{key}\nEMPTY")
            btn.txt.setGraphicsEffect(None) # Remove the text outline
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 11px; background: transparent;")
            btn.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")
            print(f"🗑️ Cleared bind for Numpad {key}")

    def open_picker(self, key):
        self.p = QWidget()
        self.p.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.p.setStyleSheet("background: #0d0d0d; border: 2px solid #FFD700; border-radius: 10px;")
        
        main_layout = QVBoxLayout(self.p)
        scroll = QScrollArea()
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        grid = QGridLayout(container)
        
        # Flatten the categorized dict into a single list of all stratagems
        all_strats = []
        for category_list in STRATAGEM_DB.values():
            all_strats.extend(category_list)

        # Now use 'all_strats' instead of 'STRATAGEMS'
        active_names = [b['name'] for b in self.active_binds.values()]
        avail = [st for st in all_strats if st['name'] not in active_names]
        
        for i, st in enumerate(avail):
            b = QPushButton(container)
            b.setFixedSize(90, 90)
            b.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 5px;")
            
            # 1. THE ICON (Fills the whole 90x90 square)
            img = QLabel(b)
            img.setFixedSize(90, 90)
            img.setScaledContents(True)
            path = resource_path(st['icon'])
            if os.path.exists(path):
                img.setPixmap(QPixmap(path))
            else:
                img.setText("📦")
                img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            # 2. THE TEXT OVERLAY (Now fills the whole 90x90 square)
            txt = QLabel(b)
            txt.setGeometry(0, 0, 90, 90) # Change: 0, 45, 90, 45 -> 0, 0, 90, 90
            txt.setWordWrap(True)
            txt.setText(st['name'])
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Increased font size +2pt and made the background cover the whole button
            txt.setStyleSheet("""
                color: white; 
                font-weight: bold; 
                font-size: 11px; 
                background: rgba(0,0,0,120); 
                border-radius: 5px;
                padding: 5px;
            """)
            txt.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            
            b.clicked.connect(lambda ch, s=st: [self.assign(key, s), self.p.close()])
            grid.addWidget(b, i // 6, i % 6)
            
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        self.p.resize(620, 550)
        self.p.show()

    def assign(self, key, strat):
        self.active_binds[key] = strat
        self.apply_visual(self.btns[key], key, strat)
        with open(CONFIG_FILE, 'w') as f: json.dump(self.active_binds, f)

    def apply_visual(self, btn, key, strat):
        path = resource_path(strat['icon'])
        if os.path.exists(path):
            btn.bg.setPixmap(QPixmap(path))            
            # Create a "Stroke/Outline" effect
            outline = QGraphicsDropShadowEffect()
            outline.setBlurRadius(2)
            outline.setXOffset(0)
            outline.setYOffset(0)
            outline.setColor(QColor(0, 0, 0, 255)) # Pure black outline
            btn.txt.setGraphicsEffect(outline)            
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 11px; background: rgba(0,0,0,80);")        
        btn.txt.setText(f"{key}\n{strat['name']}")
        btn.setStyleSheet("border: 1px solid #FFD700; border-radius: 5px;")

    def clear_all(self):
        self.active_binds = {}
        if CONFIG_FILE.exists(): CONFIG_FILE.unlink()
        for k, btn in self.btns.items():
            btn.bg.clear()
            btn.txt.setText(f"{k}\nEMPTY")
            btn.txt.setStyleSheet("color: white; font-weight: bold; font-size: 11px; background: transparent;")
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