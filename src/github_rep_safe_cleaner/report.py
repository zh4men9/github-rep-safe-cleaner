from __future__ import annotations

import csv
import html
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import Assessment


def write_run(
    output_dir: Path,
    *,
    owner: str,
    assessments: list[Assessment],
    rate_limit: dict[str, str] | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    counts = Counter(item.category for item in assessments)
    visibility_counts = Counter(item.repository.visibility for item in assessments)

    inventory = {
        "schema_version": 1,
        "generated_at": generated_at,
        "owner": owner,
        "safety": {
            "read_only": True,
            "performs_repository_deletion": False,
            "performs_archiving": False,
            "changes_visibility": False,
            "manual_decision_required": True,
        },
        "summary": {
            "total": len(assessments),
            "categories": dict(counts),
            "visibility": dict(visibility_counts),
        },
        "rate_limit": rate_limit or {},
        "assessments": [item.to_dict() for item in assessments],
    }

    paths = {
        "inventory": output_dir / "inventory.json",
        "csv": output_dir / "inventory.csv",
        "report": output_dir / "report.md",
        "candidates": output_dir / "candidates.md",
        "review": output_dir / "review.html",
        "manifest": output_dir / "manifest.json",
    }
    _write_json(paths["inventory"], inventory)
    _write_csv(paths["csv"], assessments)
    paths["report"].write_text(_render_report(owner, assessments, generated_at), encoding="utf-8")
    paths["candidates"].write_text(_render_candidates(assessments), encoding="utf-8")
    paths["review"].write_text(_render_review_html(inventory), encoding="utf-8")
    _write_json(
        paths["manifest"],
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "owner": owner,
            "files": {key: path.name for key, path in paths.items() if key != "manifest"},
            "manual_test_required": "Open review.html and inspect every DELETE_CANDIDATE before any manual GitHub action.",
        },
    )
    return paths


