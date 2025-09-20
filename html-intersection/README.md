
```markdown
html-intersection
==================

Fix canonical links, FLAGS, and RO↔EN cross-references across mirrored HTML directories.

What it does
------------
- Ensures each file's `<link rel="canonical" ...>` matches its exact filename (case-sensitive)
- Ensures the FLAGS links for RO (`+40`) and EN (`+1`) match the canonical in the same file
- Synchronizes cross-references between `ro/` and `en/` files so the pair points to each other (RO<->EN)
- Detects and reports unresolved cases:
  - invalid links (pointing to non-existent files)
  - pairs with no common links in FLAGS (all four links different)
  - unmatched RO/EN files that remain without a valid pair

Understanding "HTML Intersections"
---------------------------------
This library manages **intersections** - points where HTML files cross-reference each other through links. In complex HTML ecosystems, documents often reference each other bidirectionally, and maintaining consistency across these reference networks is crucial for:

- **Multilingual websites** - Language pairs must stay synchronized
- **Document management systems** - Related documents need consistent linking
- **Content validation** - Ensuring HTML ecosystems remain coherent over time
- **SEO optimization** - Proper canonical and cross-reference structure

The library detects discrepancies where documents point to different targets and automatically repairs these inconsistencies to maintain perfect synchronization.

Inspired by the step-by-step process in your Intersection scripts and packaged like a PyPI library (style similar to `html` on PyPI).

Install
-------
```bash
pip install html-intersection
```

Quick start
-----------
```python
from html_intersection.core import repair_all

repair_all(
    ro_directory=r"E:\\path\\to\\site\\ro",
    en_directory=r"E:\\path\\to\\site\\en",
    base_url="https://neculaifantanaru.com",
)
```

CLI usage
---------
```bash
html-intersection repair --ro-dir "E:\\path\\to\\site\\ro" --en-dir "E:\\path\\to\\site\\en" --base-url https://neculaifantanaru.com
```

Commands:
- `repair` (runs all 3 steps)
- `fix-canonicals`
- `fix-flags`
- `sync`
- `scan` (prints detected RO↔EN pairs; add `--report` to include invalid links, mismatches, unmatched files)

Python API
----------
- `fix_canonicals(ro_directory, en_directory, base_url, dry_run=False, backup_ext=None)`
- `fix_flags_match_canonical(ro_directory, en_directory, base_url, dry_run=False, backup_ext=None)`
- `sync_cross_references(ro_directory, en_directory, base_url, dry_run=False, backup_ext=None)`
- `repair_all(ro_directory, en_directory, base_url, dry_run=False, backup_ext=None)`
- `scan_issues(ro_directory, en_directory, base_url)` - Returns detailed analysis report

Examples
--------

### 1) Financial Document Synchronization
```python
from html_intersection.core import repair_all, scan_issues

# Repair cross-references between budget and execution documents
base_url = "https://finante.gov.ro"
budget_dir = r"E:\\documents\\budget"
execution_dir = r"E:\\documents\\execution"

# First, analyze the current state
issues = scan_issues(budget_dir, execution_dir, base_url)
print(f"Found {len(issues['mismatched_pairs'])} inconsistent document pairs")

# Repair all inconsistencies
canonical_fixes, flag_fixes, cross_ref_fixes = repair_all(
    budget_dir, execution_dir, base_url
)

print(f"Repaired: {cross_ref_fixes} cross-references")
```

### 2) Content Validation Before Publishing
```python
from html_intersection.core import scan_issues

# Validate content consistency before deployment
def validate_site_consistency(ro_path, en_path, base_url):
    report = scan_issues(ro_path, en_path, base_url)
    
    if report["invalid_links"]:
        print("⚠️  Invalid links found:")
        for link in report["invalid_links"]:
            print(f"   {link}")
    
    if report["mismatched_pairs"]:
        print("⚠️  Mismatched cross-references:")
        for ro_file, en_file, details in report["mismatched_pairs"]:
            print(f"   {ro_file} ↔ {en_file}: {details}")
    
    if report["unmatched_ro"] or report["unmatched_en"]:
        print(f"⚠️  Unmatched files: {len(report['unmatched_ro'])} RO, {len(report['unmatched_en'])} EN")
    
    return len(report["invalid_links"]) == 0 and len(report["mismatched_pairs"]) == 0

