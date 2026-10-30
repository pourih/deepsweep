import subprocess
import os
import re
import json

def run_tests():
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    # Read index.html to extract the actual code
    with open("index.html", "r", encoding="utf-8") as f:
        index_html = f.read()

    # Extract readConfigFromForm function body
    read_config_match = re.search(r'function readConfigFromForm\(\)\s*\{(.*?)\n  \}', index_html, re.DOTALL)
    assert read_config_match, "Could not find readConfigFromForm in index.html"
    read_config_code = read_config_match.group(1)

    # Extract the boardData mapping line in reveal()
    mapping_match = re.search(r'cells = boardData\.map\((.*?)\);', index_html, re.DOTALL)
    assert mapping_match, "Could not find boardData.map in index.html"
    mapping_code = mapping_match.group(0)

    # Build the test HTML running the actual extracted code from index.html
    test_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<div id="results"></div>
<script>
(() => {{
  const results = [];

  // -------------------------------------------------------------------------
  // Test Issue 1: Pre-game flag preservation on first reveal
  // -------------------------------------------------------------------------
  try {{
    // Setup pre-game state
    let flagCount = 0;
    let cells = Array.from({{ length: 9 }}, () => Array.from({{ length: 9 }}, () => ({{
      mine: false, revealed: false, mark: 0, adjacent: 0
    }})));

    // User marks cell (0, 0) as a flag before game starts
    cells[0][0].mark = 1;
    flagCount = 1;

    // First reveal occurs: worker returns boardData
    const boardData = Array.from({{ length: 9 }}, () => Array.from({{ length: 9 }}, () => ({{
      mine: false, adjacent: 0
    }})));

    // Execute actual code extracted from index.html:
    {mapping_code}

    // Verify mark at (0, 0) was preserved to match flagCount
    if (cells[0][0].mark === 1 && flagCount === 1) {{
      results.push({{ id: "Issue 1", name: "Pre-Game Flagging Desynchronization", status: "PASS", message: "Flag marks preserved upon board generation" }});
    }} else {{
      results.push({{ id: "Issue 1", name: "Pre-Game Flagging Desynchronization", status: "FAIL", message: "cells[0][0].mark was wiped to " + cells[0][0].mark + " while flagCount is " + flagCount }});
    }}
  }} catch (e) {{
    results.push({{ id: "Issue 1", name: "Pre-Game Flagging Desynchronization", status: "FAIL", message: e.toString() }});
  }}

  // -------------------------------------------------------------------------
  // Test Issue 2: Invalid/corrupt difficulty value in saved config
  // -------------------------------------------------------------------------
  try {{
    const difficultyEl = document.createElement("select");
    difficultyEl.innerHTML = `
      <option value="beginner">Beginner 9x9 / 10</option>
      <option value="intermediate">Intermediate 16x16 / 40</option>
      <option value="expert">Expert 30x16 / 99</option>
      <option value="custom">Custom...</option>
    `;
    const customControlsEl = document.createElement("div");
    const customRowsEl = document.createElement("input");
    const customColsEl = document.createElement("input");
    const customMinesEl = document.createElement("input");
    let rows = 9, cols = 9, mineTotal = 10;
    function clampInt(v, min, max) {{ return Math.min(max, Math.max(min, parseInt(v, 10) || min)); }}

    // Simulate corrupted/empty value from localStorage (setting unknown value gives "")
    difficultyEl.value = "unknown_or_corrupt";

    function readConfigFromForm() {{
      {read_config_code}
    }}

    try {{
      readConfigFromForm();
      if (rows && cols && mineTotal) {{
        results.push({{ id: "Issue 2", name: "Unvalidated Difficulty Rehydration Crash", status: "PASS", message: "Recovered safely from invalid difficulty: rows=" + rows + ", cols=" + cols }});
      }} else {{
        results.push({{ id: "Issue 2", name: "Unvalidated Difficulty Rehydration Crash", status: "FAIL", message: "Invalid dimensions: rows=" + rows }});
      }}
    }} catch (err) {{
      results.push({{ id: "Issue 2", name: "Unvalidated Difficulty Rehydration Crash", status: "FAIL", message: "Crashed with " + err.toString() }});
    }}
  }} catch (e) {{
    results.push({{ id: "Issue 2", name: "Unvalidated Difficulty Rehydration Crash", status: "FAIL", message: e.toString() }});
  }}

  document.getElementById("results").textContent = JSON.stringify(results);
}})();
</script>
</body>
</html>
"""

    with open("tests/test_issues.html", "w", encoding="utf-8") as f:
        f.write(test_html)

    file_url = "file:///" + os.path.abspath("tests/test_issues.html").replace("\\", "/")
    proc = subprocess.run([edge_path, "--headless=new", "--dump-dom", file_url], capture_output=True, text=True)

    start_tag = '<div id="results">'
    end_tag = '</div>'
    start_idx = proc.stdout.find(start_tag)
    end_idx = proc.stdout.find(end_tag, start_idx)
    assert start_idx != -1 and end_idx != -1, "Could not find results in DOM output"

    raw_json = proc.stdout[start_idx + len(start_tag):end_idx].strip()
    data = json.loads(raw_json)
    
    print("==================================================")
    print("TEST SUITE: Issues #1 & #2 (Extracted from index.html)")
    print("==================================================")
    all_pass = True
    for item in data:
        print(f"[{item['status']}] {item['id']}: {item['name']}")
        print(f"       Message: {item['message']}")
        if item['status'] != "PASS":
            all_pass = False
    print("==================================================")
    return all_pass

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