def default_run_directory(root: Path = Path("artifacts/runs")) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return root / stamp


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, assessments: list[Assessment]) -> None:
    fields = [
        "category",
        "confidence",
        "priority",
        "visibility",
        "full_name",
        "url",
        "fork",
        "archived",
        "size_kb",
        "pushed_at",
        "stars",
        "forks",
        "reasons",
        "counter_evidence",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in assessments:
            repo = item.repository
            writer.writerow(
                {
                    "category": item.category,
                    "confidence": item.confidence,
                    "priority": item.priority,
                    "visibility": repo.visibility,
                    "full_name": repo.full_name,
                    "url": repo.html_url,
                    "fork": repo.fork,
                    "archived": repo.archived,
                    "size_kb": repo.size_kb,
                    "pushed_at": repo.pushed_at or "",
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "reasons": " | ".join(item.reasons),
                    "counter_evidence": " | ".join(item.counter_evidence),
                }
            )


def _render_report(owner: str, assessments: list[Assessment], generated_at: str) -> str:
    counts = Counter(item.category for item in assessments)
    visibility = Counter(item.repository.visibility for item in assessments)
    return f"""# GitHub repository audit report

- Owner: `{owner}`
- Generated: `{generated_at}`
- Total repositories: **{len(assessments)}**
- Public: **{visibility.get('public', 0)}**
- Private: **{visibility.get('private', 0)}**
- Delete candidates: **{counts.get('DELETE_CANDIDATE', 0)}**
- Manual review: **{counts.get('MANUAL_REVIEW', 0)}**
- Keep: **{counts.get('KEEP', 0)}**

## Safety boundary

This run is read-only. It does not delete repositories, archive repositories, change visibility, modify settings, or write to inspected repositories. Every real GitHub action remains manual.

## Review order

1. Open `review.html`.
2. Review every `DELETE_CANDIDATE` one by one.
3. Review `MANUAL_REVIEW`, especially duplicate-name groups and old forks.
4. Export decisions from the page.
5. Perform any GitHub action manually outside this project.
"""


def _render_candidates(assessments: list[Assessment]) -> str:
    lines = [
        "# Candidate checklist",
        "",
        "> This file is advisory only. It never authorizes or performs a GitHub action.",
        "",
    ]
    selected = [item for item in assessments if item.category != "KEEP"]
    if not selected:
        lines.append("No delete candidates or manual-review repositories were found.")
        return "\n".join(lines) + "\n"
    for item in selected:
        repo = item.repository
        lines.extend(
            [
                f"## [ ] {repo.full_name}",
                "",
                f"- Category: `{item.category}`",
                f"- Visibility: `{repo.visibility}`",
                f"- Confidence: `{item.confidence:.2f}`",
                f"- URL: {repo.html_url}",
                "- Reasons:",
                *[f"  - {reason}" for reason in item.reasons],
            ]
        )
        if item.counter_evidence:
            lines.extend(["- Counter-evidence:", *[f"  - {value}" for value in item.counter_evidence]])
        lines.append("")
    return "\n".join(lines)


def _render_review_html(inventory: dict[str, Any]) -> str:
    payload = json.dumps(inventory, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GitHub Repo Safe Cleaner</title>
<style>
:root {{ color-scheme: light; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
body {{ margin:0; background:linear-gradient(135deg,#eef8ff,#f7fbff 45%,#edf5ff); color:#17324d; }}
main {{ max-width:1400px; margin:auto; padding:28px; }}
.panel {{ background:rgba(255,255,255,.92); border:1px solid #cfe5f6; border-radius:18px; box-shadow:0 12px 35px rgba(49,105,150,.10); padding:20px; margin-bottom:18px; }}
h1 {{ margin:0 0 8px; }}
.controls {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
input,select,button {{ border:1px solid #b8d8ef; border-radius:10px; padding:9px 12px; background:white; color:#17324d; }}
button {{ cursor:pointer; }}
button.active {{ outline:3px solid #9bd2f5; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th,td {{ border-bottom:1px solid #dcecf7; padding:10px 8px; text-align:left; vertical-align:top; }}
th {{ position:sticky; top:0; background:#f5fbff; z-index:1; }}
.badge {{ display:inline-block; border-radius:999px; padding:3px 8px; font-weight:600; background:#e6f4ff; }}
.DELETE_CANDIDATE {{ background:#ffe8e8; color:#8c2020; }}
.MANUAL_REVIEW {{ background:#fff4d8; color:#755000; }}
.KEEP {{ background:#e8f7ee; color:#175b35; }}
.reasons {{ max-width:440px; }}
.small {{ opacity:.72; font-size:12px; }}
a {{ color:#176fa8; }}
</style>
</head>
<body><main>
<section class="panel">
<h1>GitHub Repo Safe Cleaner</h1>
<p>只读审计页面。这里的决定只保存在浏览器并可导出；页面不会调用 GitHub API，也不会修改任何仓库。</p>
<div id="summary"></div>
</section>
<section class="panel controls">
<input id="search" placeholder="搜索仓库名称">
<select id="category"><option value="">全部分类</option><option>DELETE_CANDIDATE</option><option>MANUAL_REVIEW</option><option>KEEP</option></select>
<select id="visibility"><option value="">全部可见性</option><option>public</option><option>private</option><option>internal</option></select>
<select id="decision"><option value="">全部人工决定</option><option>UNDECIDED</option><option>KEEP</option><option>DELETE_MANUALLY</option><option>REVIEW_LATER</option></select>
<button id="export">导出 decisions.json</button>
<button id="clear">清空本页决定</button>
</section>
<section class="panel" style="overflow:auto;max-height:72vh">
<table><thead><tr><th>分类</th><th>仓库</th><th>可见性</th><th>证据</th><th>反证</th><th>人工决定</th></tr></thead><tbody id="rows"></tbody></table>
</section>
<script id="inventory" type="application/json">{payload}</script>
<script>
const data=JSON.parse(document.getElementById('inventory').textContent);
const storageKey='github-rep-safe-cleaner:'+data.owner+':decisions:v1';
let decisions=JSON.parse(localStorage.getItem(storageKey)||'{{}}');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}}[c]));
function save(){{localStorage.setItem(storageKey,JSON.stringify(decisions));render();}}
function decide(name,value){{decisions[name]={{decision:value,updated_at:new Date().toISOString()}};save();}}
function render(){{
 const q=document.getElementById('search').value.toLowerCase();
 const cat=document.getElementById('category').value;
 const vis=document.getElementById('visibility').value;
 const dec=document.getElementById('decision').value;
 const items=data.assessments.filter(x=>{{const d=(decisions[x.repository.full_name]?.decision||'UNDECIDED');return (!q||x.repository.full_name.toLowerCase().includes(q))&&(!cat||x.category===cat)&&(!vis||x.repository.visibility===vis)&&(!dec||d===dec);}});
 document.getElementById('summary').textContent=`共 ${{data.summary.total}} 个仓库；当前显示 ${{items.length}} 个；删除候选 ${{data.summary.categories.DELETE_CANDIDATE||0}} 个；人工复核 ${{data.summary.categories.MANUAL_REVIEW||0}} 个。`;
 document.getElementById('rows').innerHTML=items.map(x=>{{const r=x.repository,d=decisions[r.full_name]?.decision||'UNDECIDED';return `<tr><td><span class="badge ${{x.category}}">${{x.category}}</span><div class="small">置信度 ${{x.confidence}}</div></td><td><a target="_blank" rel="noopener" href="${{esc(r.html_url)}}">${{esc(r.full_name)}}</a><div class="small">${{esc(r.description||'无 description')}}</div></td><td>${{esc(r.visibility)}}<div class="small">${{r.fork?'fork ':''}}${{r.archived?'archived':''}}</div></td><td class="reasons">${{x.reasons.map(esc).join('<br>')}}</td><td class="reasons">${{x.counter_evidence.map(esc).join('<br>')}}</td><td><div class="controls"><button class="${{d==='KEEP'?'active':''}}" onclick='decide(${{JSON.stringify(r.full_name)}},"KEEP")'>保留</button><button class="${{d==='DELETE_MANUALLY'?'active':''}}" onclick='decide(${{JSON.stringify(r.full_name)}},"DELETE_MANUALLY")'>手动删除</button><button class="${{d==='REVIEW_LATER'?'active':''}}" onclick='decide(${{JSON.stringify(r.full_name)}},"REVIEW_LATER")'>稍后复核</button></div><div class="small">${{d}}</div></td></tr>`;}}).join('');
}}
for(const id of ['search','category','visibility','decision'])document.getElementById(id).addEventListener('input',render);
document.getElementById('export').onclick=()=>{{const body=JSON.stringify({{schema_version:1,owner:data.owner,exported_at:new Date().toISOString(),decisions}},null,2);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([body],{{type:'application/json'}}));a.download='decisions.json';a.click();URL.revokeObjectURL(a.href);}};
document.getElementById('clear').onclick=()=>{{if(confirm('只清空浏览器中的审核决定，不影响 GitHub。是否继续？')){{decisions={{}};save();}}}};
render();
</script>
</main></body></html>
"""
