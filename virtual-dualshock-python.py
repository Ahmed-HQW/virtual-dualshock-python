import urllib.parse
import os
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ============================================================
# 40 CONFIGURATION PARAMETERS - بدّل هنا بلا ما تدخل للكود
# ============================================================
CONFIG = {
    # --- Design & UI Specs (1-13) ---
    "THEME_STYLE": "white_ds4",
    "PORT": 8080,
    "CONTROLLER_SCALE": 1.0,
    "UI_OPACITY": 0.98,
    "LIGHTBAR_COLOR": "#0080FF",
    "LIGHTBAR_GLOW_INTENSITY": 20,
    "SAFE_AREA_LEFT": 30,
    "SAFE_AREA_RIGHT": 30,
    "DPAD_SIZE": 44,
    "ACTION_BTNS_SIZE": 52,
    "STICK_CONTAINER_SIZE": 118,
    "STICK_KNOB_SIZE": 58,
    "TOUCHPAD_WIDTH": 190,
    "TOUCHPAD_HEIGHT": 62,

    # --- PES Analog & Deadzone Fix (14-20) ---
    "ANALOG_DEADZONE": 0.30,          # نسبة مئوية من ANALOG_MAX_RANGE (رفعناها باش الحركة الخفيفة ماتترجمش لـ pass)
    "ANALOG_SENSITIVITY": 1.6,        # منحنى الحساسية (>1 = بطيء فالبداية، حاد فالنهاية، تحكم أدق)
    "ANALOG_MAX_RANGE": 32,
    "ANALOG_RAMP_LIMIT": 90,          # أقصى تغيّر (px/sec) يتقبل بيه السحب - كيمنع "القفزة" اللي كتفهمها PES كـ trick/quick-pass
    "RS_TRICK_ISOLATION": True,       # إلا True: الـ Right Stick كيبقى Digital Direct بلا أي ramp/curve مشترك مع Left (يبعدو التداخل)
    "PREVENT_KEY_GHOSTING": True,
    "KEY_RELEASE_DELAY": 0,           # ms، 0 = رفع فوري
    "LS_TYPE": "digital_direct",
    "RS_TYPE": "digital_direct",

    # --- PCSX2 Keybindings (21-31) ---
    "KEY_UP": "Up", "KEY_DOWN": "Down", "KEY_LEFT": "Left", "KEY_RIGHT": "Right",
    "KEY_CROSS": "k",       # Pass
    "KEY_CIRCLE": "l",      # Long Pass
    "KEY_SQUARE": "j",      # Shoot
    "KEY_TRIANGLE": "i",    # Through Pass
    "KEY_L1": "q", "KEY_L2": "1", "KEY_R1": "e", "KEY_R2": "3",
    "KEY_L3": "z",
    "KEY_R3": "x",
    "KEY_SHARE": "Tab", "KEY_OPTIONS": "Return", "KEY_PS": "Escape",
    "LS_UP": "w", "LS_DOWN": "s", "LS_LEFT": "a", "LS_RIGHT": "d",
    "RS_UP": "KP_8", "RS_DOWN": "KP_2", "RS_LEFT": "KP_4", "RS_RIGHT": "KP_6",

    # --- Offline & Zero-Lag Performance (32-40) ---
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

# مجموعتين منفصلتين تماماً — الأزرار ماعندهاش أي مفتاح مشترك مع الأنالوج
# هادشي كيحل مشكل PES ديال Pass التلقائي أثناء سحب العصا
ACTION_KEYS = {
    CONFIG["KEY_CROSS"], CONFIG["KEY_CIRCLE"], CONFIG["KEY_SQUARE"], CONFIG["KEY_TRIANGLE"],
    CONFIG["KEY_L1"], CONFIG["KEY_L2"], CONFIG["KEY_R1"], CONFIG["KEY_R2"],
    CONFIG["KEY_L3"], CONFIG["KEY_R3"],
    CONFIG["KEY_UP"], CONFIG["KEY_DOWN"], CONFIG["KEY_LEFT"], CONFIG["KEY_RIGHT"],
}
ANALOG_KEYS = {
    CONFIG["LS_UP"], CONFIG["LS_DOWN"], CONFIG["LS_LEFT"], CONFIG["LS_RIGHT"],
    CONFIG["RS_UP"], CONFIG["RS_DOWN"], CONFIG["RS_LEFT"], CONFIG["RS_RIGHT"],
}
_conflict = ACTION_KEYS & ANALOG_KEYS
if _conflict:
    raise ValueError(
        f"تعارض مفاتيح (Key Ghosting risk): هاد المفاتيح مكررة بين الأنالوج وأزرار الأكشن: {_conflict}. "
        f"بدّل واحد منهم فـ CONFIG قبل ما تشغل السيرفر."
    )

CONFIG_JSON = json.dumps(CONFIG, ensure_ascii=False)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover, orientation=landscape">
<title>DS4 White Pro Gamepad</title>
<style>
* { box-sizing: border-box; -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; touch-action: none; }
html, body {
    background: #000; color: #222; margin: 0; padding: 0;
    height: 100vh; width: 100vw; overflow: hidden; font-family: -apple-system, Arial, sans-serif;
}
#start-screen {
    position: fixed; inset: 0; background: radial-gradient(circle at 50% 40%, #1a1a1f, #000);
    z-index: 9999; display: flex; justify-content: center; align-items: center; flex-direction: column; color: #fff;
}
#start-screen h2 { margin-bottom: 6px; font-size: 20px; }
#start-screen p { color: #888; font-size: 13px; margin-top: 0; }
#start-btn {
    padding: 16px 38px; font-size: 20px; background: linear-gradient(135deg,#0080FF,#00c6ff);
    border: none; border-radius: 30px; font-weight: bold; cursor: pointer; color: #fff;
    margin-top: 18px; box-shadow: 0 8px 24px rgba(0,128,255,0.5);
}
.scale-control {
    margin: 18px 0; display: flex; align-items: center; gap: 12px;
    background: #16161a; padding: 10px 20px; border-radius: 12px; border: 1px solid #2a2a30;
}
.scale-control label { font-size: 14px; color: #ccc; }
.scale-control input[type="range"] { cursor: pointer; width: 160px; }
#scaleVal { font-weight: bold; color: #00c6ff; min-width: 45px; text-align: center; font-size: 14px; }

#pad {
    display: none; position: fixed; inset: 0; width: 100%; height: 100%;
    transform-origin: center center;
    padding-left: calc(env(safe-area-inset-left, 0px) + var(--safe-left));
    padding-right: calc(env(safe-area-inset-right, 0px) + var(--safe-right));
    background: radial-gradient(ellipse at 50% 0%, #ffffff 0%, #e9e9ec 55%, #d8d8dd 100%);
    opacity: var(--ui-opacity);
}

/* Lightbar */
#lightbar {
    position: absolute; top: 0; left: 50%; transform: translateX(-50%);
    width: 140px; height: 8px; border-radius: 0 0 8px 8px;
    background: var(--lb-color);
    box-shadow: 0 0 var(--lb-glow) var(--lb-glow) var(--lb-color), 0 0 6px 2px var(--lb-color);
}

/* Shoulders - white body, dark grey buttons */
.shoulder {
    position: absolute; background: linear-gradient(180deg,#3a3a42,#222226);
    border: 1px solid #454550; color: #eee; font-size: 15px; font-weight: bold;
    display: flex; justify-content: center; align-items: center;
    border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
}
.shoulder:active, .shoulder.active { background: linear-gradient(180deg,#4a4a55,#2a2a30); transform: scale(0.96); }
#L1 { width: 92px; height: 34px; top: 8px; left: 4%; border-radius: 14px 14px 4px 4px; }
#L2 { width: 92px; height: 30px; top: 44px; left: 4%; border-radius: 10px; font-size: 13px; }
#R1 { width: 92px; height: 34px; top: 8px; right: 4%; border-radius: 14px 14px 4px 4px; }
#R2 { width: 92px; height: 30px; top: 44px; right: 4%; border-radius: 10px; font-size: 13px; }

/* D-Pad */
.dpad { position: absolute; top: 32%; left: 9%; width: 150px; height: 150px; }
.dbtn {
    position: absolute; background: linear-gradient(180deg,#4a4a52,#2a2a2e);
    border: 1px solid #55555c; color: #eee; display: flex; justify-content: center; align-items: center;
    box-shadow: 0 3px 8px rgba(0,0,0,0.4); font-size: 16px;
}
.dbtn:active, .dbtn.active { background: linear-gradient(180deg,#5a5a62,#34343a); }
#up { top: 0; left: 52px; border-radius: 6px 6px 2px 2px; }
#down { bottom: 0; left: 52px; border-radius: 2px 2px 6px 6px; }
#left { top: 52px; left: 0; border-radius: 6px 2px 2px 6px; }
#right { top: 52px; right: 0; border-radius: 2px 6px 6px 2px; }

/* Action buttons - white housing, colored glyphs */
.action { position: absolute; top: 30%; right: 8%; width: 160px; height: 160px; }
.abtn {
    position: absolute; border-radius: 50%; display: flex; justify-content: center; align-items: center;
    font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.3), inset 0 1px 1px rgba(255,255,255,0.6);
    background: linear-gradient(180deg,#ffffff,#e4e4e8); border: 1px solid #c9c9d0;
}
.abtn:active, .abtn.active { filter: brightness(0.92); transform: scale(0.93); }
#triangle { top: 0; left: 55px; color: #2ec4a6; }
#cross { bottom: 0; left: 55px; color: #3d7bff; }
#square { top: 55px; left: 0; color: #ff4fa3; }
#circle { top: 55px; right: 0; color: #ff4747; }

/* Touchpad */
#touchpad {
    position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
    border-radius: 12px; background: #f2f2f4;
    border: 1px solid #cfcfd6; box-shadow: inset 0 2px 6px rgba(0,0,0,0.15);
}
#touchpad.active { background: #e2e2e8; }

/* Center buttons */
.center-btns { position: absolute; top: 82px; left: 50%; transform: translateX(-50%); display: flex; gap: 26px; align-items: center; }
.small-btn {
    width: 30px; height: 30px; background: #2a2a2e; border-radius: 50%; border: 1px solid #444;
    font-size: 9px; color: #ccc; display: flex; justify-content: center; align-items: center;
}
#ps-btn {
    position: absolute; bottom: 6%; left: 50%; transform: translateX(-50%);
    width: 46px; height: 46px; border-radius: 50%; background: radial-gradient(circle,#3a3a40,#18181c);
    border: 1px solid #555; display: flex; justify-content: center; align-items: center; color: #6fa8ff; font-size: 11px; font-weight: bold;
}
#ps-btn:active, #ps-btn.active { filter: brightness(1.5); }

/* Sticks */
.stick-wrap {
    position: absolute; bottom: 8%; border-radius: 50%;
    background: radial-gradient(circle,#eaeaee,#d2d2d8); border: 2px solid #c2c2ca;
    box-shadow: inset 0 4px 10px rgba(0,0,0,0.2);
}
#left-stick-wrap { left: 22%; }
#right-stick-wrap { right: 22%; }
.stick-knob {
    position: absolute; border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #4a4a52, #202024);
    box-shadow: 0 4px 10px rgba(0,0,0,0.4), inset 0 1px 2px rgba(255,255,255,0.2);
}
</style>
</head>
<body>

<div id="start-screen">
    <h2>🎮 DualShock 4 White Edition</h2>
    <p>Huawei P20 Lite — PCSX2 / PES Optimized</p>
    <div class="scale-control">
        <label for="scaleRange">حجم المانيتا:</label>
        <input type="range" id="scaleRange" min="0.6" max="1.4" step="0.05" value="__SCALE__">
        <span id="scaleVal">__SCALE_PCT__%</span>
    </div>
    <button id="start-btn">إضغط هنا للبدء (Fullscreen)</button>
</div>

<div id="pad">
    <div id="lightbar"></div>

    <div id="L1" class="shoulder" data-key="__KEY_L1__">L1</div>
    <div id="L2" class="shoulder" data-key="__KEY_L2__">L2</div>
    <div id="R1" class="shoulder" data-key="__KEY_R1__">R1</div>
    <div id="R2" class="shoulder" data-key="__KEY_R2__">R2</div>

    <div id="touchpad" class="tbtn" data-key="__KEY_TOUCHPAD_PLACEHOLDER__"></div>

    <div class="center-btns">
        <div class="small-btn" id="share" data-key="__KEY_SHARE__">SH</div>
        <div class="small-btn" id="options" data-key="__KEY_OPTIONS__">OPT</div>
    </div>
    <div id="ps-btn" data-key="__KEY_PS__">PS</div>

    <div class="dpad">
        <div id="up" class="dbtn" data-key="__KEY_UP__">▲</div>
        <div id="left" class="dbtn" data-key="__KEY_LEFT__">◀</div>
        <div id="right" class="dbtn" data-key="__KEY_RIGHT__">▶</div>
        <div id="down" class="dbtn" data-key="__KEY_DOWN__">▼</div>
    </div>

    <div class="action">
        <div id="triangle" class="abtn" data-key="__KEY_TRIANGLE__">△</div>
        <div id="cross" class="abtn" data-key="__KEY_CROSS__">✕</div>
        <div id="square" class="abtn" data-key="__KEY_SQUARE__">□</div>
        <div id="circle" class="abtn" data-key="__KEY_CIRCLE__">○</div>
    </div>

    <div id="left-stick-wrap" class="stick-wrap">
        <div class="stick-knob" id="ls" data-key3="__KEY_L3__"></div>
    </div>
    <div id="right-stick-wrap" class="stick-wrap">
        <div class="stick-knob" id="rs" data-key3="__KEY_R3__"></div>
    </div>
</div>

<script>
const CFG = __CONFIG_JSON__;

// ---- Apply config ----
const root = document.documentElement;
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
tp.removeAttribute('data-key'); // touchpad بلا key فهاد النسخة PES (تفادي أي تعارض)

const scaleRange = document.getElementById('scaleRange');
const scaleVal = document.getElementById('scaleVal');
const padEl = document.getElementById('pad');

function applyScale(v) {
    scaleVal.textContent = Math.round(v * 100) + '%';
    padEl.style.transform = `scale(${v})`;
}
applyScale(CFG.CONTROLLER_SCALE);
scaleRange.addEventListener('input', e => applyScale(parseFloat(e.target.value)));

document.getElementById('start-btn').addEventListener('click', async () => {
    try {
        if (CFG.FULLSCREEN_AUTO_LOCK) {
            if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
            if (screen.orientation && screen.orientation.lock) await screen.orientation.lock('landscape');
        }
    } catch (e) {}
    document.getElementById('start-screen').style.display = 'none';
    padEl.style.display = 'block';
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
    if (CFG.VIBRATION_ENABLED && navigator.vibrate) navigator.vibrate(ms || CFG.VIBRATION_DURATION);
}

// ---- State tracking (منع تكرار إرسال نفس الأمر مرتين لـ xdotool) ----
const pressedState = new Set();
function sendKey(action, key) {
    if (!key) return;
    if (action === 'press') {
        if (pressedState.has(key)) return; // already pressed, avoid duplicate xdotool call
        pressedState.add(key);
    } else {
        if (!pressedState.has(key)) return; // already released
        pressedState.delete(key);
    }
    const doSend = () => fetch(`/${action}?key=${encodeURIComponent(key)}`);
    if (action === 'release' && CFG.KEY_RELEASE_DELAY > 0) {
        setTimeout(doSend, CFG.KEY_RELEASE_DELAY);
    } else {
        doSend();
    }
}

// Buttons with data-key (press/release) — أزرار الأكشن + D-Pad + shoulders + L3/R3/Share/Options/PS
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

// Stick click (L3/R3) — منفصل تماماً عن حركة السحب
['ls','rs'].forEach(id => {
    const el = document.getElementById(id);
    let held = false;
    el.addEventListener('touchstart', e => {
        if (e.targetTouches.length === 1 && !held) {
            held = true; playClick(); vibe();
            sendKey('press', el.dataset.key3);
        }
    }, {passive:true});
    el.addEventListener('touchend', () => {
        if (held) { held = false; sendKey('release', el.dataset.key3); }
    }, {passive:true});
});

// ---- Analog sticks — منطق Deadzone صارم لحل مشكل PES (Pass تلقائي) ----
function setupJoystick(wrapId, knobId, keys, isRightStick) {
    const wrap = document.getElementById(wrapId);
    const knob = document.getElementById(knobId);
    let activeKeys = new Set(); // المفاتيح المرسلة حالياً من هاد العصا فقط (isolated per-stick)

    // deadzone الحقيقية بالبكسل = نسبة * أقصى مدى
    const deadzonePx = CFG.ANALOG_DEADZONE * CFG.ANALOG_MAX_RANGE;

    // RS_TRICK_ISOLATION: الـ Right Stick كيمشي Digital Direct صرفة (بلا curve وبلا ramp)
    // باش يبقى معزول تماماً على أي منطق كيقدر يفهمو PES كـ "quick trick / skill move"
    const useRamp = !(isRightStick && CFG.RS_TRICK_ISOLATION);

    function applySensitivity(v) {
        const sign = v < 0 ? -1 : 1;
        const norm = Math.abs(v) / CFG.ANALOG_MAX_RANGE;
        const curved = Math.pow(norm, CFG.ANALOG_SENSITIVITY);
        return sign * curved * CFG.ANALOG_MAX_RANGE;
    }

    // Ramp limiting: كنحدو أقصى سرعة تغيّر الموضع (px/sec) باش نمنعو "القفزة"
    // اللي PES كيقرا فيها حركة سريعة مفاجئة = quick-pass/trick auto-trigger
    let smoothX = 0, smoothY = 0;
    let lastTs = 0;

    function rampLimit(targetX, targetY, now) {
        if (!useRamp) return {x: targetX, y: targetY}; // Right Stick معزول: بلا ramp
        if (lastTs === 0) { lastTs = now; smoothX = targetX; smoothY = targetY; return {x: smoothX, y: smoothY}; }
        const dt = Math.max((now - lastTs) / 1000, 0.001); // ثانية
        lastTs = now;
        const maxStep = CFG.ANALOG_RAMP_LIMIT * dt; // أقصى px يتقبل بيهم فهاد الفريم

        const dx = targetX - smoothX;
        const dy = targetY - smoothY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > maxStep && dist > 0) {
            const ratio = maxStep / dist;
            smoothX += dx * ratio;
            smoothY += dy * ratio;
        } else {
            smoothX = targetX;
            smoothY = targetY;
        }
        return {x: smoothX, y: smoothY};
    }

    function handle(e) {
        e.preventDefault();
        const touch = e.targetTouches[0];
        if (!touch) return;
        const rect = wrap.getBoundingClientRect();
        const scale = parseFloat(scaleRange.value);
        let rawX = (touch.clientX - rect.left - rect.width / 2) / scale;
        let rawY = (touch.clientY - rect.top - rect.height / 2) / scale;

        const max = CFG.ANALOG_MAX_RANGE;
        if (rawX > max) rawX = max; if (rawX < -max) rawX = -max;
        if (rawY > max) rawY = max; if (rawY < -max) rawY = -max;

        const curvedX = applySensitivity(rawX);
        const curvedY = applySensitivity(rawY);

        const now = performance.now();
        const limited = rampLimit(curvedX, curvedY, now);
        const x = limited.x, y = limited.y;

        knob.style.transform = `translate(${x}px, ${y}px)`;

        // Strict deadzone: خارج المنطقة الميتة فقط كنحسبو الاتجاه
        const magnitude = Math.sqrt(x * x + y * y);
        let newKeys = new Set();
        if (magnitude >= deadzonePx) {
            if (y < -deadzonePx) newKeys.add(keys.UP);
            if (y > deadzonePx) newKeys.add(keys.DOWN);
            if (x < -deadzonePx) newKeys.add(keys.LEFT);
            if (x > deadzonePx) newKeys.add(keys.RIGHT);
        }

        // إرسال فقط الفرق (state tracking) — بلا تكرار
        activeKeys.forEach(k => { if (!newKeys.has(k)) sendKey('release', k); });
        newKeys.forEach(k => { if (!activeKeys.has(k)) { sendKey('press', k); vibe(10); } });
        activeKeys = newKeys;
    }

    wrap.addEventListener('touchstart', e => { lastTs = 0; handle(e); }, {passive:false});
    wrap.addEventListener('touchmove', handle, {passive:false});
    wrap.addEventListener('touchend', e => {
        e.preventDefault();
        knob.style.transform = 'translate(0px, 0px)';
        activeKeys.forEach(k => sendKey('release', k));
        activeKeys.clear();
        smoothX = 0; smoothY = 0; lastTs = 0;
    }, {passive:false});
    wrap.addEventListener('touchcancel', () => {
        knob.style.transform = 'translate(0px, 0px)';
        activeKeys.forEach(k => sendKey('release', k));
        activeKeys.clear();
        smoothX = 0; smoothY = 0; lastTs = 0;
    });
}

setupJoystick('left-stick-wrap', 'ls', {UP: CFG.LS_UP, DOWN: CFG.LS_DOWN, LEFT: CFG.LS_LEFT, RIGHT: CFG.LS_RIGHT}, false);
setupJoystick('right-stick-wrap', 'rs', {UP: CFG.RS_UP, DOWN: CFG.RS_DOWN, LEFT: CFG.RS_LEFT, RIGHT: CFG.RS_RIGHT}, true);
</script>
</body>
</html>
"""


def render_html():
    page = HTML_PAGE
    page = page.replace("__CONFIG_JSON__", CONFIG_JSON)
    page = page.replace("__SCALE__", str(CONFIG["CONTROLLER_SCALE"]))
    page = page.replace("__SCALE_PCT__", str(int(CONFIG["CONTROLLER_SCALE"] * 100)))
    page = page.replace("__KEY_L1__", CONFIG["KEY_L1"])
    page = page.replace("__KEY_L2__", CONFIG["KEY_L2"])
    page = page.replace("__KEY_R1__", CONFIG["KEY_R1"])
    page = page.replace("__KEY_R2__", CONFIG["KEY_R2"])
    page = page.replace("__KEY_L3__", CONFIG["KEY_L3"])
    page = page.replace("__KEY_R3__", CONFIG["KEY_R3"])
    page = page.replace("__KEY_SHARE__", CONFIG["KEY_SHARE"])
    page = page.replace("__KEY_OPTIONS__", CONFIG["KEY_OPTIONS"])
    page = page.replace("__KEY_PS__", CONFIG["KEY_PS"])
    page = page.replace("__KEY_TOUCHPAD_PLACEHOLDER__", "")
    page = page.replace("__KEY_UP__", CONFIG["KEY_UP"])
    page = page.replace("__KEY_DOWN__", CONFIG["KEY_DOWN"])
    page = page.replace("__KEY_LEFT__", CONFIG["KEY_LEFT"])
    page = page.replace("__KEY_RIGHT__", CONFIG["KEY_RIGHT"])
    page = page.replace("__KEY_TRIANGLE__", CONFIG["KEY_TRIANGLE"])
    page = page.replace("__KEY_CROSS__", CONFIG["KEY_CROSS"])
    page = page.replace("__KEY_SQUARE__", CONFIG["KEY_SQUARE"])
    page = page.replace("__KEY_CIRCLE__", CONFIG["KEY_CIRCLE"])
    return page


# قفل خفيف باش نضمنو ماشي جوج طلبات press/release ليدوزو فنفس الوقت
# ويعملو race condition فحالة الأزرار (إضافي لمنع Key Ghosting)
_key_lock = threading.Lock()
_server_pressed = set()


def safe_keydown(key):
    with _key_lock:
        if CONFIG["PREVENT_KEY_GHOSTING"] and key in _server_pressed:
            return  # مضغوط ديجا، ماكنعاودوش نبعتو نفس الأمر
        _server_pressed.add(key)
    os.system(f"xdotool keydown -- {key}")


def safe_keyup(key):
    with _key_lock:
        _server_pressed.discard(key)
    os.system(f"xdotool keyup -- {key}")


class GamepadHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # وقف الـ logs لتخفيف الضغط على المعالج (SERVER_THREADING optimization)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/':
            body = render_html().encode('utf-8')
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

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    ServerClass = ThreadingHTTPServer if CONFIG["SERVER_THREADING"] else __import__("http.server", fromlist=["HTTPServer"]).HTTPServer
    server_address = ("0.0.0.0", CONFIG["PORT"])
    httpd = ServerClass(server_address, GamepadHandler)
    print("========================================")
    print("🔥 DS4 White Edition Gamepad Server 🔥")
    print("✔ PES Analog/Deadzone fix: ACTIVE")
    print(f"✔ Deadzone: {CONFIG['ANALOG_DEADZONE']*100:.0f}% | Sensitivity curve: {CONFIG['ANALOG_SENSITIVITY']}")
    print("➜ 1. Connect USB and enable Tethering.")
    print(f"➜ 2. Open phone browser: http://<PC_LOCAL_IP>:{CONFIG['PORT']}")
    print("========================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
