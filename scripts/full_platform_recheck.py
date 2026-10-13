"""Run final QA in resumable groups; keep output private in ignored tmp logs.

Run --group backend and --group browser in separate background processes.
Each evidence entry is written only after its command actually finishes.
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv/Scripts/python.exe")
JOBS = {
    "backend": [
        ("regression", ["-m", "pytest", "-q", "--junitxml=tmp/master_regression_final.xml"]),
        ("data_models", ["scripts/master_data_qa.py"]),
        ("security", ["scripts/security_audit.py"]),
        ("requirements", ["-m", "pip", "check"]),
        ("dependencies", ["-m", "pip_audit", "--local", "--format", "json", "--output", "tmp/dependency_audit.json"]),
    ],
    "browser": [
        ("workspace", ["scripts/master_browser_qa.py"]),
        ("uploads", ["scripts/uploads_browser_qa.py", "--skip-live"]),
        ("chart_controls", ["scripts/chart_controls_qa.py"]),
        ("connected_reports", ["scripts/master_workflow_qa.py"]),
        ("comparison", ["scripts/comparison_browser_qa.py"]),
        ("comparison_controls", ["scripts/comparison_chart_qa.py"]),
        ("sevika_local", ["scripts/sevika_browser_qa.py", "--local-only"]),
        ("live_insights", ["scripts/hf_live_dataset_qa.py", "--execute"]),
        ("sevika_live", ["scripts/sevika_live_browser_qa.py"]),
        ("public_login", ["scripts/landing_login_qa.py"]),
        ("themes_sidebar_motion", ["scripts/unified_experience_qa.py"]),
    ],
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", required=True, choices=JOBS)
    parser.add_argument("--resume", action="store_true", help="Skip commands already passed in this run's status file.")
    parser.add_argument("--skip-live", action="store_true", help="Record known provider quota blocking; finish the independent local checks.")
    args = parser.parse_args()
    folder = ROOT / "tmp/recheck"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (args.group + "-status.json")
    report = json.loads(path.read_text()) if args.resume and path.exists() else {
        "started_at": utc(), "group": args.group, "passed": False, "steps": []
    }
    for name, command in JOBS[args.group]:
        if args.skip_live and name in {"live_insights", "sevika_live"}:
            step = next((s for s in report['steps'] if s['name']==name), {'name':name, 'command':command, 'seconds':0})
            step.update(status='blocked', reason='Actual Hugging Face request rejected: inference credits exhausted. No repeated provider calls.')
            report['steps']=[s for s in report['steps'] if s['name']!=name]+[step]
            path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            continue
        if args.resume and any(s["name"] == name and s.get("exit_code") == 0 for s in report["steps"]):
            continue
        step = {"name": name, "started_at": utc(), "command": command, "status": "running"}
        report["steps"] = [s for s in report["steps"] if s["name"] != name] + [step]
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        start = time.perf_counter()
        with (folder / (name + ".log")).open("w", encoding="utf-8") as output:
            try:
                result = subprocess.run([PYTHON, *command], cwd=ROOT, stdout=output,
                                        stderr=subprocess.STDOUT, timeout=1800, check=False)
                step["exit_code"] = result.returncode
            except subprocess.TimeoutExpired:
                step["exit_code"] = 124
                step["reason"] = "Command exceeded the 30-minute per-step limit."
        step.update(finished_at=utc(), seconds=round(time.perf_counter() - start, 2),
                    status="passed" if step["exit_code"] == 0 else "failed")
        report["finished_at"] = utc()
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(name, step["status"], step["seconds"], flush=True)
        if step["exit_code"]:
            return step["exit_code"]
    report["local_checks_passed"] = all(s['status']=='passed' for s in report['steps'] if s['name'] not in {'live_insights','sevika_live'})
    report["blocked_steps"] = [s['name'] for s in report['steps'] if s['status']=='blocked']
    report["passed"] = report['local_checks_passed'] and not report['blocked_steps']
    report["completed"] = True
    report["finished_at"] = utc()
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
