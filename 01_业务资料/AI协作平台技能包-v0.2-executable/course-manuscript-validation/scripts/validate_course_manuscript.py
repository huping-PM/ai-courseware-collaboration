#!/usr/bin/env python3
"""Deterministic baseline checks for course manuscript drafts."""
import argparse
import json
import re
from pathlib import Path

PLACEHOLDER = re.compile(r"(?:TODO|TBD|\[角色名\]|\[待补[^\]]*\]|冻结的问题)", re.I)

def issue(rule_id, location, evidence, hint):
    return {"severity": "P0", "rule_id": rule_id, "location": location,
            "evidence": evidence, "repair_hint": hint}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-spec", required=True)
    parser.add_argument("--manuscript", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spec = json.loads(Path(args.task_spec).read_text(encoding="utf-8"))
    text = Path(args.manuscript).read_text(encoding="utf-8")
    findings = []
    declared = {e["name"] for e in spec.get("entities", []) if e.get("name")}
    mentioned = set(re.findall(r"小[王李张赵陈刘]|李老师|王老师", text))
    for name in sorted(mentioned - declared):
        findings.append(issue("ROLE_UNDECLARED", "manuscript", name, "将角色加入任务卡并确认，或删除/改为已声明角色。"))
    for match in PLACEHOLDER.finditer(text):
        findings.append(issue("TEMPLATE_RESIDUE", "manuscript", match.group(), "删除残留文本并补齐正式内容。"))
    for section in spec.get("required_sections", []):
        if section not in text:
            findings.append(issue("SECTION_MISSING", "manuscript", section, "补齐任务卡要求的栏目。"))
    count = len(re.findall(r"(?:^|\n)\s*\d+\.\s*【", text))
    if spec.get("exercise_count") is not None and count != spec["exercise_count"]:
        findings.append(issue("EXERCISE_COUNT", "练习题", str(count), "使练习题数量与任务卡一致。"))
    report = {"status": "BLOCKED" if findings else "PASS", "blocking_issue_count": len(findings), "findings": findings}
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
