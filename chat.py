# shivay_web.py
# SHIVAY — Web Chat (ChatGPT-like UI) + your AI logic in one file
# Features: greetings, math, Google, YouTube, Spotify, Date/Time, News,
#           Open/Close apps, (optional) Shutdown/Restart/Sleep with confirmation.

from flask import Flask, request, jsonify, make_response
import webbrowser
import urllib.parse
import os
import platform
import math
import re
from datetime import datetime

app = Flask(__name__)

# ---------- Core helpers ----------
def open_application(app_name: str) -> str:
    """Open an app or website based on user request."""
    system = platform.system()

    apps = {
        "notepad": "notepad" if system == "Windows" else "gedit",
        "calculator": "calc" if system == "Windows" else "gnome-calculator",
        "paint": "mspaint" if system == "Windows" else "gimp",
        "cmd": "cmd" if system == "Windows" else "gnome-terminal",
        "terminal": "cmd" if system == "Windows" else "gnome-terminal",
        "explorer": "explorer" if system == "Windows" else "nautilus",
        "vs code": "code" if system == "Windows" else "code",
        "chrome": "start chrome" if system == "Windows" else "google-chrome",
        "edge": "start msedge" if system == "Windows" else "microsoft-edge",
        "firefox": "start firefox" if system == "Windows" else "firefox",
    }

    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "spotify": "https://open.spotify.com",
        "github": "https://github.com",
        "facebook": "https://facebook.com",
        "instagram": "https://instagram.com",
        "twitter": "https://twitter.com",
        "news": "https://news.google.com",
    }

    key = app_name.lower().strip()

    # Known app?
    if key in apps:
        try:
            os.system(apps[key])
            return f"✅ Opening {app_name}..."
        except Exception:
            return f"⚠️ Could not open {app_name}."

    # Known site?
    if key in sites:
        webbrowser.open(sites[key], new=2)
        return f"🌐 Opening {app_name} in browser..."

    # If it's a URL, open directly
    if key.startswith("http://") or key.startswith("https://"):
        webbrowser.open(key, new=2)
        return f"🌐 Opening {key} ..."

    # Unknown → search
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(app_name), new=2)
    return f"🔍 I didn’t find “{app_name}” directly. Searching on Google..."

def close_application(app_name: str) -> str:
    """Close an application based on user request."""
    system = platform.system()
    key = app_name.lower().strip()

    process_names = {
        "notepad": "notepad.exe",
        "calculator": "calculator.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "terminal": "cmd.exe" if system == "Windows" else "gnome-terminal",
        "explorer": "explorer.exe",
        "chrome": "chrome.exe",
        "spotify": "spotify.exe",
        "firefox": "firefox.exe",
        "vs code": "Code.exe" if system == "Windows" else "code",
    }

    process = process_names.get(key, key)

    try:
        if system == "Windows":
            os.system(f"taskkill /f /im {process}")
        else:
            os.system(f"pkill {process}")
        return f"❌ {app_name} closed."
    except Exception:
        return f"⚠️ Could not close {app_name}."

def is_math_expression(text: str) -> bool:
    """Heuristic to decide if the text is a math expression."""
    if not re.search(r"\d", text):  # must contain a digit
        return False
    if not re.search(r"[+\-*/%^()]", text):
        return False
    if re.search(r"[a-zA-Z]{2,}", text) and not re.search(r"(sin|cos|tan|log|ln|sqrt|pi|e)\b", text):
        return False
    return True

# Safe math environment
SAFE = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}
SAFE.update({"abs": abs, "round": round, "pow": pow, "min": min, "max": max})

def safe_eval_math(expr: str):
    expr = expr.replace("^", "**")
    if "__" in expr or "import" in expr or "os." in expr or "sys." in expr:
        raise ValueError("unsafe expression")
    return eval(expr, {"__builtins__": None}, SAFE)

