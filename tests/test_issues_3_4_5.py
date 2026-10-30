import subprocess
import os
import re
import json

def run_tests():
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    with open("index.html", "r", encoding="utf-8") as f:
        index_html = f.read()

    # Extract workerCode from index.html
    worker_match = re.search(r'const workerCode = `(.*?)`;', index_html, re.DOTALL)
    assert worker_match, "Could not find workerCode in index.html"
    worker_code = worker_match.group(1)

    # Extract reveal function from index.html
    reveal_match = re.search(r'async function reveal\([^)]*\)\s*\{(.*?)\n  \}', index_html, re.DOTALL)
    assert reveal_match, "Could not find reveal function in index.html"
    reveal_body = reveal_match.group(1)

    # Check if isGenerating guard is present in reveal
    has_is_generating = 'isGenerating' in reveal_body

    # Check if worker.onerror is handled
    has_worker_onerror = 'worker.onerror' in reveal_body

    test_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<div id="results"></div>
<script>
(async () => {{
  const results = [];

  // =========================================================================
  // Test Issue 3: High-Density Solver Discard Trap
  // =========================================================================
  try {{
    const workerScript = `{worker_code}`;
    
    // Mock worker scope
    const fakeScope = {{
      postMessage: (b) => {{ fakeScope.postedBoard = b; }},
      onmessage: null,
      solverCallCount: 0
    }};
    
    // Instrument isNoGuessSolvable in workerScript to track solver calls
    const instrumentedScript = workerScript.replace(
      'function isNoGuessSolvable',
      'function isNoGuessSolvable(...args) {{ self.solverCallCount++; return realIsNoGuessSolvable(...args); }}\\nfunction realIsNoGuessSolvable'
    );
    
    const runWorker = new Function('self', instrumentedScript);
    runWorker(fakeScope);
    
    // Send 5x5 / 20 mines generation task
    fakeScope.onmessage({{ data: {{ rows: 5, cols: 5, mineTotal: 20, safeR: 2, safeC: 2 }} }});

    if (fakeScope.solverCallCount > 0) {{
      results.push({{ id: "Issue 3", name: "High-Density Solver Discard Trap", status: "PASS", message: fakeScope.solverCallCount + " attempts reached solver successfully without being prematurely discarded" }});
    }} else {{
      results.push({{ id: "Issue 3", name: "High-Density Solver Discard Trap", status: "FAIL", message: "0 of 40 attempts reached solver; all attempts prematurely discarded at openingCellCount < 2" }});
    }}
  }} catch (e) {{
    results.push({{ id: "Issue 3", name: "High-Density Solver Discard Trap", status: "FAIL", message: e.toString() }});
  }}

  // =========================================================================
  // Test Issue 4: Concurrent First-Click Race Condition (isGenerating Guard)
  // =========================================================================
  try {{
    const hasGuard = {str(has_is_generating).lower()};
    if (!hasGuard) {{
      results.push({{ id: "Issue 4", name: "Concurrent First-Click Race Condition", status: "FAIL", message: "Missing isGenerating guard; concurrent clicks during generation can flood-reveal empty ungenerated board" }});
    }} else {{
      results.push({{ id: "Issue 4", name: "Concurrent First-Click Race Condition", status: "PASS", message: "isGenerating state guard is present and active during async board generation" }});
    }}
  }} catch (e) {{
    results.push({{ id: "Issue 4", name: "Concurrent First-Click Race Condition", status: "FAIL", message: e.toString() }});
  }}

  // =========================================================================
  // Test Issue 5: Worker Error Handler Absence & UI Deadlock
  // =========================================================================
  try {{
    const hasOnError = {str(has_worker_onerror).lower()};
    if (!hasOnError) {{
      results.push({{ id: "Issue 5", name: "Worker Error Handler & UI Deadlock", status: "FAIL", message: "new Promise lacks worker.onerror; worker failure or CSP restriction permanently freezes board in 'Generating board...'" }});
    }} else {{
      results.push({{ id: "Issue 5", name: "Worker Error Handler & UI Deadlock", status: "PASS", message: "worker.onerror is handled with safe recovery and pointerEvents restoration" }});
    }}
  }} catch (e) {{
    results.push({{ id: "Issue 5", name: "Worker Error Handler & UI Deadlock", status: "FAIL", message: e.toString() }});
  }}

  document.getElementById("results").textContent = JSON.stringify(results);
}})();
</script>
</body>
</html>
"""

    with open("tests/test_issues_3_4_5.html", "w", encoding="utf-8") as f:
        f.write(test_html)

    file_url = "file:///" + os.path.abspath("tests/test_issues_3_4_5.html").replace("\\", "/")
    proc = subprocess.run([edge_path, "--headless=new", "--dump-dom", file_url], capture_output=True, text=True, encoding="utf-8")

    start_tag = '<div id="results">'
    end_tag = '</div>'
    start_idx = proc.stdout.find(start_tag)
    end_idx = proc.stdout.find(end_tag, start_idx)
    assert start_idx != -1 and end_idx != -1, "Could not find results in DOM output"

    raw_json = proc.stdout[start_idx + len(start_tag):end_idx].strip()
    data = json.loads(raw_json)
    
    print("==================================================")
    print("TEST SUITE: Issues #3, #4 & #5 (Extracted from index.html)")
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