# Usage
is_consistent = validate_site_consistency(
    ro_path=r"E:\\website\\ro",
    en_path=r"E:\\website\\en", 
    base_url="https://example.com"
)

if is_consistent:
    print("✅ All cross-references are consistent!")
else:
    print("❌ Inconsistencies detected - run repair_all() to fix")
```

### 3) Basic repair
```python
from html_intersection.core import repair_all

repair_all(
    ro_directory=r"E:\\site\\ro",
    en_directory=r"E:\\site\\en",
    base_url="https://neculaifantanaru.com",
)
```

### 4) Dry run (no writes)
```python
from html_intersection.core import repair_all

repair_all(
    ro_directory=r"E:\\site\\ro",
    en_directory=r"E:\\site\\en",
    base_url="https://neculaifantanaru.com",
    dry_run=True,
)
```

### 5) CLI one step at a time
```bash
html-intersection fix-canonicals --ro-dir "E:\\site\\ro" --en-dir "E:\\site\\en" --base-url https://neculaifantanaru.com
html-intersection fix-flags      --ro-dir "E:\\site\\ro" --en-dir "E:\\site\\en" --base-url https://neculaifantanaru.com
html-intersection sync           --ro-dir "E:\\site\\ro" --en-dir "E:\\site\\en" --base-url https://neculaifantanaru.com

# Scan with detailed report
html-intersection scan           --ro-dir "E:\\site\\ro" --en-dir "E:\\site\\en" --base-url https://neculaifantanaru.com --report
```

How the logic works (3 steps)
-----------------------------
1. **Canonicals**: set canonical to exact file name (case-sensitive); RO → `https://.../<name>.html`, EN → `https://.../en/<Name>.html`.
2. **FLAGS = canonical** in the same file: RO uses `cunt_code="+40"`; EN uses `cunt_code="+1"`.
3. **Cross-references RO↔EN**: in `ro/<name>.html` the `+1` link points to the paired `en/<Name>.html`; in `en/<Name>.html` the `+40` link points to the paired `ro/<name>.html`.

Technical Details
----------------
- **Link normalization**: Automatically fixes `.html.html` → `.html` and other common issues
- **Bidirectional validation**: Ensures both directions of cross-references are consistent
- **Smart file pairing**: Uses FLAG links and filename similarity to detect document relationships
- **Case sensitivity**: Preserves exact filename casing in all operations
- **Flexible matching**: Accepts both `"+40"` and `"\+40"` formats in cunt_code attributes

Use Cases
---------
- **Multilingual websites**: Maintain synchronization between language versions
- **Documentation systems**: Keep related documents properly cross-referenced  
- **Content management**: Validate link integrity across document collections
- **SEO maintenance**: Ensure canonical URLs and cross-references support search optimization
- **Quality assurance**: Automated validation before content deployment

Notes on robustness
-------------------
- The matching for `+40` and `+1` accepts both `"+40"` and `"\+40"` (and similarly for `+1`).
- Accidental `...html.html` is normalized to `...html` when comparing and fixing.
- `scan --report` surfaces invalid links, mismatched pairs with no common links, and files left unmatched.
- Files are written UTF-8; the reader tries `utf-8`, `latin1`, `cp1252`, `iso-8859-1`.
- You can pass `backup_ext=".bak"` to keep a backup of modified files.
- The library aims to follow the precise, case-sensitive flow in your instructions.

Windows install and build
-------------------------
```powershell
# Create and activate venv
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install build tooling
py -m pip install --upgrade pip build twine

# Build the wheel and sdist
py -m build

# Upload to TestPyPI (recommended first)
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-<YOUR_TESTPYPI_TOKEN>"
py -m twine upload --repository testpypi dist/*

# Upload to PyPI (when ready)
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-<YOUR_PYPI_TOKEN>"
py -m twine upload dist/*
```

References
----------
- Diacritice project structure reference: [`https://github.com/me-suzy/html-intersection`](https://github.com/me-suzy/html-intersection)
- PyPI `html` package page style reference: [`https://pypi.org/project/html/`](https://pypi.org/project/html/)
```

Principalele îmbunătățiri:

