This entire project was 98% AI generated, but I told it exactly what I wanted, and what should change. The main thing to note here is that I don't know how to code Python. I barely know how to understand code... With that said:


# HellTux: Helldivers 2 Stratagem Macro Engine

**HellTux** is a high-performance, Python-based macro engine designed specifically for Helldivers 2 on Linux (CachyOS/Arch/Steam Deck). It provides a sleek PySide6 interface to bind and execute over 90+ Stratagems with a single keypress, using the native Linux `uinput` kernel module for undetectable, low-latency input.



## Main Features
* **90+ Stratagems:** Includes the latest "Orbital Napalm Barrage," "Sterilizer," and "Emancipator Exosuit."
* **Categorized UI:** Smart separation between "Standard" and "Mission-Specific" stratagems (Reinforce, Hellbomb, etc.).
* **Linux Native:** Built for Wayland, tested on CachyOS.
* **Smart Binding:** Prevention of duplicate keybinds and easy "Search-to-Bind" workflow.
* **Low Level:** Uses `python-uinput` to simulate hardware-level keyboard events.

---

## Prerequisites & Dependencies

### 1. System Packages (CachyOS / Arch)
You need the Python interpreter and the `uinput` kernel headers.
```bash
sudo pacman -S python python-pip libevdev

2. Python Requirements

It is recommended to use a virtual environment:
Bash

python -m venv .venv
source .venv/bin/activate.fish  # For Fish shell
# OR: source .venv/bin/activate # For Bash/Zsh

pip install PySide6 python-uinput

CRITICAL SETUP: UINPUT Permissions

Because HellTux simulates a keyboard, it needs permission to access /dev/uinput. This is the most important step.
1. Create the uinput group
Bash

sudo groupadd uinput
sudo usermod -aG uinput $USER

2. Set Udev Rules

Create a new rule file:
Bash

echo 'KERNEL=="uinput", GROUP="uinput", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules

3. 🚨 THE REBOOT (Don't skip!)

You MUST reboot your computer now. Udev rules and group assignments do not fully propagate to the kernel session until a fresh boot. If you skip this, the script will fail with a Permission Denied error.
How to Run

    Ensure your icons are in the icons/ folder.

    Launch the script:
    Bash

    python HellTux.py

    Use the Picker to select a Stratagem.

    Assign a key (e.g., F1, Num 1, or a side mouse button).

    Dive into a mission and spread Managed Democracy!

📜 Legal & Safety

HellTux simulates keypresses. While it does not read game memory or modify game files, always use macros responsibly. The developers are not responsible for any "Accidental" 500KG bombs dropped on teammates.

Developed with ❤️ on CachyOS for the Helldivers community.