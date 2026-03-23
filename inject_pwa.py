"""
Injects PWA tags into the pygbag-generated build/web/index.html.
Run after pygbag --build main.py
"""
import re, shutil, os

INDEX = os.path.join("build", "web", "index.html")

PWA_TAGS = """
  <!-- PWA -->
  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="#0a0a19">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Sirtet">
  <link rel="apple-touch-icon" href="icon-192.png">
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () =>
        navigator.serviceWorker.register('sw.js')
      );
    }
  </script>
"""

if not os.path.exists(INDEX):
    print(f"ERROR: {INDEX} not found — run 'pygbag --build main.py' first.")
    raise SystemExit(1)

with open(INDEX, "r", encoding="utf-8") as f:
    html = f.read()

if "manifest.json" in html:
    print("PWA tags already present, skipping.")
else:
    html = re.sub(r"(</head>)", PWA_TAGS + r"\1", html, count=1)
    shutil.copy(INDEX, INDEX + ".bak")
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"PWA tags injected into {INDEX}")
