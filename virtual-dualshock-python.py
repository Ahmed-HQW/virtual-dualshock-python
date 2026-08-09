import urllib.parse
import os
import sys
import json
import time
import shutil
import threading
import subprocess
import configparser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ============================================================
# DEEP EDIT v2 — Multi-Profile DualShock Virtual Gamepad Server
# PC DualShock / PS2 DualShock / PS4 DualShock
# ============================================================

PORT = 8080

# ------------------------------------------------------------
# UI / Visual base config (شارك بين البروفايلات الثلاثة)
# ------------------------------------------------------------
UI_BASE = {
    "PORT": PORT,
    "CONTROLLER_SCALE": 1.0,
    "UI_OPACITY": 0.98,
    "LIGHTBAR_GLOW_INTENSITY": 20,
    "SAFE_AREA_LEFT": 30,
    "SAFE_AREA_RIGHT": 30,
    "DPAD_SIZE": 44,
    "ACTION_BTNS_SIZE": 52,
    "STICK_CONTAINER_SIZE": 118,
    "STICK_KNOB_SIZE": 58,
    "TOUCHPAD_WIDTH": 190,
    "TOUCHPAD_HEIGHT": 62,

    "ANALOG_DEADZONE": 0.22,
    "ANALOG_SENSITIVITY": 1.6,
    "ANALOG_MAX_RANGE": 32,
    "PREVENT_KEY_GHOSTING": True,
    "KEY_RELEASE_DELAY": 0,

    "SOUND_CLICK_ENABLED": True,
    "SOUND_CLICK_FREQ": 1200,
    "SOUND_CLICK_VOLUME": 0.15,
    "VIBRATION_ENABLED": True,
    "VIBRATION_DURATION": 20,
    "FULLSCREEN_AUTO_LOCK": True,
    "MULTI_TOUCH_OPTIMIZED": True,
    "NO_EXTERNAL_DEPS": True,
    "SERVER_THREADING": True,
}

# ------------------------------------------------------------
# PROFILE 1: PC DualShock — bindings مريحة لأي لعبة PC عادية (WASD مألوف)
# ------------------------------------------------------------
PROFILE_PC = {
    "LABEL": "PC DualShock",
    "LIGHTBAR_COLOR": "#0080FF",
    "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
    "KEY_TRIANGLE": "u", "KEY_CIRCLE": "o", "KEY_SQUARE": "i", "KEY_CROSS": "j",
    "KEY_L1": "q", "KEY_L2": "1", "KEY_R1": "e", "KEY_R2": "3",
    "KEY_L3": "z", "KEY_R3": "x",
    "KEY_SHARE": "Tab", "KEY_OPTIONS": "Return", "KEY_PS": "Escape",
    "LS_UP": "w", "LS_DOWN": "s", "LS_LEFT": "a", "LS_RIGHT": "d",
    "RS_UP": "KP_8", "RS_DOWN": "KP_2", "RS_LEFT": "KP_4", "RS_RIGHT": "KP_6",
    "RS_TRICK_ISOLATION": False,
    "ANALOG_RAMP_LIMIT": 200,
    "LS_TYPE": "digital_direct", "RS_TYPE": "digital_direct",
}

# ------------------------------------------------------------
# PROFILE 2: PS2 DualShock — منسوخة بالضبط من صورة إعدادات PCSX2
# (منفذ التحكم 1، DualShock 2) اللي تصورتها. Source of truth = الصورة.
# ------------------------------------------------------------
PROFILE_PS2 = {
    "LABEL": "PS2 DualShock",
    "LIGHTBAR_COLOR": "#0080FF",
    # D-Pad — Keyboard Up/Down/Left/Right (كيفما فالصورة بالضبط)
    "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
    # Face Buttons — Triangle=I, Circle=L, Square=J, Cross=K
    "KEY_TRIANGLE": "i", "KEY_CIRCLE": "l", "KEY_SQUARE": "j", "KEY_CROSS": "k",
    # Shoulders — L1=Q, L2=1, R1=E, R2=3
    "KEY_L1": "q", "KEY_L2": "1", "KEY_R1": "e", "KEY_R2": "3",
    # Sticks click — L3=2, R3=4
    "KEY_L3": "2", "KEY_R3": "4",
    # Start=Return, Select=BackSpace, PS/Analog toggle مربوط بـ Escape افتراضياً (ماكاينش فالصورة)
    "KEY_SHARE": "BackSpace", "KEY_OPTIONS": "Return", "KEY_PS": "Escape",
    # Left stick — W/A/S/D بالضبط كيفما فالصورة
    "LS_UP": "w", "LS_DOWN": "s", "LS_LEFT": "a", "LS_RIGHT": "d",
    # Right stick — Up=T, Down=G, Left=F, Right=H بالضبط كيفما فالصورة
    "RS_UP": "t", "RS_DOWN": "g", "RS_LEFT": "f", "RS_RIGHT": "h",
    "RS_TRICK_ISOLATION": True,
    "ANALOG_RAMP_LIMIT": 90,
    "LS_TYPE": "digital_direct", "RS_TYPE": "digital_direct",
}

# ------------------------------------------------------------
# PROFILE 3: PS4 DualShock — bindings مختلفة باش تخدم بيها PS4 emulators (RPCS3/Shadps4)
# أو أي كونفيغ كيتسنى DS4 layout classic
# ------------------------------------------------------------
PROFILE_PS4 = {
    "LABEL": "PS4 DualShock",
    "LIGHTBAR_COLOR": "#00c6ff",
    "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
    "KEY_TRIANGLE": "y", "KEY_CIRCLE": "period", "KEY_SQUARE": "comma", "KEY_CROSS": "n",
    "KEY_L1": "1", "KEY_L2": "2", "KEY_R1": "9", "KEY_R2": "0",
    "KEY_L3": "c", "KEY_R3": "m",
    "KEY_SHARE": "F2", "KEY_OPTIONS": "F3", "KEY_PS": "F1",
    "LS_UP": "w", "LS_DOWN": "s", "LS_LEFT": "a", "LS_RIGHT": "d",
    "RS_UP": "KP_8", "RS_DOWN": "KP_2", "RS_LEFT": "KP_4", "RS_RIGHT": "KP_6",
    "RS_TRICK_ISOLATION": True,
    "ANALOG_RAMP_LIMIT": 140,
    "LS_TYPE": "digital_direct", "RS_TYPE": "digital_direct",
}

PROFILES = {
    "pc": {**UI_BASE, **PROFILE_PC},
    "ps2": {**UI_BASE, **PROFILE_PS2},
    "ps4": {**UI_BASE, **PROFILE_PS4},
}

DEFAULT_PROFILE_KEY = "ps2"


