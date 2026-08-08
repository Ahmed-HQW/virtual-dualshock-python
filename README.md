<div align="center">

# 🎮 Virtual DualShock 4 — Python Edition

### يد تحكم DualShock 4 افتراضية من الهاتف ديالك، بلا أنترنت، بلا تطبيق

**تحويل أي هاتف (Android / iPhone) ليد تحكم PS4 حقيقية على الكمبيوتر، عبر كابل USB فقط — مصممة خصيصاً لألعاب PES و PCSX2**

[![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-gold?style=for-the-badge)](#-الرخصة--license)
[![Platform](https://img.shields.io/badge/Platform-Linux-000000?style=for-the-badge&logo=linux&logoColor=white)](#-المتطلبات--requirements)
[![No Internet](https://img.shields.io/badge/Offline-100%25-success?style=for-the-badge)](#)
[![Made in Morocco](https://img.shields.io/badge/Made%20in-Morocco%20🇲🇦-C1272D?style=for-the-badge)](#)

**[⬇️ تحميل المشروع](https://github.com/Ahmed-HQW/virtual-dualshock-python)** • **[🐛 الإبلاغ عن مشكل](https://github.com/Ahmed-HQW/virtual-dualshock-python/issues)** • **[✨ اقتراح ميزة](https://github.com/Ahmed-HQW/virtual-dualshock-python/issues)**

</div>

---

## 🔍 كيوورد بحث سريعة

`virtual gamepad python` • `DualShock 4 emulator web` • `PS4 controller phone to PC` • `PES 2021 mobile controller` • `PCSX2 gamepad browser` • `USB tethering gamepad` • `xdotool keyboard emulation` • `يد تحكم افتراضية بايثون` • `تحويل الهاتف ليد تحكم` • `تحكم PES بالهاتف` • `virtual joystick html5` • `Python HTTP game controller server` • `offline gamepad no app` • `PS4 controller simulator browser` • `Linux gamepad emulator python` • `تشغيل PES بالتلفون` • `PCSX2 android controller` • `web based dualshock` • `no lag mobile controller` • `Ahmed HQW ARCHON`

---

## 📖 عن المشروع

**Virtual DualShock Python** هو خادم ويب صغير مكتوب بـ Python بالكامل (بدون أي `dependencies` خارجية)، كيحول شاشة هاتفك إلى يد تحكم **DualShock 4** حقيقية شغالة مباشرة من المتصفح (Browser). المشروع تصمم خصيصاً باش يحل مشكل التأخير (Lag) والتعارض بين الأزرار والعصا التناظرية (Analog Stick) اللي كتوقع فيها ألعاب PES و PCSX2 — خاصة مشكل "الباص التلقائي" (Auto-Pass) المزعج.

الخادم كيخدم صفحة HTML/CSS/JS فيها تصميم DualShock 4 كامل (لوحة اتجاهات، أزرار أكشن، عصيان تناظريان، Touchpad، شوامل L1/L2/R1/R2)، وكل ضغطة كتترجم فالوقت الحقيقي لضغطة كيبورد حقيقية على الكمبيوتر عبر `xdotool`.

### ⚡ ليش هاد المشروع؟

- ما بغيتيش تشري يد تحكم PS4 حقيقية باش تلعب PES على الكمبيوتر
- بغيتي تلعب PES بلا لاغ ولا تأخير فالأزرار
- كتلعب فبلاصة فيها ما كاينش أنترنت (Offline بالكامل، خدمة USB فقط)
- بغيتي حل نهائي لمشكل الـ Auto-Pass اللي كتسبب فيه العصا التناظرية العادية

---

## ✨ الميزات (Features)

| الميزة | الوصف |
|---|---|
| 🔌 **بلا أنترنت 100%** | كيخدم بالكامل عبر USB Tethering، بلا حاجة لـ WiFi ولا Data |
| 🐍 **Pure Python** | صفر Dependencies خارجية — مكتبة `http.server` القياسية فقط |
| 🎯 **حل مشكل PES Analog Fix** | Deadzone محسوبة بدقة + Sensitivity Curve + Ramp Limiting باش توقف الـ Auto-Pass |
| 🧠 **Right Stick معزول (Isolated)** | العصا اليمنى Digital Direct بلا تداخل مع أي Ramp/Curve مشترك |
| 🚫 **Anti Key-Ghosting** | حماية من تكرار إرسال نفس الزر مرتين (Race Condition Lock) |
| ⚡ **Zero-Lag Threading** | `ThreadingHTTPServer` باش يعالج عدة طلبات فنفس الوقت بلا تعليق |
| 🎨 **تصميم DS4 احترافي** | Lightbar متحرك، أزرار بألوان أصلية (△○✕□)، Touchpad وظيفي |
| 📳 **Vibration + Sound Feedback** | اهتزاز وصوت خفيف عند كل ضغطة (قابلين للتعطيل) |
| ⚙️ **40+ إعداد قابل للتعديل** | كل شيء (المفاتيح، الألوان، الحساسية، الحجم) قابل للتخصيص من `CONFIG` بلا ما تدخل للكود |
| 📱 **متجاوب مع كل الشاشات** | Landscape Mode، Multi-Touch Optimized، يخدم على أي هاتف Android أو iPhone |
| 🔒 **Full-Screen Auto-Lock** | يقفل الشاشة أوتوماتيكياً باش ما يوقفش اللعب بالخطأ |

---

## 🖥️ لقطة شاشة (Preview)

```
┌─────────────────────────────────────────────────┐
│  ⬤ Lightbar (Blue)                               │
│                                                   │
│  [L1]                              [R1]          │
│  [L2]         ⬜ Touchpad ⬜        [R2]          │
│                                                   │
│       ▲                      △                   │
│  ◄  D-PAD  ►            □   ACTION   ○           │
│       ▼                      ✕                   │
│                                                   │
│   (( Left Stick ))      (( Right Stick ))         │
│                                                   │
│  [SHARE]      [PS]      [OPTIONS]                │
└─────────────────────────────────────────────────┘
```

---

## 📋 المتطلبات (Requirements)

| المتطلب | التفاصيل |
|---|---|
| نظام التشغيل | Linux (Ubuntu, Debian, Arch, أي توزيعة فيها X11) |
| Python | 3.6 أو أحدث (مثبت بشكل افتراضي فمعظم توزيعات Linux) |
| xdotool | `sudo apt install xdotool` (Debian/Ubuntu) أو `sudo pacman -S xdotool` (Arch) |
| الهاتف | أي Android أو iPhone فيه متصفح (Chrome, Safari...) |
| الاتصال | كابل USB (وضع Tethering/USB Internet) — **بلا حاجة لأنترنت حقيقي** |
| PS2 Emulator | [PCSX2](https://pcsx2.net/) لتشغيل PES 2013-2021 على الكمبيوتر |

> 💡 **ملاحظة:** المشروع كيخدم على Linux لأنه كيستعمل `xdotool` باش يبعث ضغطات الكيبورد للنظام. إلا كنتي على Windows، خاصك بديل زي `pydirectinput` (شوف قسم [المساهمة](#-المساهمة--contributing)).

---

## 🚀 التثبيت والتشغيل (بشكل احترافي، خطوة بخطوة)

### الخطوة 1️⃣ — نزّل المشروع

```bash
git clone https://github.com/Ahmed-HQW/virtual-dualshock-python.git
cd virtual-dualshock-python
```

أو حمّل الملف مباشرة: [virtual-dualshock-python.py](https://github.com/Ahmed-HQW/virtual-dualshock-python)

### الخطوة 2️⃣ — تأكد أن `xdotool` مثبت

```bash
# Debian / Ubuntu / Linux Mint
sudo apt update && sudo apt install xdotool -y

# Arch / Manjaro
sudo pacman -S xdotool

# Fedora
sudo dnf install xdotool
```

### الخطوة 3️⃣ — شغّل السيرفر

```bash
python3 virtual-dualshock-python.py
```

غادي يبان ليك هاد الرسالة فالـ Terminal:

```
========================================
🔥 DS4 White Edition Gamepad Server 🔥
✔ PES Analog/Deadzone fix: ACTIVE
✔ Deadzone: 30% | Sensitivity curve: 1.6
➜ 1. Connect USB and enable Tethering.
➜ 2. Open phone browser: http://<PC_LOCAL_IP>:8080
========================================
```

### الخطوة 4️⃣ — وصّل الهاتف بالكمبيوتر عبر USB

1. وصّل الهاتف بالكمبيوتر بكابل USB عادي
2. فالهاتف، دخل لـ **الإعدادات (Settings) → شبكة الاتصال (Network) → USB Tethering / مشاركة الإنترنت عبر USB**
3. فعّل الخيار (فهاد الخطوة، الهاتف غادي يعطي للكمبيوتر عنوان IP محلي — **بلا حاجة لأنترنت حقيقي**، غير اتصال شبكي محلي)

### الخطوة 5️⃣ — لقى IP ديال الكمبيوتر

فالـ Terminal ديال الكمبيوتر، كتب:

```bash
ip addr show
# أو
hostname -I
```

غادي تلقى شي حاجة بحال `192.168.42.129` (هادشي هو الـ IP المحلي).

### الخطوة 6️⃣ — دخل من الهاتف

حل المتصفح فالهاتف (Chrome مستحسن) وكتب:

```
http://192.168.42.129:8080
```

*(بدّل الـ IP بالـ IP ديالك اللي لقيتي فالخطوة 5)*

اضغط على **"ابدأ" (Start)**، وهاداك لصح — يد التحكم بانت! حط الهاتف Landscape وابدا اللعب. 🎮

### الخطوة 7️⃣ — شغّل PCSX2 و PES

حل PCSX2، شغل اللعبة، وابدا تلعب — كل ضغطة من الهاتف غادي تتحول لضغطة كيبورد حقيقية على الكمبيوتر.

---

## 🎛️ خريطة الأزرار الافتراضية (Default Keybindings)

| زر DS4 | مفتاح الكيبورد | الوظيفة فـ PES |
|---|---|---|
| ✕ Cross | `K` | Pass |
| ○ Circle | `L` | Long Pass |
| □ Square | `J` | Shoot |
| △ Triangle | `I` | Through Pass |
| L1 / R1 | `Q` / `E` | Sprint Modifier / Player Switch |
| L2 / R2 | `1` / `3` | Sprint / Finesse |
| L3 / R3 | `Z` / `X` | Sprint Stick / Change Camera |
| D-Pad | Arrow Keys | Navigation |
| Left Stick | `W A S D` | Movement |
| Right Stick | `Numpad 8/2/4/6` | Trick / Camera |
| Share / Options / PS | `Tab` / `Enter` / `Esc` | Menu Controls |

> ⚙️ **كل هاد المفاتيح قابلة للتعديل** من `CONFIG` فبداية الملف، بلا ما تدور على شي حتة فالكود.

---

## ⚙️ التخصيص (Configuration)

كل الإعدادات مجمعة فـ `dictionary` واحد فوق الملف، مقسمة على 40 باراميتر:

```python
CONFIG = {
    "PORT": 8080,                    # بدّل البورت
    "LIGHTBAR_COLOR": "#0080FF",     # لون الـ Lightbar
    "ANALOG_DEADZONE": 0.30,         # حساسية العصا (Deadzone)
    "ANALOG_SENSITIVITY": 1.6,       # منحنى الحساسية
    "KEY_CROSS": "k",                # بدّل أي مفتاح كيبورد
    # ... و 35 باراميتر آخر
}
```

بدّل القيمة، حفظ (`Ctrl+S`)، عاود شغل السكريبت — بلا ما تحتاج تفهم الكود.

---

## 🧩 حل المشاكل الشائعة (Troubleshooting)

<details>
<summary><b>❌ ما قدرتش نوصل للـ IP من الهاتف</b></summary>

- تأكد أن USB Tethering مفعّل فعلاً فالهاتف (ماشي غير الشحن)
- تأكد أن الكمبيوتر والهاتف على نفس الشبكة المحلية (نفس الـ Subnet)
- جرب `ip addr` مرة أخرى، الـ IP كيتبدل فبعض الحالات
- عطل الـ Firewall مؤقتاً: `sudo ufw allow 8080`
</details>

<details>
<summary><b>❌ الأزرار ما كتخدمش فPES</b></summary>

- تأكد أن `xdotool` مثبت: `xdotool --version`
- تأكد أن نافذة PCSX2 هي الـ Active Window (مفوكسة) وقت اللعب
- تأكد أن keybindings ديال PCSX2 مطابقين للمفاتيح فـ `CONFIG`
</details>

<details>
<summary><b>❌ العصا كتعمل Pass تلقائي (Auto-Pass)</b></summary>

هادشي بالضبط اللي المشروع صممناه باش يحلو! زيد فـ `ANALOG_DEADZONE` (مثلاً من `0.30` لـ `0.40`) ونقص `ANALOG_RAMP_LIMIT` باش تزيد الحماية.
</details>

---

## 🌟 مشاريع ذات صلة — من نفس المطور

### 🤖 Zunexa — منصة الذكاء الاصطناعي لتوليد المحتوى

<div align="center">

**[🔗 zunexa.vercel.app](https://zunexa.vercel.app)**

منصة SaaS مغربية بالكامل، مبنية باش تولد محتوى احترافي بالذكاء الاصطناعي — موجهة للسوق المغربي والعربي (MENA) — نصوص، أفكار، ومحتوى تسويقي جاهز فثواني.

**[✨ جرب Zunexa AI مباشرة → zunexa.vercel.app/ai](https://zunexa.vercel.app/ai)**

</div>

> 🇲🇦 مشروع صاحب هاد الريبو (Ahmed) موجه بالكامل نحو بناء أدوات AI و SaaS محلية 100% مغربية، تحت مظلة **ARCHON** — راه تقدر تتابع باقي المشاريع من البروفايل ديالو.

---

## 🗂️ بنية المشروع (Project Structure)

```
virtual-dualshock-python/
│
├── virtual-dualshock-python.py   # الملف الرئيسي — كل شيء فيه (Server + HTML + JS + CSS)
├── README.md                     # هاد الملف
└── LICENSE                       # رخصة المشروع
```

المشروع مصمم بفلسفة **Single-File Deployment** — ملف واحد، بلا Dependencies، بلا Build Step، خدم وسالا.

---

## 🛠️ التقنيات المستعملة (Tech Stack)

- **Backend:** Python 3 (`http.server`, `threading`) — Standard Library فقط
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (بلا Frameworks)
- **System Bridge:** `xdotool` (X11 Automation)
- **Networking:** USB Tethering / Local IP HTTP Server

---

## 🤝 المساهمة (Contributing)

المساهمات مرحب بيها بزاف! إلا بغيتي تزيد:

- ✅ دعم Windows (بديل لـ `xdotool` زي `pydirectinput` أو `pyautogui`)
- ✅ دعم Bluetooth بدل USB فقط
- ✅ Presets جاهزين لألعاب أخرى (FIFA, Tekken...)
- ✅ Vibration حقيقي عبر Gamepad API

افتح **Pull Request** أو **Issue** وغادي نراجعها بسرعة.

```bash
# Fork المشروع
git clone https://github.com/YOUR_USERNAME/virtual-dualshock-python.git
git checkout -b feature/your-feature-name
git commit -m "Add: your feature"
git push origin feature/your-feature-name
# دير Pull Request
```

---

## ⭐ دعم المشروع

إلا عجبك المشروع، عطيه **⭐ Star** على GitHub — هادشي كيشجعنا نكملو نطورو! ولا شاركو مع صحابك اللي كيلعبو PES بلا يد تحكم.

---

## 📜 الرخصة | License

هاد المشروع تحت رخصة **MIT License** — حر الاستخدام، التعديل، والتوزيع، مع الإشارة للمصدر الأصلي.

```
MIT License
Copyright (c) 2025-2026 Ahmed (Ahmed-HQW)
```

---

## 👤 المطور | Author

**Ahmed** — مطور مستقل (Solo Developer) من بئر جديد، الجديدة، المغرب 🇲🇦

- 🔗 GitHub: [Ahmed-HQW](https://github.com/Ahmed-HQW)
- 🤖 Zunexa (منصة AI/SaaS): [zunexa.vercel.app](https://zunexa.vercel.app)
- 🧠 Zunexa AI (الذكاء الاصطناعي): [zunexa.vercel.app/ai](https://zunexa.vercel.app/ai)

---

<div align="center">

### إلا كتبحث على: `python virtual gamepad` • `PS4 controller emulator` • `PES mobile controller` • `PCSX2 phone gamepad` • `يد تحكم من الهاتف` — راك فالبلاصة الصحيحة 🎯

**صنع بـ ❤️ فالمغرب 🇲🇦**

</div>
