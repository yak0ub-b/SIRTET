#!/usr/bin/env bash
# Full web build for Sirtet
# Usage: bash build_web.sh
set -e

echo "=== 1/4 Generating PWA icons ==="
python pwa/generate_icons.py

echo "=== 2/4 Building WebAssembly with pygbag ==="
pygbag --build main.py

echo "=== 3/4 Copying PWA assets ==="
cp pwa/manifest.json build/web/
cp pwa/sw.js         build/web/
cp pwa/icon-192.png  build/web/
cp pwa/icon-512.png  build/web/

echo "=== 4/4 Injecting PWA tags into index.html ==="
python inject_pwa.py

echo ""
echo "Build complete! Files are in: build/web/"
echo ""
echo "Next steps:"
echo "  1. Create a GitHub repo and push this project"
echo "  2. Push build/web/ contents to the gh-pages branch"
echo "  3. Enable GitHub Pages in repo Settings → Pages"
echo "  4. Open the URL on your phone — Chrome will show 'Add to Home Screen'"