def validate_profile(cfg: dict, name: str):
    """كتأكد بلي ماكايناش أي تعارض بين مفاتيح الأزرار ومفاتيح الأنالوج (Key Ghosting)."""
    action_keys = {
        cfg["KEY_CROSS"], cfg["KEY_CIRCLE"], cfg["KEY_SQUARE"], cfg["KEY_TRIANGLE"],
        cfg["KEY_L1"], cfg["KEY_L2"], cfg["KEY_R1"], cfg["KEY_R2"],
        cfg["KEY_L3"], cfg["KEY_R3"],
        cfg["KEY_UP"], cfg["KEY_DOWN"], cfg["KEY_LEFT"], cfg["KEY_RIGHT"],
    }
    analog_keys = {
        cfg["LS_UP"], cfg["LS_DOWN"], cfg["LS_LEFT"], cfg["LS_RIGHT"],
        cfg["RS_UP"], cfg["RS_DOWN"], cfg["RS_LEFT"], cfg["RS_RIGHT"],
    }
    conflict = action_keys & analog_keys
    if conflict:
        raise ValueError(
            f"[{name}] تعارض مفاتيح (Key Ghosting risk): {conflict}. "
            f"بدّل واحد منهم فالبروفايل قبل ما تشغل السيرفر."
        )


for _name, _cfg in PROFILES.items():
    validate_profile(_cfg, _name)

PROFILES_JSON = json.dumps(PROFILES, ensure_ascii=False)
# ============================================================
# PCSX2 Auto-Launch + Auto-Configure (best-effort, safe)
# ============================================================
# ملاحظة صريحة: PCSX2 الحديثة (Qt) كتخزن bindings الـ Pad فـ INI
# باسم فيه أرقام السلاسل (SDL keycodes) ماشي بسمية "Q"/"W" مباشرة،
# وهاد التنسيق كيتبدل بين نسخة ونسخة. باش نبقاو أمينين، هاد الفانكسيون
# كتدير detect للمسار، كتاخد backup قبل أي تعديل، وكتكتب القيم اللي
# قادرة تضمنها (SDL keyboard mapping بصيغة Keyboard/<Key>).
# إلا PCSX2 ماكانتش مثبتة أو المسار ماتلقاش، كتسكت بلا ما توقف السيرفر.

PCSX2_CANDIDATE_CONFIG_DIRS = [
    os.path.expanduser("~/.config/PCSX2/inis"),
    os.path.expanduser("~/.var/app/net.pcsx2.PCSX2/config/PCSX2/inis"),  # Flatpak
    os.path.expanduser("~/PCSX2/inis"),
]

PCSX2_CANDIDATE_BINARIES = [
    "pcsx2", "pcsx2-qt", "PCSX2",
    "/usr/bin/pcsx2", "/usr/bin/pcsx2-qt",
    "/usr/local/bin/pcsx2",
    "flatpak run net.pcsx2.PCSX2",
]


def find_pcsx2_binary():
    for candidate in PCSX2_CANDIDATE_BINARIES:
        if candidate.startswith("flatpak"):
            if shutil.which("flatpak"):
                check = subprocess.run(
                    ["flatpak", "list", "--app", "--columns=application"],
                    capture_output=True, text=True
                )
                if "net.pcsx2.PCSX2" in check.stdout:
                    return ["flatpak", "run", "net.pcsx2.PCSX2"]
            continue
        path = shutil.which(candidate) if not candidate.startswith("/") else (candidate if os.path.isfile(candidate) else None)
        if path:
            return [path]
    return None


def find_pcsx2_config_dir():
    for d in PCSX2_CANDIDATE_CONFIG_DIRS:
        if os.path.isdir(d):
            return d
    return None


