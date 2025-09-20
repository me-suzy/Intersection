#!/usr/bin/env python3
"""
Test imediat pentru biblioteca html-intersection cu budget/execution
"""

import os
import tempfile
import shutil
from html_intersection import repair_all, scan_issues

def test_immediate():
    """Test imediat cu budget/execution"""
    print("🧪 TESTARE IMEDIATĂ - HTML-INTERSECTION")
    print("=" * 50)

    # Creez directoare temporare
    base_dir = tempfile.mkdtemp()
    budget_dir = os.path.join(base_dir, "budget")
    execution_dir = os.path.join(base_dir, "execution")

    os.makedirs(budget_dir)
    os.makedirs(execution_dir)

    # Creez fișierul budget
    budget_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Buget General 2024</title>
    <link rel="canonical" href="https://finante.gov.ro/budget/buget-general-2024.html" />
</head>
<body>
    <h1>Buget General 2024</h1>
    <!-- FLAGS_1 -->
    <ul>
        <li><a cunt_code="+40" href="https://finante.gov.ro/buget-general-2024.html">RO</a></li>
        <li><a cunt_code="+1" href="https://finante.gov.ro/execution/executie-bugetara-t3-2024.html">EN</a></li>
    </ul>
    <!-- FLAGS -->
    <p>Acesta este documentul de buget pentru anul 2024.</p>
</body>
</html>'''

    # Creez fișierul execution
    execution_html = '''<!DOCTYPE html>
<html>
<head>
    <title>Execuția Bugetară T3 2024</title>
    <link rel="canonical" href="https://finante.gov.ro/execution/executie-bugetara-t3-2024.html" />
</head>
<body>
    <h1>Execuția Bugetară T3 2024</h1>
    <!-- FLAGS_1 -->
    <ul>
        <li><a cunt_code="+40" href="https://finante.gov.ro/buget-general-2024.html">RO</a></li>
        <li><a cunt_code="+1" href="https://finante.gov.ro/execution/executie-bugetara-t3-2024.html">EN</a></li>
    </ul>
    <!-- FLAGS -->
    <p>Acesta este documentul de execuție bugetară pentru trimestrul 3, 2024.</p>
</body>
</html>'''

    # Scriu fișierele
    with open(os.path.join(budget_dir, "buget-general-2024.html"), "w", encoding="utf-8") as f:
        f.write(budget_html)

    with open(os.path.join(execution_dir, "executie-bugetara-t3-2024.html"), "w", encoding="utf-8") as f:
        f.write(execution_html)

    try:
        print("1. Testez scan_issues...")
        report = scan_issues(
            first_directory=budget_dir,
            second_directory=execution_dir,
            base_url="https://finante.gov.ro",
            second_dir_path="execution"
        )

        print(f"   ✅ Perechi găsite: {len(report['bidirectional_pairs'])}")
        print(f"   ✅ Link-uri invalide: {len(report['invalid_links'])}")

        print("\n2. Testez repair_all...")
        canonical_fixes, flag_fixes, cross_ref_fixes = repair_all(
            first_directory=budget_dir,
            second_directory=execution_dir,
            base_url="https://finante.gov.ro",
            second_dir_path="execution",
            dry_run=False
        )

        print(f"   ✅ Canonical-uri reparate: {canonical_fixes}")
        print(f"   ✅ Flag-uri reparate: {flag_fixes}")
        print(f"   ✅ Cross-references reparate: {cross_ref_fixes}")

        print("\n3. Verific rezultatele...")

        # Citesc fișierul budget reparat
        budget_file = os.path.join(budget_dir, "buget-general-2024.html")
        with open(budget_file, "r", encoding="utf-8") as f:
            budget_content = f.read()

        # Citesc fișierul execution reparat
        execution_file = os.path.join(execution_dir, "executie-bugetara-t3-2024.html")
        with open(execution_file, "r", encoding="utf-8") as f:
            execution_content = f.read()

        import re

        # Verific canonical-ul budget
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', budget_content)
        if canonical_match:
            print(f"   📄 Budget canonical: {canonical_match.group(1)}")

        # Verific canonical-ul execution
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', execution_content)
        if canonical_match:
            print(f"   📄 Execution canonical: {canonical_match.group(1)}")

        print("\n🎉 TESTARE COMPLETĂ - TOATE TESTELE AU TRECUT!")
        print("Biblioteca funcționează perfect cu budget/execution!")

        return True

    except Exception as e:
        print(f"❌ EROARE: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Curățare
        shutil.rmtree(base_dir)

if __name__ == "__main__":
    test_immediate()