# ---------- AI logic ----------
def shivay_reply(user_text: str, admin_confirm: bool = False) -> str:
    original = user_text.strip()
    if not original:
        return "Please type something 🙂"

    text = original.lower().strip()

    # Greetings
    if text in ["hi", "hello", "hey", "namaste", "hii", "hey shivay", "hello shivay"]:
        return f"Hello 👋 I am SHIVAY."

    # Who are you
    if "who are you" in text or "what are you" in text:
        return "I am SHIVAY, your simple AI assistant."

    # Date / Time
    if any(k in text for k in ("date", "today")):
        return datetime.now().strftime("%A, %d %B %Y")
    if any(k in text for k in ("time", "current time", "what time")):
        return datetime.now().strftime("%I:%M %p")

    # News
    if "news" in text or "headlines" in text:
        webbrowser.open("https://news.google.com/topstories", new=2)
        return "📰 Opened Google News."

    # Google quick
    if text.startswith("google "):
        q = original[len("google "):].strip()
        if q:
            url = "https://www.google.com/search?q=" + urllib.parse.quote(q)
            webbrowser.open(url, new=2)
            return f"🔎 Searching Google for “{q}”..."
        return "Tell me what to search on Google."

    # Spotify
    if text.startswith("spotify ") or text.startswith("search song"):
        song = original.replace("search song", "", 1).replace("spotify", "", 1).strip()
        if song:
            url = "https://open.spotify.com/search/" + urllib.parse.quote(song)
            webbrowser.open(url, new=2)
            return f"🎵 Searching “{song}” on Spotify."
        return "Please tell me a song name."

    # YouTube
    if text.startswith("play ") or text.startswith("play song ") or text.startswith("play video ") or text.startswith("youtube "):
        q = original
        for pfx in ("play song ", "play video ", "play ", "youtube "):
            if text.startswith(pfx):
                q = original[len(pfx):].strip()
                break
        if q:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q)
            webbrowser.open(url, new=2)
            return f"▶️ YouTube search for “{q}”."
        return "Please tell me what to play."

    # Open / Close apps or websites
    if text.startswith("open "):
        target = original[len("open "):].strip()
        return open_application(target)

    if text.startswith("close "):
        target = original[len("close "):].strip()
        return close_application(target)

    # Admin: Shutdown / Restart / Sleep (require admin_confirm=True)
    if "shutdown" in text or "turn off" in text:
        if not admin_confirm:
            return "⚠️ Confirm to shutdown? (yes/no)."
        if platform.system() == "Windows":
            os.system("shutdown /s /t 5")
        else:
            os.system("shutdown -h now")
        return "⚠️ Shutting down the system..."

    if "restart" in text or "reboot" in text:
        if not admin_confirm:
            return "⚠️ Confirm to restart? (yes/no)."
        if platform.system() == "Windows":
            os.system("shutdown /r /t 5")
        else:
            os.system("reboot")
        return "🔄 Restarting the system..."

    if "sleep" in text or "go to sleep" in text:
        if not admin_confirm:
            return "⚠️ Confirm to sleep? (yes/no)."
        sysname = platform.system()
        if sysname == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif sysname == "Linux":
            os.system("systemctl suspend")
        elif sysname == "Darwin":
            os.system("pmset sleepnow")
        return "💤 Putting system to sleep..."

    # Math (safe)
    try:
        if is_math_expression(text):
            try:
                result = safe_eval_math(text)
                return f"The answer is: {result}"
            except Exception as e:
                return f"Couldn't evaluate expression: {e}"
    except Exception:
        pass

    # --- Open direct URL if user typed one ---
    if original.startswith("http://") or original.startswith("https://"):
        webbrowser.open(original, new=2)
        return f"🌐 Opening {original} ..."

    # Fallback: Google
    url = "https://www.google.com/search?q=" + urllib.parse.quote(original)
    webbrowser.open(url, new=2)
    return f"🔎 Redirecting to Google for “{original}”..."

# ---------- Routes ----------
@app.route("/", methods=["GET"])
def index():
    # A minimal ChatGPT-like web UI, served directly.
    html = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>SHIVAY • Chat</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { --bg:#0f172a; --panel:#111827; --bubble:#1f2937; --text:#e5e7eb; --accent:#22d3ee; }
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial}
    .wrap{max-width:900px;margin:0 auto;display:flex;flex-direction:column;height:100vh}
    header{padding:16px 20px;border-bottom:1px solid #1f2937;display:flex;gap:10px;align-items:center}
    .dot{width:10px;height:10px;border-radius:50%;background:var(--accent)}
    h1{margin:0;font-size:18px;font-weight:700}
    .chat{flex:1;overflow:auto;padding:24px;display:flex;flex-direction:column;gap:14px}
    .msg{max-width:75%;padding:12px 14px;border-radius:16px;line-height:1.4;background:var(--bubble);box-shadow:0 1px 0 rgba(0,0,0,.2)}
    .me{align-self:flex-end;background:#0369a1}
    .ai{align-self:flex-start}
    .small{opacity:.8;font-size:12px;margin-top:4px}
    footer{padding:12px;border-top:1px solid #1f2937;background:var(--panel);display:flex;gap:10px}
    input,button{font:inherit}
    #q{flex:1;padding:12px 14px;border-radius:12px;border:1px solid #374151;background:#0b1220;color:var(--text);outline:none}
    #send{padding:12px 16px;border-radius:12px;border:0;background:var(--accent);color:#0b1220;font-weight:700;cursor:pointer}
    .row{display:flex;gap:10px}
    label{display:flex;align-items:center;gap:6px;font-size:12px;opacity:.9}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <span class="dot"></span>
      <h1>SHIVAY — your AI assistant</h1>
    </header>
    <div id="chat" class="chat">
      <div class="msg ai">Hello 👋 I am SHIVAY. What I Can Do For You ?<div class="small">tips: “open calculator”, “play lo-fi”, “spotify shape of you”, “system date”, “google pizza near me”</div></div>
    </div>
    <footer>
      <input id="q" placeholder="Type a message…" autocomplete="off">
      <button id="send">Send</button>
      <div class="row">
        <label><input type="checkbox" id="confirm"> confirm admin action</label>
      </div>
    </footer>
  </div>

  <script>
    const q = document.getElementById('q');
    const chat = document.getElementById('chat');
    const btn = document.getElementById('send');
    const confirmBox = document.getElementById('confirm');

    function addMsg(text, who='ai'){
      const div = document.createElement('div');
      div.className = 'msg ' + (who==='me'?'me':'ai');
      div.textContent = text;
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
      return div;
    }

    async function send(){
      const text = q.value.trim();
      if(!text) return;
      addMsg(text, 'me');
      q.value = '';
      const thinking = addMsg('…');
      try{
        const res = await fetch('/chat', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ message: text, confirm: confirmBox.checked })
        });
        const data = await res.json();
        thinking.remove();
        addMsg(data.reply || 'No reply');
      }catch(e){
        thinking.remove();
        addMsg('Error contacting SHIVAY.');
      }
    }

    btn.addEventListener('click', send);
    q.addEventListener('keydown', e => {
      if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }
    });
  </script>
</body>
</html>
    """
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

@app.route("/chat", methods=["POST"])
def chat():
    from typing import Any, Dict
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    admin_confirm = bool(data.get("confirm"))
    reply = shivay_reply(message, admin_confirm=admin_confirm)
    return jsonify({"reply": reply})

# ---------- Run ----------
if __name__ == "__main__":
    print("SHIVAY web is running! Open http://127.0.0.1:5000  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)