def launch_pcsx2():
    """كتلانسي PCSX2 فـ subprocess منفصل (بلا ما توقف السيرفر ديال gamepad)."""
    binary = find_pcsx2_binary()
    if not binary:
        print("⚠ PCSX2 ماتلقاتش فالنظام (PATH). خصك تلانسيها يدوياً، أو زيد المسار فـ PCSX2_CANDIDATE_BINARIES.")
        return None
    try:
        proc = subprocess.Popen(
            binary,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(f"✔ PCSX2 تلانسات (PID {proc.pid}) عبر: {' '.join(binary)}")
        return proc
    except Exception as e:
        print(f"⚠ فشل لانسي PCSX2: {e}")
        return None


def _sdl_keyboard_token(key_name: str) -> str:
    """
    كيبدل سمية المفتاح (زي اللي مستعملين فـ xdotool، مثلا 'w', 'Up', 'KP_8')
    لصيغة قريبة من SDL keyboard binding string اللي كيفهمها PCSX2 Qt
    (Keyboard/<SDL_KeyName>). هاد التحويل بسيط وكيغطي المفاتيح
    الشائعة المستعملة فالبروفايلات ديالنا فقط — ماشي مترجم شامل.
    """
    special_map = {
        "Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right",
        "Return": "Return", "Escape": "Escape", "Tab": "Tab",
        "BackSpace": "Backspace",
        "KP_8": "Keypad 8", "KP_2": "Keypad 2", "KP_4": "Keypad 4", "KP_6": "Keypad 6",
        "period": "Period", "comma": "Comma",
        "F1": "F1", "F2": "F2", "F3": "F3",
    }
    if key_name in special_map:
        return f"Keyboard/{special_map[key_name]}"
    if len(key_name) == 1:
        return f"Keyboard/{key_name.upper()}"
    if key_name.isdigit():
        return f"Keyboard/{key_name}"
    return f"Keyboard/{key_name.capitalize()}"


# خريطة: مفتاح البروفايل عندنا -> اسم الـ binding فملف PCSX2 Pad INI
PCSX2_PAD_FIELD_MAP = {
    "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
    "KEY_TRIANGLE": "Triangle", "KEY_CIRCLE": "Circle", "KEY_SQUARE": "Square", "KEY_CROSS": "Cross",
    "KEY_L1": "L1", "KEY_L2": "L2", "KEY_R1": "R1", "KEY_R2": "R2",
    "KEY_L3": "L3", "KEY_R3": "R3",
    "KEY_SHARE": "Select", "KEY_OPTIONS": "Start",
    "LS_UP": "LUp", "LS_DOWN": "LDown", "LS_LEFT": "LLeft", "LS_RIGHT": "LRight",
    "RS_UP": "RUp", "RS_DOWN": "RDown", "RS_LEFT": "RLeft", "RS_RIGHT": "RRight",
}


def apply_pcsx2_pad_config(profile_cfg: dict, pad_section: str = "Pad1"):
    """
    كتكتب bindings البروفايل الحالي فملف Pad INI ديال PCSX2 (best-effort).
    - كتاخد نسخة احتياطية (.bak) قبل أي تعديل.
    - إلا المسار ماتلقاش، كترجع False بلا ما تكسر شي حاجة.
    - PCSX2 خاصها تكون مغلقة وقت الكتابة باش التغييرات ماتنمحاوش.
    """
    config_dir = find_pcsx2_config_dir()
    if not config_dir:
        print("⚠ ماتلقا مجلد إعدادات PCSX2 (~/.config/PCSX2/inis). تخطي auto-config.")
        return False

    pad_file = os.path.join(config_dir, "PAD.ini")
    if not os.path.isfile(pad_file):
        print(f"⚠ ماتلقا PAD.ini فـ {config_dir}. تخطي auto-config (خصك تدير أول لانسمون يدوي لـ PCSX2 باش يخلق الملفات).")
        return False

    try:
        backup_path = pad_file + ".bak"
        if not os.path.isfile(backup_path):
            shutil.copy2(pad_file, backup_path)
            print(f"✔ نسخة احتياطية دارت: {backup_path}")

        parser = configparser.ConfigParser(strict=False)
        parser.optionxform = str  # حافظ على حالة الأحرف (case-sensitive)
        parser.read(pad_file, encoding="utf-8")

        if pad_section not in parser:
            parser[pad_section] = {}

        for cfg_key, ini_field in PCSX2_PAD_FIELD_MAP.items():
            if cfg_key in profile_cfg:
                parser[pad_section][ini_field] = _sdl_keyboard_token(profile_cfg[cfg_key])

        with open(pad_file, "w", encoding="utf-8") as f:
            parser.write(f)

        print(f"✔ PCSX2 PAD.ini تحدّث بنجاح ({pad_section}) — بروفايل: {profile_cfg.get('LABEL')}")
        print("  ملاحظة: خاص PCSX2 تكون مغلقة وقت الكتابة، وخصك تعاود تلانسيها باش التغييرات تبان.")
        return True
    except Exception as e:
        print(f"⚠ فشل تعديل PAD.ini: {e}")
        return False
# ============================================================
# Thermal Monitor (READ-ONLY, بلا صلاحيات root، بلا تعديل kernel)
# ============================================================
# ملاحظة مهمة: هاد الجزء كيقرا الحرارة فقط ويعطي تنبيه فالتيرمينال.
# ماكيبدلش CPU governor ولا كيدير undervolt/overclock ولا كيلمس
# /sys/class/thermal بالكتابة. هادشي مقصود: تعديلات kernel-level
# فالحرارة والفريكونس بلا فهم دقيق للجهاز = خطر حقيقي (تلف هاردوير
# أو throttle عكسي)، خصوصا فمعالج قديم زي i3-4005U.
#
# إلا بغيتي تحكم فعلي فالـ CPU governor، الطريقة الآمنة هي تستعمل
# أدوات جاهزة ومختبرة (cpupower, thermald, tlp) عبر sudo يدوياً —
# ماشي سكريبت كيكتب فالـ kernel بلا تحكم ديالك.

THERMAL_ZONE_PATHS = [
    "/sys/class/thermal/thermal_zone0/temp",
    "/sys/class/thermal/thermal_zone1/temp",
]

THERMAL_WARN_C = 80.0
THERMAL_POLL_INTERVAL_SEC = 5


def read_cpu_temp_c():
    """كتقرا الحرارة الحالية (Celsius) من أول thermal zone صالحة. كترجع None إلا ماتلقاتش."""
    for path in THERMAL_ZONE_PATHS:
        try:
            with open(path, "r") as f:
                raw = f.read().strip()
                milli = int(raw)
                return milli / 1000.0
        except (FileNotFoundError, PermissionError, ValueError):
            continue
    return None


def thermal_monitor_loop(stop_event: threading.Event):
    """
    Thread فالخلفية: كيقرا الحرارة كل بضع ثواني وكيعطي تنبيه فالتيرمينال
    إلا فاق THERMAL_WARN_C. بلا أي تدخل فالنظام — قراءة فقط.
    """
    warned = False
    while not stop_event.is_set():
        temp = read_cpu_temp_c()
        if temp is not None:
            if temp >= THERMAL_WARN_C and not warned:
                print(f"🌡 تنبيه: حرارة المعالج {temp:.1f}°C — فاقت {THERMAL_WARN_C:.0f}°C. "
                      f"نصيحة: خفف الإضاءة الخلفية، سد التطبيقات الزايدة، أو دير تهوية أحسن للجهاز.")
                warned = True
            elif temp < THERMAL_WARN_C - 5:
                warned = False  # reset التنبيه إلا برد الجهاز شوية (hysteresis)
        stop_event.wait(THERMAL_POLL_INTERVAL_SEC)


def start_thermal_monitor():
    """كيبدا الـ thread ديال المراقبة، كيرجع (thread, stop_event) باش تقدر توقفو."""
    stop_event = threading.Event()
    t = threading.Thread(target=thermal_monitor_loop, args=(stop_event,), daemon=True)
    t.start()
    return t, stop_event
HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover, orientation=landscape">
<title>DualShock Multi-Profile Gamepad</title>
<style>
* { box-sizing: border-box; -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; touch-action: none; }
html, body {
    background: #000; color: #222; margin: 0; padding: 0;
    height: 100vh; width: 100vw; overflow: hidden; font-family: -apple-system, Arial, sans-serif;
}

/* ============ START / PROFILE SELECT SCREEN ============ */
#start-screen {
    position: fixed; inset: 0; background: radial-gradient(circle at 50% 40%, #1a1a1f, #000);
    z-index: 9999; display: flex; justify-content: center; align-items: center; flex-direction: column; color: #fff;
    overflow-y: auto; padding: 20px 0;
}
#start-screen h2 { margin-bottom: 4px; font-size: 20px; }
#start-screen p { color: #888; font-size: 12px; margin-top: 0; }

.profile-select {
    display: flex; gap: 12px; margin: 14px 0; flex-wrap: wrap; justify-content: center; max-width: 90vw;
}
.profile-card {
    background: linear-gradient(160deg,#232328,#141417);
    border: 2px solid #333338; border-radius: 16px; padding: 14px 18px;
    cursor: pointer; text-align: center; min-width: 120px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
}
.profile-card:active { transform: scale(0.96); }
.profile-card.selected {
    border-color: #00c6ff;
    box-shadow: 0 0 0 2px rgba(0,198,255,0.35), 0 8px 20px rgba(0,150,255,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
}
.profile-card .icon { font-size: 28px; margin-bottom: 6px; }
.profile-card .name { font-size: 13px; font-weight: bold; color: #eee; }
.profile-card .sub { font-size: 10px; color: #888; margin-top: 3px; }

#start-btn {
    padding: 16px 38px; font-size: 20px; background: linear-gradient(135deg,#0080FF,#00c6ff);
    border: none; border-radius: 30px; font-weight: bold; cursor: pointer; color: #fff;
    margin-top: 14px; box-shadow: 0 8px 24px rgba(0,128,255,0.5), inset 0 2px 0 rgba(255,255,255,0.25), inset 0 -3px 6px rgba(0,0,0,0.25);
}
#start-btn:active { transform: translateY(2px); box-shadow: 0 4px 12px rgba(0,128,255,0.45); }

.scale-control {
    margin: 10px 0; display: flex; align-items: center; gap: 12px;
    background: #16161a; padding: 10px 20px; border-radius: 12px; border: 1px solid #2a2a30;
}
.scale-control label { font-size: 13px; color: #ccc; }
.scale-control input[type="range"] { cursor: pointer; width: 150px; }
#scaleVal { font-weight: bold; color: #00c6ff; min-width: 42px; text-align: center; font-size: 13px; }

/* Accessibility panel (Huawei P20 Lite tuned) */
.access-panel {
    margin: 6px 0; background: #16161a; border: 1px solid #2a2a30; border-radius: 12px;
    padding: 10px 18px; display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; max-width: 92vw;
}
.access-item { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #ccc; }
.access-item input[type="range"] { width: 90px; }
.access-item input[type="checkbox"] { width: 16px; height: 16px; }

/* ============ PAD SCREEN ============ */
#pad {
    display: none; position: fixed; inset: 0; width: 100%; height: 100%;
    transform-origin: center center;
    padding-left: calc(env(safe-area-inset-left, 0px) + var(--safe-left));
    padding-right: calc(env(safe-area-inset-right, 0px) + var(--safe-right));
    background: radial-gradient(ellipse at 50% 0%, #2c2c32 0%, #19191c 55%, #0c0c0e 100%);
    opacity: var(--ui-opacity);
    filter: contrast(var(--access-contrast, 1)) brightness(var(--access-brightness, 1));
}

#lightbar {
    position: absolute; top: 0; left: 50%; transform: translateX(-50%);
    width: 140px; height: 8px; border-radius: 0 0 8px 8px;
    background: var(--lb-color);
    box-shadow: 0 0 var(--lb-glow) var(--lb-glow) var(--lb-color), 0 0 6px 2px var(--lb-color);
}

/* ============ 3D BUTTON SYSTEM ============
   كل زر عندو: طبقة قاعدية غامقة (تعطي عمق) + طبقة علوية بـ gradient
   + inset highlight فالأعلى (ضوء) + inset shadow فالأسفل (عمق) +
   drop-shadow خارجي (يرفعو عن السطح) + انيميشن ضغط واقعي (translateY + تصغير الظل)
*/
.shoulder {
    position: absolute;
    background: linear-gradient(180deg,#5a5a64 0%,#3a3a42 45%,#26262c 100%);
    border: 1px solid #1a1a1e; color: #f0f0f0; font-size: 15px; font-weight: bold;
    display: flex; justify-content: center; align-items: center;
    border-radius: 10px;
    box-shadow:
        0 6px 0 #131316,
        0 10px 16px rgba(0,0,0,0.55),
        inset 0 2px 2px rgba(255,255,255,0.25),
        inset 0 -3px 4px rgba(0,0,0,0.35);
    transition: transform 0.05s ease, box-shadow 0.05s ease;
}
.shoulder:active, .shoulder.active {
    background: linear-gradient(180deg,#6a6a75,#3a3a42);
    transform: translateY(4px);
    box-shadow:
        0 2px 0 #131316,
        0 3px 6px rgba(0,0,0,0.5),
        inset 0 2px 2px rgba(255,255,255,0.15),
        inset 0 -2px 3px rgba(0,0,0,0.3);
}
#L1 { width: 92px; height: 34px; top: 8px; left: 4%; border-radius: 14px 14px 4px 4px; }
#L2 { width: 92px; height: 30px; top: 44px; left: 4%; border-radius: 10px; font-size: 13px; }
#R1 { width: 92px; height: 34px; top: 8px; right: 4%; border-radius: 14px 14px 4px 4px; }
#R2 { width: 92px; height: 30px; top: 44px; right: 4%; border-radius: 10px; font-size: 13px; }

/* D-Pad — 3D beveled cross look */
.dpad { position: absolute; top: 32%; left: 9%; width: 150px; height: 150px; }
.dbtn {
    position: absolute;
    background: linear-gradient(180deg,#4d4d56 0%,#2c2c32 50%,#1c1c20 100%);
    border: 1px solid #0f0f11; color: #eee; display: flex; justify-content: center; align-items: center;
    box-shadow:
        0 4px 0 #0a0a0c,
        0 7px 10px rgba(0,0,0,0.5),
        inset 0 2px 2px rgba(255,255,255,0.2),
        inset 0 -2px 3px rgba(0,0,0,0.4);
    font-size: 16px;
    transition: transform 0.05s ease, box-shadow 0.05s ease;
}
.dbtn:active, .dbtn.active {
    background: linear-gradient(180deg,#5d5d66,#2c2c32);
    transform: translateY(3px);
    box-shadow:
        0 1px 0 #0a0a0c,
        0 2px 4px rgba(0,0,0,0.5),
        inset 0 2px 2px rgba(255,255,255,0.12),
        inset 0 -1px 2px rgba(0,0,0,0.3);
}
#up { top: 0; left: 52px; border-radius: 6px 6px 2px 2px; }
#down { bottom: 0; left: 52px; border-radius: 2px 2px 6px 6px; }
#left { top: 52px; left: 0; border-radius: 6px 2px 2px 6px; }
#right { top: 52px; right: 0; border-radius: 2px 6px 6px 2px; }

/* Action buttons — glossy 3D spheres */
.action { position: absolute; top: 30%; right: 8%; width: 160px; height: 160px; }
.abtn {
    position: absolute; border-radius: 50%; display: flex; justify-content: center; align-items: center;
    font-weight: bold; font-size: 20px;
    background: radial-gradient(circle at 35% 25%, #4a4a52 0%, #2c2c32 55%, #1a1a1e 100%);
    border: 1px solid #0d0d0f;
    box-shadow:
        0 6px 0 #0a0a0c,
        0 10px 16px rgba(0,0,0,0.55),
        inset 0 2px 3px rgba(255,255,255,0.3),
        inset 0 -4px 6px rgba(0,0,0,0.4);
    transition: transform 0.05s ease, box-shadow 0.05s ease, filter 0.05s ease;
}
.abtn:active, .abtn.active {
    filter: brightness(1.15);
    transform: translateY(4px) scale(0.97);
    box-shadow:
        0 2px 0 #0a0a0c,
        0 4px 8px rgba(0,0,0,0.5),
        inset 0 2px 2px rgba(255,255,255,0.2),
        inset 0 -2px 3px rgba(0,0,0,0.3);
}
#triangle { top: 0; left: 55px; color: #2ec4a6; }
#cross { bottom: 0; left: 55px; color: #4d9dff; }
#square { top: 55px; left: 0; color: #ff59b3; }
#circle { top: 55px; right: 0; color: #ff5c5c; }

/* Touchpad — recessed 3D panel look */
#touchpad {
    position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
    border-radius: 12px; background: linear-gradient(180deg,#1c1c20,#111113);
    border: 1px solid #0a0a0c;
    box-shadow: inset 0 4px 10px rgba(0,0,0,0.6), inset 0 -1px 0 rgba(255,255,255,0.05), 0 2px 4px rgba(0,0,0,0.3);
}
#touchpad.active { background: linear-gradient(180deg,#26262c,#161618); }

/* Center buttons — small 3D pucks */
.center-btns { position: absolute; top: 82px; left: 50%; transform: translateX(-50%); display: flex; gap: 26px; align-items: center; }
.small-btn {
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(180deg,#3a3a42,#1c1c20); border: 1px solid #0a0a0c;
    font-size: 9px; color: #ccc; display: flex; justify-content: center; align-items: center;
    box-shadow: 0 3px 0 #08080a, 0 5px 8px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.2);
    transition: transform 0.05s ease, box-shadow 0.05s ease;
}
.small-btn:active, .small-btn.active {
    transform: translateY(2px);
    box-shadow: 0 1px 0 #08080a, 0 2px 4px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255,255,255,0.15);
}
#ps-btn {
    position: absolute; bottom: 6%; left: 50%; transform: translateX(-50%);
    width: 46px; height: 46px; border-radius: 50%;
    background: radial-gradient(circle,#3a3a40,#0c0c0e);
    border: 1px solid #0a0a0c; display: flex; justify-content: center; align-items: center;
    color: #6fa8ff; font-size: 11px; font-weight: bold;
    box-shadow: 0 4px 0 #060607, 0 7px 10px rgba(0,0,0,0.5), inset 0 1px 2px rgba(255,255,255,0.25);
    transition: transform 0.05s ease, box-shadow 0.05s ease;
}
#ps-btn:active, #ps-btn.active {
    filter: brightness(1.5); transform: translateX(-50%) translateY(3px);
    box-shadow: 0 1px 0 #060607, 0 2px 5px rgba(0,0,0,0.5), inset 0 1px 2px rgba(255,255,255,0.2);
}

/* Sticks — deep 3D socket + glossy ball knob */
.stick-wrap {
    position: absolute; bottom: 8%; border-radius: 50%;
    background: radial-gradient(circle,#1e1e22,#0c0c0e);
    border: 2px solid #050506;
    box-shadow: inset 0 6px 14px rgba(0,0,0,0.7), inset 0 -1px 0 rgba(255,255,255,0.04), 0 2px 6px rgba(0,0,0,0.4);
}
#left-stick-wrap { left: 22%; }
#right-stick-wrap { right: 22%; }
.stick-knob {
    position: absolute; border-radius: 50%;
    background: radial-gradient(circle at 32% 28%, #6a6a74 0%, #3a3a42 55%, #1c1c20 100%);
    box-shadow:
        0 8px 0 #0a0a0c,
        0 12px 18px rgba(0,0,0,0.55),
        inset 0 3px 4px rgba(255,255,255,0.35),
        inset 0 -5px 8px rgba(0,0,0,0.45);
    transition: box-shadow 0.05s ease;
}
.stick-knob.pressed {
    box-shadow:
        0 3px 0 #0a0a0c,
        0 5px 8px rgba(0,0,0,0.5),
        inset 0 3px 4px rgba(255,255,255,0.25),
        inset 0 -3px 5px rgba(0,0,0,0.4);
}
</style>
</head>
<body>

<div id="start-screen">
    <h2>🎮 DualShock Multi-Profile Gamepad</h2>
    <p>Huawei P20 Lite — PC / PS2 / PS4 Profiles</p>

    <div class="profile-select" id="profileSelect">
        <div class="profile-card" data-profile="pc">
            <div class="icon">🖥️</div>
            <div class="name">PC DualShock</div>
            <div class="sub">WASD Layout</div>
        </div>
        <div class="profile-card" data-profile="ps2">
            <div class="icon">📀</div>
            <div class="name">PS2 DualShock</div>
            <div class="sub">PCSX2 Exact</div>
        </div>
        <div class="profile-card" data-profile="ps4">
            <div class="icon">🎮</div>
            <div class="name">PS4 DualShock</div>
            <div class="sub">DS4 Layout</div>
        </div>
    </div>

    <div class="scale-control">
        <label for="scaleRange">حجم المانيتا:</label>
        <input type="range" id="scaleRange" min="0.6" max="1.4" step="0.05" value="1.0">
        <span id="scaleVal">100%</span>
    </div>

    <div class="access-panel">
        <div class="access-item">
            <label>التباين</label>
            <input type="range" id="accessContrast" min="0.8" max="1.4" step="0.05" value="1">
        </div>
        <div class="access-item">
            <label>الإضاءة</label>
            <input type="range" id="accessBrightness" min="0.7" max="1.3" step="0.05" value="1">
        </div>
        <div class="access-item">
            <label>اهتزاز قوي</label>
            <input type="checkbox" id="accessBigVibe">
        </div>
        <div class="access-item">
            <label>أزرار كبيرة</label>
            <input type="checkbox" id="accessBigButtons">
        </div>
    </div>

    <button id="start-btn">إضغط هنا للبدء (Fullscreen)</button>
</div>

<div id="pad">
    <div id="lightbar"></div>

    <div id="L1" class="shoulder" data-key="">L1</div>
    <div id="L2" class="shoulder" data-key="">L2</div>
    <div id="R1" class="shoulder" data-key="">R1</div>
    <div id="R2" class="shoulder" data-key="">R2</div>

    <div id="touchpad" class="tbtn"></div>

    <div class="center-btns">
        <div class="small-btn" id="share" data-key="">SH</div>
        <div class="small-btn" id="options" data-key="">OPT</div>
    </div>
    <div id="ps-btn" data-key="">PS</div>

    <div class="dpad">
        <div id="up" class="dbtn" data-key="">▲</div>
        <div id="left" class="dbtn" data-key="">◀</div>
        <div id="right" class="dbtn" data-key="">▶</div>
        <div id="down" class="dbtn" data-key="">▼</div>
    </div>

    <div class="action">
        <div id="triangle" class="abtn" data-key="">△</div>
        <div id="cross" class="abtn" data-key="">✕</div>
        <div id="square" class="abtn" data-key="">□</div>
        <div id="circle" class="abtn" data-key="">○</div>
    </div>

    <div id="left-stick-wrap" class="stick-wrap">
        <div class="stick-knob" id="ls" data-key3=""></div>
    </div>
    <div id="right-stick-wrap" class="stick-wrap">
        <div class="stick-knob" id="rs" data-key3=""></div>
    </div>
</div>

<script>
const PROFILES = __PROFILES_JSON__;
const DEFAULT_PROFILE = "__DEFAULT_PROFILE__";
let CFG = PROFILES[DEFAULT_PROFILE];
let currentProfileKey = DEFAULT_PROFILE;

// ---- Profile selector ----
const profileCards = document.querySelectorAll('.profile-card');
function selectProfileCard(key) {
    profileCards.forEach(c => c.classList.toggle('selected', c.dataset.profile === key));
    currentProfileKey = key;
    CFG = PROFILES[key];
}
profileCards.forEach(card => {
    card.addEventListener('click', () => selectProfileCard(card.dataset.profile));
});
selectProfileCard(DEFAULT_PROFILE);

function bindKeysToDOM() {
    const map = {
        L1: CFG.KEY_L1, L2: CFG.KEY_L2, R1: CFG.KEY_R1, R2: CFG.KEY_R2,
        share: CFG.KEY_SHARE, options: CFG.KEY_OPTIONS, 'ps-btn': CFG.KEY_PS,
        up: CFG.KEY_UP, down: CFG.KEY_DOWN, left: CFG.KEY_LEFT, right: CFG.KEY_RIGHT,
        triangle: CFG.KEY_TRIANGLE, cross: CFG.KEY_CROSS, square: CFG.KEY_SQUARE, circle: CFG.KEY_CIRCLE,
    };
    for (const [id, key] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.dataset.key = key;
    }
    document.getElementById('ls').dataset.key3 = CFG.KEY_L3;
    document.getElementById('rs').dataset.key3 = CFG.KEY_R3;
}

// ---- Apply visual config ----
const root = document.documentElement;
function applyVisualConfig() {
    root.style.setProperty('--ui-opacity', CFG.UI_OPACITY);
    root.style.setProperty('--lb-color', CFG.LIGHTBAR_COLOR);
    root.style.setProperty('--lb-glow', CFG.LIGHTBAR_GLOW_INTENSITY + 'px');
    root.style.setProperty('--safe-left', CFG.SAFE_AREA_LEFT + 'px');
    root.style.setProperty('--safe-right', CFG.SAFE_AREA_RIGHT + 'px');

    document.querySelectorAll('.dbtn').forEach(el => {
        el.style.width = CFG.DPAD_SIZE + 'px';
        el.style.height = CFG.DPAD_SIZE + 'px';
    });
    document.querySelectorAll('.abtn').forEach(el => {
        el.style.width = CFG.ACTION_BTNS_SIZE + 'px';
        el.style.height = CFG.ACTION_BTNS_SIZE + 'px';
    });
    document.querySelectorAll('.stick-wrap').forEach(el => {
        el.style.width = CFG.STICK_CONTAINER_SIZE + 'px';
        el.style.height = CFG.STICK_CONTAINER_SIZE + 'px';
    });
    document.querySelectorAll('.stick-knob').forEach(el => {
        const k = CFG.STICK_KNOB_SIZE;
        el.style.width = k + 'px';
        el.style.height = k + 'px';
        el.style.top = (CFG.STICK_CONTAINER_SIZE - k) / 2 + 'px';
        el.style.left = (CFG.STICK_CONTAINER_SIZE - k) / 2 + 'px';
    });
    const tp = document.getElementById('touchpad');
    tp.style.width = CFG.TOUCHPAD_WIDTH + 'px';
    tp.style.height = CFG.TOUCHPAD_HEIGHT + 'px';
}

// ---- Accessibility panel (Huawei P20 Lite tuning) ----
const accessContrast = document.getElementById('accessContrast');
const accessBrightness = document.getElementById('accessBrightness');
const accessBigVibe = document.getElementById('accessBigVibe');
const accessBigButtons = document.getElementById('accessBigButtons');
let bigVibeMode = false;
let bigButtonsMode = false;

accessContrast.addEventListener('input', e => root.style.setProperty('--access-contrast', e.target.value));
accessBrightness.addEventListener('input', e => root.style.setProperty('--access-brightness', e.target.value));
accessBigVibe.addEventListener('change', e => { bigVibeMode = e.target.checked; });
accessBigButtons.addEventListener('change', e => {
    bigButtonsMode = e.target.checked;
    document.querySelectorAll('.abtn, .dbtn, .shoulder').forEach(el => {
        el.style.filter = bigButtonsMode ? 'brightness(1.08)' : '';
        el.style.transform = bigButtonsMode ? (el.style.transform || '') : el.style.transform;
    });
    if (bigButtonsMode) {
        document.documentElement.style.setProperty('--btn-scale', '1.18');
        document.querySelectorAll('.dbtn').forEach(el => { el.style.width = (CFG.DPAD_SIZE * 1.18) + 'px'; el.style.height = (CFG.DPAD_SIZE * 1.18) + 'px'; });
        document.querySelectorAll('.abtn').forEach(el => { el.style.width = (CFG.ACTION_BTNS_SIZE * 1.18) + 'px'; el.style.height = (CFG.ACTION_BTNS_SIZE * 1.18) + 'px'; });
    } else {
        applyVisualConfig();
    }
});

const scaleRange = document.getElementById('scaleRange');
const scaleVal = document.getElementById('scaleVal');
const padEl = document.getElementById('pad');

function applyScale(v) {
    scaleVal.textContent = Math.round(v * 100) + '%';
    padEl.style.transform = `scale(${v})`;
}
scaleRange.addEventListener('input', e => applyScale(parseFloat(e.target.value)));

document.getElementById('start-btn').addEventListener('click', async () => {
    bindKeysToDOM();
    applyVisualConfig();
    applyScale(parseFloat(scaleRange.value));
    try {
        if (CFG.FULLSCREEN_AUTO_LOCK) {
            if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
            if (screen.orientation && screen.orientation.lock) await screen.orientation.lock('landscape');
        }
    } catch (e) {}
    document.getElementById('start-screen').style.display = 'none';
    padEl.style.display = 'block';
    initJoysticks();
});

// ---- Offline click sound (Web Audio API, no files, no network) ----
let audioCtx = null;
function ensureAudio() {
    if (!audioCtx) {
        const AC = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AC();
    }
    if (audioCtx.state === 'suspended') audioCtx.resume();
}
function playClick() {
    if (!CFG.SOUND_CLICK_ENABLED) return;
    ensureAudio();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'square';
    osc.frequency.value = CFG.SOUND_CLICK_FREQ;
    gain.gain.setValueAtTime(CFG.SOUND_CLICK_VOLUME, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.045);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.05);
}
function vibe(ms) {
    if (!CFG.VIBRATION_ENABLED || !navigator.vibrate) return;
    const base = ms || CFG.VIBRATION_DURATION;
    navigator.vibrate(bigVibeMode ? base * 2.2 : base);
}

// ---- State tracking (منع تكرار إرسال نفس الأمر مرتين) ----
const pressedState = new Set();
function sendKey(action, key) {
    if (!key) return;
    if (action === 'press') {
        if (pressedState.has(key)) return;
        pressedState.add(key);
    } else {
        if (!pressedState.has(key)) return;
        pressedState.delete(key);
    }
    const doSend = () => fetch(`/${action}?key=${encodeURIComponent(key)}`);
    if (action === 'release' && CFG.KEY_RELEASE_DELAY > 0) {
        setTimeout(doSend, CFG.KEY_RELEASE_DELAY);
    } else {
        doSend();
    }
}

// Buttons with data-key (press/release)
document.querySelectorAll('[data-key]').forEach(btn => {
    btn.addEventListener('touchstart', e => {
        e.preventDefault();
        playClick(); vibe();
        btn.classList.add('active');
        sendKey('press', btn.dataset.key);
    }, {passive:false});
    btn.addEventListener('touchend', e => {
        e.preventDefault();
        btn.classList.remove('active');
        sendKey('release', btn.dataset.key);
    }, {passive:false});
    btn.addEventListener('touchcancel', e => {
        btn.classList.remove('active');
        sendKey('release', btn.dataset.key);
    });
});

// Stick click (L3/R3)
['ls','rs'].forEach(id => {
    const el = document.getElementById(id);
    let held = false;
    el.addEventListener('touchstart', e => {
        if (e.targetTouches.length === 1 && !held) {
            held = true; playClick(); vibe();
            el.classList.add('pressed');
            sendKey('press', el.dataset.key3);
        }
    }, {passive:true});
    el.addEventListener('touchend', () => {
        if (held) { held = false; el.classList.remove('pressed'); sendKey('release', el.dataset.key3); }
    }, {passive:true});
});

// ============================================================
// ANALOG STICK — 360° MATHEMATICAL MODEL (rewritten from scratch)
// ============================================================
// المنطق القديم كان كيدير ramp-limiting بالبكسل اللي كيخلط بين
// السرعة والاتجاه وكيسبب "قفزات" حسب معدل تحديث اللمس (touch
// polling rate) ديال الهاتف. هاد النسخة كتخدم بمتجهات (vectors)
// نقية بصيغة قطبية (radius + angle) وكتفصل بشكل تام بين:
//   1) الحساب الهندسي (نظيف، مستقل عن الفريمريت)
//   2) قرار "شنو الاتجاه المفعّل" (8-way digital mapping من الزاوية)
//   3) الرسم البصري (transform ديال الكنوب)
// هادشي كيلغي مشكل "quick pass" لأن القرار كيتبنى على الزاوية+القوة
// الحالية فقط، بلا أي تراكم أو تأخير زمني يقدر يعطي إشارة كاذبة.

function setupJoystick(wrapId, knobId, keys, isRightStick) {
    const wrap = document.getElementById(wrapId);
    const knob = document.getElementById(knobId);
    let activeKeys = new Set();
    let touchId = null;

    function getRadius() {
        return wrap.getBoundingClientRect().width / 2;
    }

    function handleMove(clientX, clientY) {
        const rect = wrap.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;

        // متجه خام من المركز للمس (بالبكسل الحقيقي على الشاشة)
        let dx = clientX - cx;
        let dy = clientY - cy;

        const rawDist = Math.sqrt(dx * dx + dy * dy);
        const maxRadius = getRadius();

        // صيغة قطبية: زاوية + قوة (0 → 1) — هادي القاعدة الرياضية
        // للحركة 360° الدقيقة، بلا أي اعوجاج بين المحورين X وY
        const angle = Math.atan2(dy, dx);
        let magnitude01 = Math.min(rawDist / maxRadius, 1);

        // Deadzone دائرية (radial) — أدق من deadzone مربعة على كل محور
        const dz = CFG.ANALOG_DEADZONE;
        let effectiveMag;
        if (magnitude01 <= dz) {
            effectiveMag = 0;
        } else {
            // إعادة تحجيم بعد الـ deadzone: 0 → 1 بشكل متصل (بلا قفزة عند الحافة)
            effectiveMag = (magnitude01 - dz) / (1 - dz);
        }

        // منحنى الحساسية (response curve): تحكم أدق فالبداية، استجابة
        // كاملة قرب الحافة. Exponent قابل للتحكم من CFG.ANALOG_SENSITIVITY
        const curvedMag = Math.pow(effectiveMag, CFG.ANALOG_SENSITIVITY);

        // الموضع البصري للكنوب (بالبكسل، محدود بحدود الدائرة)
        const visualDist = curvedMag * (CFG.ANALOG_MAX_RANGE);
        const knobX = Math.cos(angle) * visualDist;
        const knobY = Math.sin(angle) * visualDist;
        knob.style.transform = `translate(${knobX}px, ${knobY}px)`;

        // ---- تحويل الزاوية لاتجاهات digital (8-way) ----
        // كنستعملو الزاوية مباشرة (ماشي x/y منفصلين) باش الأركان
        // يخرجو بشكل متماثل ودقيق فكل الاتجاهات الثمانية
        let newKeys = new Set();
        if (curvedMag > 0) {
            const deg = angle * 180 / Math.PI; // -180..180، 0=يمين، 90=تحت (شاشة)
            // 8 قطاعات، كل وحدة 45°، مركزة على الاتجاه
            const sector = Math.round(deg / 45) * 45;
            const norm = ((sector % 360) + 360) % 360;
            // norm: 0=يمين, 45=يمين-تحت, 90=تحت, 135=يسار-تحت,
            // 180=يسار, 225=يسار-فوق, 270=فوق, 315=يمين-فوق
            if (norm === 0) { newKeys.add(keys.RIGHT); }
            else if (norm === 45) { newKeys.add(keys.RIGHT); newKeys.add(keys.DOWN); }
            else if (norm === 90) { newKeys.add(keys.DOWN); }
            else if (norm === 135) { newKeys.add(keys.LEFT); newKeys.add(keys.DOWN); }
            else if (norm === 180) { newKeys.add(keys.LEFT); }
            else if (norm === 225) { newKeys.add(keys.LEFT); newKeys.add(keys.UP); }
            else if (norm === 270) { newKeys.add(keys.UP); }
            else if (norm === 315) { newKeys.add(keys.RIGHT); newKeys.add(keys.UP); }
        }

        // إرسال فقط الفرق (state diffing) — بلا تكرار أوامر
        activeKeys.forEach(k => { if (!newKeys.has(k)) sendKey('release', k); });
        newKeys.forEach(k => { if (!activeKeys.has(k)) { sendKey('press', k); vibe(8); } });
        activeKeys = newKeys;
    }

    function reset() {
        knob.style.transform = 'translate(0px, 0px)';
        activeKeys.forEach(k => sendKey('release', k));
        activeKeys.clear();
        touchId = null;
    }

    wrap.addEventListener('touchstart', e => {
        e.preventDefault();
        const t = e.changedTouches[0];
        if (!t) return;
        touchId = t.identifier;
        handleMove(t.clientX, t.clientY);
    }, {passive:false});

    wrap.addEventListener('touchmove', e => {
        e.preventDefault();
        for (const t of e.changedTouches) {
            if (t.identifier === touchId) { handleMove(t.clientX, t.clientY); break; }
        }
    }, {passive:false});

    wrap.addEventListener('touchend', e => {
        e.preventDefault();
        for (const t of e.changedTouches) {
            if (t.identifier === touchId) { reset(); break; }
        }
    }, {passive:false});

    wrap.addEventListener('touchcancel', reset);
}

function initJoysticks() {
    setupJoystick('left-stick-wrap', 'ls', {UP: CFG.LS_UP, DOWN: CFG.LS_DOWN, LEFT: CFG.LS_LEFT, RIGHT: CFG.LS_RIGHT}, false);
    setupJoystick('right-stick-wrap', 'rs', {UP: CFG.RS_UP, DOWN: CFG.RS_DOWN, LEFT: CFG.RS_LEFT, RIGHT: CFG.RS_RIGHT}, true);
}
</script>
</body>
</html>
"""


def render_html(profiles: dict, default_profile: str) -> str:
    import json as _json
    page = HTML_PAGE
    page = page.replace("__PROFILES_JSON__", _json.dumps(profiles, ensure_ascii=False))
    page = page.replace("__DEFAULT_PROFILE__", default_profile)
    return page
# ============================================================
# HTTP Server + Key Injection + Main Entry
# ============================================================

_key_lock = threading.Lock()
_server_pressed = set()

# آخر بروفايل مختار من طرف الواجهة (كيوصل عبر /select-profile)
_active_profile_key = [DEFAULT_PROFILE_KEY]

PREVENT_GHOSTING_GLOBAL = True  # افتراضي، غادي يتبدل حسب البروفايل المفعّل


def safe_keydown(key):
    with _key_lock:
        if PREVENT_GHOSTING_GLOBAL and key in _server_pressed:
            return
        _server_pressed.add(key)
    if shutil.which("xdotool"):
        os.system(f"xdotool keydown -- {key}")
    else:
        print(f"⚠ xdotool ماتلقاش. تأكد بلي مثبت: sudo apt install xdotool")


def safe_keyup(key):
    with _key_lock:
        _server_pressed.discard(key)
    if shutil.which("xdotool"):
        os.system(f"xdotool keyup -- {key}")


class GamepadHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # وقف الـ logs لتخفيف الضغط على المعالج

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/':
            body = render_html(PROFILES, DEFAULT_PROFILE_KEY).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == '/press':
            query = urllib.parse.parse_qs(parsed.query)
            if 'key' in query:
                safe_keydown(query['key'][0])
            self.send_response(200)
            self.end_headers()

        elif parsed.path == '/release':
            query = urllib.parse.parse_qs(parsed.query)
            if 'key' in query:
                safe_keyup(query['key'][0])
            self.send_response(200)
            self.end_headers()

        elif parsed.path == '/select-profile':
            # الواجهة كتقدر تخبر السيرفر بلي بدلات البروفايل — مفيد
            # إلا بغيتي تربط PCSX2 auto-config بالبروفايل المختار حالياً
            query = urllib.parse.parse_qs(parsed.query)
            key = query.get('key', [DEFAULT_PROFILE_KEY])[0]
            if key in PROFILES:
                _active_profile_key[0] = key
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(400)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()


def main():
    print("=" * 60)
    print("🔥 DualShock Multi-Profile Gamepad Server 🔥")
    print("=" * 60)
    for key, cfg in PROFILES.items():
        marker = " (default)" if key == DEFAULT_PROFILE_KEY else ""
        print(f"  ➜ [{key}] {cfg['LABEL']}{marker}")
    print("-" * 60)

    if not shutil.which("xdotool"):
        print("⚠ تحذير: xdotool ماتلقاش فالنظام. الأزرار ماغاديش تخدم.")
        print("   ثبتها بـ: sudo apt install xdotool")

    # --- Thermal monitor (read-only, safe) ---
    thermal_thread, thermal_stop = start_thermal_monitor()
    print(f"✔ مراقبة الحرارة فعالة (تنبيه عند {THERMAL_WARN_C:.0f}°C، قراءة فقط بلا تعديل نظام)")

    # --- Auto-launch PCSX2 (best-effort) ---
    pcsx2_proc = None
    if "--no-pcsx2" not in sys.argv:
        pcsx2_proc = launch_pcsx2()
        # كنجربو نكتبو الـ bindings ديال بروفايل PS2 إلا PCSX2 كانت
        # مغلقة قبل اللانسمون (best-effort، ماكيوقفش السيرفر إلا فشل)
        if "--no-autoconfig" not in sys.argv:
            apply_pcsx2_pad_config(PROFILES["ps2"], pad_section="Pad1")

    print("-" * 60)
    print(f"➜ 1. Connect USB and enable Tethering (أو كون على نفس الواي فاي).")
    print(f"➜ 2. Open phone browser: http://<PC_LOCAL_IP>:{PORT}")
    print(f"➜ 3. اختار البروفايل (PC / PS2 / PS4) من الواجهة وبدا.")
    print("=" * 60)

    ServerClass = ThreadingHTTPServer if UI_BASE["SERVER_THREADING"] else __import__("http.server", fromlist=["HTTPServer"]).HTTPServer
    server_address = ("0.0.0.0", PORT)
    httpd = ServerClass(server_address, GamepadHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        thermal_stop.set()
        thermal_thread.join(timeout=2)
        if pcsx2_proc is not None:
            print("ℹ PCSX2 خلاتها خدامة (ماوقفناهاش). سدها يدوياً إلا بغيتي.")


if __name__ == "__main__":
    main()
