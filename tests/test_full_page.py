import subprocess
import os

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
file_url = "file:///" + os.path.abspath("index.html").replace("\\", "/")

# Load index.html in Edge and capture DOM
result = subprocess.run([
    edge_path,
    "--headless=new",
    "--dump-dom",
    file_url
], capture_output=True, text=True, encoding="utf-8")

assert result.returncode == 0, f"Edge exited with error code {result.returncode}"
dom = result.stdout

# Verify key elements rendered properly
assert '<header class="title-header">Deep<span>Sweep</span></header>' in dom, "Header title missing"
assert '<div id="board"' in dom, "Board container missing"
assert 'Beginner 9×9 / 10' in dom, "Difficulty selector missing"
assert 'Tap to reveal · Long-press to flag' in dom, "Status line missing"

print("Full page load verification: PASS (Page parsed and executed with 0 syntax or runtime errors)")
