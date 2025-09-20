import os
import re
from pathlib import Path

ro_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro'
en_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en'

def read_file_with_fallback_encoding(file_path):
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    print(f"Nu s-a putut citi fișierul {file_path}")
    return None

def write_file_with_encoding(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Eroare la salvarea fișierului {file_path}: {e}")
        return False

def normalize_value(val):
    if val is None:
        return None
    val = val.replace('\xa0', ' ').strip()
    val = val.replace('–', '-').replace('—', '-')
    return val

def get_links_from_flags(content, filename, directory):
    flags_section = re.search(r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->', content, re.DOTALL)
    if not flags_section:
        print(f"\nFIȘIER PROBLEMATIC: {os.path.join(directory, filename)} - Nu s-a găsit secțiunea FLAGS")
        return None

    flags_content = flags_section.group(1)

    # Try the old format first (with img tags and title attributes)
    ro_match = re.search(r'<a href="https://neculaifantanaru\.com/+([^"]+)"[^>]*?><img[^>]*?title="ro"', flags_content)
    en_match = re.search(r'<a href="https://neculaifantanaru\.com/+en/([^"]+)"[^>]*?><img[^>]*?title="en"', flags_content)

    # If old format not found, try the new format (with li elements and cunt_code attributes)
    if not ro_match or not en_match:
        # New format patterns
        ro_match_new = re.search(r'<li><a cunt_code="\+40" href="https://neculaifantanaru\.com/([^"]+)"', flags_content)
        en_match_new = re.search(r'<li><a cunt_code="\+1" href="https://neculaifantanaru\.com/en/([^"]+)"', flags_content)

        if ro_match_new:
            ro_match = ro_match_new
        if en_match_new:
            en_match = en_match_new

    # If still no matches found, try a more flexible approach for new format
    if not ro_match or not en_match:
        if not ro_match:
            ro_match_flexible = re.search(r'<li><a[^>]*href="https://neculaifantanaru\.com/([^"]+)"[^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>Romania</span>', flags_content)
            if ro_match_flexible:
                ro_match = ro_match_flexible

        if not en_match:
            en_match_flexible = re.search(r'<li><a[^>]*href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>United States</span>', flags_content)
            if en_match_flexible:
                en_match = en_match_flexible

    if not ro_match or not en_match:
        return None

    return {
        'ro_link': normalize_value(ro_match.group(1)),
        'en_link': normalize_value(en_match.group(1))
    }

def fix_links_in_flags(content, correct_ro_link, correct_en_link):
    """
    Fix the links in the FLAGS section of the content
    """
    flags_section = re.search(r'(<!-- FLAGS_1 -->)(.*?)(<!-- FLAGS -->)', content, re.DOTALL)
    if not flags_section:
        return content, False

    original_flags_content = flags_section.group(2)
    fixed_flags_content = original_flags_content

    # Fix RO links in old format
    fixed_flags_content = re.sub(
        r'<a href="https://neculaifantanaru\.com/+[^"]*"([^>]*?><img[^>]*?title="ro")',
        f'<a href="https://neculaifantanaru.com/{correct_ro_link}"\\1',
        fixed_flags_content
    )

    # Fix EN links in old format
    fixed_flags_content = re.sub(
        r'<a href="https://neculaifantanaru\.com/+en/[^"]*"([^>]*?><img[^>]*?title="en")',
        f'<a href="https://neculaifantanaru.com/en/{correct_en_link}"\\1',
        fixed_flags_content
    )

    # Fix RO links in new format (with cunt_code="+40")
    fixed_flags_content = re.sub(
        r'<li><a cunt_code="\+40" href="https://neculaifantanaru\.com/[^"]*"',
        f'<li><a cunt_code="+40" href="https://neculaifantanaru.com/{correct_ro_link}"',
        fixed_flags_content
    )

    # Fix EN links in new format (with cunt_code="+1")
    fixed_flags_content = re.sub(
        r'<li><a cunt_code="\+1" href="https://neculaifantanaru\.com/en/[^"]*"',
        f'<li><a cunt_code="+1" href="https://neculaifantanaru.com/en/{correct_en_link}"',
        fixed_flags_content
    )

    # Fix RO links in flexible new format (Romania)
    fixed_flags_content = re.sub(
        r'<li><a([^>]*) href="https://neculaifantanaru\.com/[^"]*"([^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>Romania</span>)',
        f'<li><a\\1 href="https://neculaifantanaru.com/{correct_ro_link}"\\2',
        fixed_flags_content
    )

    # Fix EN links in flexible new format (United States)
    fixed_flags_content = re.sub(
        r'<li><a([^>]*) href="https://neculaifantanaru\.com/en/[^"]*"([^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>United States</span>)',
        f'<li><a\\1 href="https://neculaifantanaru.com/en/{correct_en_link}"\\2',
        fixed_flags_content
    )

    if fixed_flags_content != original_flags_content:
        new_content = content.replace(flags_section.group(0), flags_section.group(1) + fixed_flags_content + flags_section.group(3))
        return new_content, True
    else:
        return content, False

def compare_and_check_files():
    issues_found = []
    unique_ro_files = []

    # First pass: collect all RO files and their EN references
    ro_files_data = {}
    for ro_file in os.listdir(ro_directory):
        if not ro_file.endswith('.html'):
            continue

        ro_path = os.path.join(ro_directory, ro_file)
        ro_content = read_file_with_fallback_encoding(ro_path)
        if not ro_content:
            continue

        ro_links = get_links_from_flags(ro_content, ro_file, ro_directory)
        if not ro_links:
            continue

        ro_files_data[ro_file] = ro_links

    # Second pass: identify which EN files belong to which RO files
    en_to_ro_mapping = {}
    for ro_file, ro_links in ro_files_data.items():
        expected_en_filename = ro_links['en_link']
        if expected_en_filename:
            en_path = os.path.join(en_directory, expected_en_filename)
            if os.path.exists(en_path):
                en_content = read_file_with_fallback_encoding(en_path)
                if en_content:
                    en_links = get_links_from_flags(en_content, expected_en_filename, en_directory)
                    if en_links and en_links['ro_link']:
                        # This EN file truly belongs to the RO file mentioned in its FLAGS
                        en_to_ro_mapping[expected_en_filename] = en_links['ro_link']

    # Third pass: identify unique RO files and regular issues
    for ro_file, ro_links in ro_files_data.items():
        print(f"Procesare fișier: {ro_file}", flush=True)

        expected_en_filename = ro_links['en_link']
        is_unique_ro = False

        # Check if this RO file is unique
        if expected_en_filename in en_to_ro_mapping:
            true_owner = en_to_ro_mapping[expected_en_filename]
            if true_owner != ro_file:
                # This RO file is referencing an EN file that belongs to another RO file
                is_unique_ro = True
                print(f"  🟡 Fișierul RO {ro_file} este UNIC")
                print(f"     Referențiază EN: {expected_en_filename}")
                print(f"     Dar EN-ul aparține la: {true_owner}")

                unique_ro_files.append({
                    'ro_file': ro_file,
                    'referenced_en': expected_en_filename,
                    'en_belongs_to': true_owner
                })
                continue

        # If not unique, process as regular file
        en_file = None
        en_content = None
        en_links = None

        if expected_en_filename:
            en_path = os.path.join(en_directory, expected_en_filename)
            if os.path.exists(en_path):
                en_file = expected_en_filename
                en_content = read_file_with_fallback_encoding(en_path)
                if en_content:
                    en_links = get_links_from_flags(en_content, en_file, en_directory)
            else:
                # Check for case-insensitive match
                en_files = [f for f in os.listdir(en_directory) if f.lower() == expected_en_filename.lower()]
                if en_files:
                    en_file = en_files[0]
                    en_path = os.path.join(en_directory, en_file)
                    en_content = read_file_with_fallback_encoding(en_path)
                    if en_content:
                        en_links = get_links_from_flags(en_content, en_file, en_directory)
                    print(f"  ⚠️ Fișierul EN există cu case diferit: {en_file} (așteptat: {expected_en_filename})")
                else:
                    print(f"  ⚠️ Fișierul EN nu există: {expected_en_filename}")

        # Regular error checking
        correct_ro_link = normalize_value(ro_file)
        correct_en_link = normalize_value(en_file) if en_file else normalize_value(expected_en_filename)

        print(f"  🔎 RO file links: RO={ro_links['ro_link']}, EN={ro_links['en_link']}")
        print(f"  🔎 Expected: RO={correct_ro_link}, EN={correct_en_link}")
        if en_links:
            print(f"  🔎 EN file links: RO={en_links['ro_link']}, EN={en_links['en_link']}")

        ro_has_error = False
        en_has_error = False

        if ro_links['ro_link'] != correct_ro_link:
            ro_has_error = True
        if ro_links['en_link'] != correct_en_link:
            ro_has_error = True

        if en_links:
            if en_links['ro_link'] != correct_ro_link:
                en_has_error = True
            if en_links['en_link'] != correct_en_link:
                en_has_error = True

        if ro_has_error or en_has_error:
            issue_details = {
                'ro_file': ro_file,
                'en_file': en_file,
                'ro_has_error': ro_has_error,
                'en_has_error': en_has_error,
                'ro_links': ro_links,
                'en_links': en_links,
                'correct_ro_link': correct_ro_link,
                'correct_en_link': correct_en_link,
                'ro_content': read_file_with_fallback_encoding(os.path.join(ro_directory, ro_file)),
                'en_content': en_content
            }
            issues_found.append(issue_details)

            print(f"  🔍 Identificată problemă în: {ro_file}")

            if ro_has_error:
                print(f"    → Erori în fișierul RO: {ro_file}")
                if ro_links['ro_link'] != correct_ro_link:
                    print(f"      ✗ Link RO greșit: {ro_links['ro_link']} → Ar trebui să fie: {correct_ro_link}")
                if ro_links['en_link'] != correct_en_link:
                    print(f"      ✗ Link EN greșit: {ro_links['en_link']} → Ar trebui să fie: {correct_en_link}")

            if en_has_error:
                print(f"    → Erori în fișierul EN: {en_file}")
                if en_links['ro_link'] != correct_ro_link:
                    print(f"      ✗ Link RO greșit: {en_links['ro_link']} → Ar trebui să fie: {correct_ro_link}")
                if en_links['en_link'] != correct_en_link:
                    print(f"      ✗ Link EN greșit: {en_links['en_link']} → Ar trebui să fie: {correct_en_link}")

            print()

    return issues_found, unique_ro_files

def fix_issues(issues_found):
    """
    Fix the issues found in regular files (not unique RO files)
    """
    fixed_files = []

    for issue in issues_found:
        ro_file = issue['ro_file']
        en_file = issue['en_file']

        # Fix RO file if it has errors
        if issue['ro_has_error'] and issue['ro_content']:
            print(f"\n🔧 Reparare fișier RO: {ro_file}")

            fixed_content, was_fixed = fix_links_in_flags(
                issue['ro_content'],
                issue['correct_ro_link'],
                issue['correct_en_link']
            )

            if was_fixed:
                ro_path = os.path.join(ro_directory, ro_file)
                if write_file_with_encoding(ro_path, fixed_content):
                    print(f"  ✅ Fișierul RO {ro_file} a fost corectat cu succes!")
                    fixed_files.append(f"RO: {ro_file}")
                else:
                    print(f"  ❌ Eroare la salvarea fișierului RO {ro_file}")
            else:
                print(f"  ⚠️ Nu s-au putut face modificări în fișierul RO {ro_file}")

        # Fix EN file if it has errors and exists
        if issue['en_has_error'] and issue['en_content'] and en_file:
            print(f"\n🔧 Reparare fișier EN: {en_file}")

            fixed_content, was_fixed = fix_links_in_flags(
                issue['en_content'],
                issue['correct_ro_link'],
                issue['correct_en_link']
            )

            if was_fixed:
                en_path = os.path.join(en_directory, en_file)
                if write_file_with_encoding(en_path, fixed_content):
                    print(f"  ✅ Fișierul EN {en_file} a fost corectat cu succes!")
                    fixed_files.append(f"EN: {en_file}")
                else:
                    print(f"  ❌ Eroare la salvarea fișierului EN {en_file}")
            else:
                print(f"  ⚠️ Nu s-au putut face modificări în fișierul EN {en_file}")

    return fixed_files

# Rulează verificarea
print("\nVerificare link-uri în FLAGS...")
print("=" * 80)

issues_found, unique_ro_files = compare_and_check_files()

# Report unique RO files
if unique_ro_files:
    print(f"\n🟡 FIȘIERE RO UNICE (fără corespondent real în EN):")
    print("=" * 80)
    print(f"Total fișiere RO unice găsite: {len(unique_ro_files)}")

    for i, unique in enumerate(unique_ro_files, 1):
        print(f"\n{i}. Fișierul RO UNIC: {unique['ro_file']}")
        print(f"   Referențiază EN: {unique['referenced_en']}")
        print(f"   Dar EN-ul aparține la: {unique['en_belongs_to']}")

    print("=" * 80)

# Report and fix regular issues
if issues_found:
    print(f"\n🔍 VERIFICARE COMPLETĂ - PROBLEME REGULATE!")
    print("=" * 80)
    print(f"Total fișiere cu probleme găsite: {len(issues_found)}")

    for i, issue in enumerate(issues_found, 1):
        print(f"\n{i}. Fișierul RO: {issue['ro_file']}")
        print(f"   Fișierul EN: {issue['en_file'] if issue['en_file'] else 'Nu există'}")
        if issue['ro_has_error']:
            print(f"   🔴 GREȘEALĂ în RO")
            if issue['ro_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['ro_links']['ro_link']} → Ar trebui să fie: {issue['correct_ro_link']}")
            if issue['ro_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['ro_links']['en_link']} → Ar trebui să fie: {issue['correct_en_link']}")

        if issue['en_has_error']:
            print(f"   🔴 GREȘEALĂ în EN")
            if issue['en_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['en_links']['ro_link']} → Ar trebui să fie: {issue['correct_ro_link']}")
            if issue['en_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['en_links']['en_link']} → Ar trebui să fie: {issue['correct_en_link']}")

    print("=" * 80)

    # Fix the issues
    print(f"\n🔧 REPARARE AUTOMATĂ A PROBLEMELOR...")
    print("=" * 80)

    fixed_files = fix_issues(issues_found)

    if fixed_files:
        print(f"\n✅ FIȘIERE REPARATE CU SUCCES:")
        for i, fixed_file in enumerate(fixed_files, 1):
            print(f"  {i}. {fixed_file}")
    else:
        print(f"\n❌ Nu s-au putut repara fișierele.")

    print("=" * 80)
else:
    print("✅ Nu s-au găsit probleme regulate în fișiere.")

print("\n🔍 Verificare și reparare finală completată!")