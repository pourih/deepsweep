import subprocess
import os
import json

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
test_file = os.path.abspath("tests/test_bugs.html")
file_url = "file:///" + test_file.replace("\\", "/")

proc = subprocess.run([edge_path, "--headless=new", "--dump-dom", file_url], capture_output=True, text=True)
stdout = proc.stdout

# Extract output from <div id="results">...</div>
start_tag = '<div id="results">'
end_tag = '</div>'
start_idx = stdout.find(start_tag)
end_idx = stdout.find(end_tag, start_idx)

if start_idx != -1 and end_idx != -1:
    json_text = stdout[start_idx + len(start_tag):end_idx].strip()
    try:
        results = json.loads(json_text)
        print("=== UNIT TEST SUITE RESULTS (FAILING TO PROVE BUGS EXIST) ===")
        for res in results:
            print(f"[{res['status']}] {res['name']}")
            if 'error' in res:
                print(f"    Details: {res['error']}")
    except Exception as e:
        print("Raw output:", json_text)
else:
    print("Could not find results div in stdout.")
    print(stdout[:500])
