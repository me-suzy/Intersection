import os
import re
from collections import defaultdict

# Define directories
base_dir = r'e:\Carte\BB\17 - Site Leadership\Principal 2022'
ro_dir = os.path.join(base_dir, 'ro')
en_dir = os.path.join(base_dir, 'en')

# Function to extract canonical from HTML content
def extract_canonical(content):
    match = re.search(r'<link rel="canonical" href="https://neculaifantanaru\.com/(en/)?([^"]+)" />', content)
    if match:
        return (match.group(1) or '') + match.group(2)
    return None

# Function to extract flags section
def extract_flags(content):
    flags_start = content.find('<!-- FLAGS_1 -->')
    flags_end = content.find('<!-- FLAGS -->', flags_start)
    if flags_start != -1 and flags_end != -1:
        return content[flags_start:flags_end + len('<!-- FLAGS -->')]
    return None

# Function to replace canonical in content
def replace_canonical(content, new_href):
    return re.sub(r'<link rel="canonical" href="[^"]+" />', f'<link rel="canonical" href="{new_href}" />', content)

# Function to replace specific flag link in flags (improved regex for \+1 and +1)
def replace_flag_link(flags, code, new_href):
    # Handle both \+1 and +1, \+40 and +40
    if code == r'\+1':
        pattern = r'<li><a cunt_code="(\\?\+1)" href="[^"]+">'
    elif code == r'\+40':
        pattern = r'<li><a cunt_code="(\\?\+40)" href="[^"]+">'
    else:
        pattern = rf'<li><a cunt_code="{code}" href="[^"]+">'

    replacement = f'<li><a cunt_code="{code.replace(chr(92), "")}" href="{new_href}">'  # Remove backslash from output
    return re.sub(pattern, replacement, flags, count=1)

# Function to update file
def update_file(file_path, new_content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

# Function to extract flag link (improved to handle \+1 and +1)
def extract_flag_link(flags, code):
    if code == '+1':
        match = re.search(r'<li><a cunt_code="(\\?\+1)" href="([^"]+)"', flags)
    elif code == '+40':
        match = re.search(r'<li><a cunt_code="(\\?\+40)" href="([^"]+)"', flags)
    else:
        match = re.search(rf'<li><a cunt_code="{code}" href="([^"]+)"', flags)
    return match.group(2) if match else None

# Function to fix double .html.html
def fix_double_html(url):
    return url.replace('.html.html', '.html')

# Function to check if two filenames are similar (potential pair)
def are_similar_filenames(ro_name, en_name):
    ro_base = ro_name[:-5].lower()  # remove .html
    en_base = en_name[:-5].lower()  # remove .html

    # Direct match
    if ro_base == en_base:
        return True

    # Common patterns: replace dashes with spaces and check
    ro_words = ro_base.replace('-', ' ').split()
    en_words = en_base.replace('-', ' ').split()

    # At least 50% of words match or similar length and structure
    if len(ro_words) >= 3 and len(en_words) >= 3:
        # Check for semantic similarity (simplified)
        if (len(ro_words) == len(en_words) and
            len(ro_base.replace('-', '')) > 20 and
            len(en_base.replace('-', '')) > 20):
            return True

    return False

# PASUL 1: Canonical = Numele fișierului
print('================================================================================')
print('PASUL 1: CANONICAL = NUMELE FIȘIERULUI')
print('============================================================')

canonical_fixed_ro = 0
canonical_fixed_en = 0

# Process RO files
ro_files = [f for f in os.listdir(ro_dir) if f.endswith('.html')]
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    expected_canonical = filename[:-5]  # without .html, case-sensitive
    expected_href = f'https://neculaifantanaru.com/{expected_canonical}.html'
    if canonical != expected_canonical + '.html':
        new_content = replace_canonical(content, expected_href)
        update_file(file_path, new_content)
        canonical_fixed_ro += 1
        print(f'Corectat RO: {filename} canonical → {expected_canonical}.html')

# Process EN files
en_files = [f for f in os.listdir(en_dir) if f.endswith('.html')]
for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    expected_canonical = f'en/{filename[:-5]}.html'  # en/ + name without .html
    expected_href = f'https://neculaifantanaru.com/{expected_canonical}'
    if canonical != expected_canonical:
        new_content = replace_canonical(content, expected_href)
        update_file(file_path, new_content)
        canonical_fixed_en += 1
        print(f'Corectat EN: {filename} canonical → {expected_canonical}')

print(f'✅ Canonical-uri reparate: RO={canonical_fixed_ro}, EN={canonical_fixed_en}, TOTAL={canonical_fixed_ro + canonical_fixed_en}')

# PASUL 2: FLAGS = Canonical (în același fișier)
print('\nPASUL 2: FLAGS = CANONICAL (în același fișier)')
print('============================================================')

flags_fixed_ro = 0
flags_fixed_en = 0

# Process RO files for own flag (+40)
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    flags = extract_flags(content)
    if flags and canonical:
        current_link = extract_flag_link(flags, '+40')
        expected_href = f'https://neculaifantanaru.com/{filename[:-5]}.html'
        if current_link and current_link != expected_href:
            new_flags = replace_flag_link(flags, r'\+40', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            flags_fixed_ro += 1
            print(f'Corectat RO flags own: {filename} → {expected_href}')

# Process EN files for own flag (+1)
for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    flags = extract_flags(content)
    if flags and canonical:
        current_link = extract_flag_link(flags, '+1')
        expected_href = f'https://neculaifantanaru.com/en/{filename[:-5]}.html'
        if current_link:
            # Fix double .html.html
            fixed_link = fix_double_html(current_link)
            if fixed_link != expected_href:
                new_flags = replace_flag_link(flags, r'\+1', expected_href)
                new_content = content.replace(flags, new_flags)
                update_file(file_path, new_content)
                flags_fixed_en += 1
                if '.html.html' in current_link:
                    print(f'Corectat EN flags own (dublu .html): {filename} → {expected_href}')
                else:
                    print(f'Corectat EN flags own: {filename} → {expected_href}')

print(f'✅ FLAGS reparate: RO={flags_fixed_ro}, EN={flags_fixed_en}, TOTAL={flags_fixed_ro + flags_fixed_en}')

# PASUL 3: SINCRONIZARE CROSS-REFERENCES RO ↔ EN
print('\nPASUL 3: SINCRONIZARE CROSS-REFERENCES RO ↔ EN')
print('============================================================')

# Build file sets for validation
ro_files_set = set(ro_files)
en_files_set = set(en_files)

# Build mappings (strict validation)
ro_to_en_map = {}
en_to_ro_map = {}
invalid_links = []

# First pass: Try to match based on existing flags (strict validation)
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        en_link = extract_flag_link(flags, '+1')
        if en_link:
            # Extract filename from URL
            en_match = re.search(r'https://neculaifantanaru\.com/en/([^"]+)\.html', en_link)
            if en_match:
                en_name = en_match.group(1) + '.html'
                # Check if EN file actually exists
                if en_name in en_files_set:
                    ro_to_en_map[filename] = en_name
                else:
                    invalid_links.append(f"RO {filename}: link către EN inexistent {en_name}")

for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        ro_link = extract_flag_link(flags, '+40')
        if ro_link:
            # Extract filename from URL
            ro_match = re.search(r'https://neculaifantanaru\.com/([^"]+)\.html', ro_link)
            if ro_match:
                ro_name = ro_match.group(1) + '.html'
                # Check if RO file actually exists
                if ro_name in ro_files_set:
                    en_to_ro_map[filename] = ro_name
                else:
                    invalid_links.append(f"EN {filename}: link către RO inexistent {ro_name}")

# Find bidirectional matches
bidirectional_pairs = []
for ro_file, en_file in ro_to_en_map.items():
    if en_file in en_to_ro_map and en_to_ro_map[en_file] == ro_file:
        bidirectional_pairs.append((ro_file, en_file))

# Find files with NO COMMON LINKS (all 4 links different)
orphaned_files = []
mismatched_pairs = []

for ro_file in ro_files:
    if ro_file not in [pair[0] for pair in bidirectional_pairs]:
        # Get RO's EN link and EN's RO link
        ro_file_path = os.path.join(ro_dir, ro_file)
        with open(ro_file_path, 'r', encoding='utf-8') as f:
            ro_content = f.read()
        ro_flags = extract_flags(ro_content)
        ro_en_link = extract_flag_link(ro_flags, '+1') if ro_flags else None

        if ro_en_link:
            en_match = re.search(r'https://neculaifantanaru\.com/en/([^"]+)\.html', ro_en_link)
            if en_match:
                potential_en = en_match.group(1) + '.html'

                # Check if this EN exists and what it points back to
                if potential_en in en_files_set:
                    en_file_path = os.path.join(en_dir, potential_en)
                    with open(en_file_path, 'r', encoding='utf-8') as f:
                        en_content = f.read()
                    en_flags = extract_flags(en_content)
                    en_ro_link = extract_flag_link(en_flags, '+40') if en_flags else None

                    if en_ro_link:
                        ro_match = re.search(r'https://neculaifantanaru\.com/([^"]+)\.html', en_ro_link)
                        if ro_match:
                            pointed_ro = ro_match.group(1) + '.html'

                            # Check if all 4 links are different (no common links)
                            if pointed_ro != ro_file:
                                # Find potential similar filenames
                                potential_pairs = []
                                for en_f in en_files:
                                    if are_similar_filenames(ro_file, en_f):
                                        potential_pairs.append(en_f)

                                if potential_pairs:
                                    mismatched_pairs.append((ro_file, potential_pairs[0],
                                                           f"RO→EN: {ro_en_link}, EN→RO: {en_ro_link}"))
                                else:
                                    orphaned_files.append(f"RO {ro_file}: fără pereche validă")

# Fallback: Match by filename similarity (case-insensitive) for remaining files
unmatched_ro = [f for f in ro_files if f not in [pair[0] for pair in bidirectional_pairs]
                and f not in [pair[0] for pair in mismatched_pairs]]
unmatched_en = [f for f in en_files if f not in [pair[1] for pair in bidirectional_pairs]
                and f not in [pair[1] for pair in mismatched_pairs]]

similarity_pairs = []
for ro_filename in unmatched_ro:
    ro_base = ro_filename[:-5].lower()
    for en_filename in unmatched_en:
        en_base = en_filename[:-5].lower()
        if (ro_base == en_base or ro_base.replace('-', ' ') == en_base.replace('-', ' ') or
            are_similar_filenames(ro_filename, en_filename)):
            if en_filename not in [pair[1] for pair in similarity_pairs]:
                similarity_pairs.append((ro_filename, en_filename))
                break

all_pairs = bidirectional_pairs + similarity_pairs + [(pair[0], pair[1]) for pair in mismatched_pairs]

print(f'Găsite {len(bidirectional_pairs)} perechi bidirectionale, {len(similarity_pairs)} perechi prin similaritate și {len(mismatched_pairs)} perechi cu link-uri diferite')

# Report mismatched pairs (no common links)
if mismatched_pairs:
    print('\n🚨 PERECHI CU TOATE LINK-URILE DIFERITE (FĂRĂ PUNCTE COMUNE):')
    for ro_f, en_f, details in mismatched_pairs:
        print(f'  {ro_f} ↔ {en_f}: {details}')

# Correct cross-references
cross_fixed = 0

for ro_filename, en_filename in all_pairs:
    # Correct RO file: set +1 to mapped EN
    file_path = os.path.join(ro_dir, ro_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        current_link = extract_flag_link(flags, '+1')
        expected_href = f'https://neculaifantanaru.com/en/{en_filename[:-5]}.html'
        if current_link != expected_href:
            new_flags = replace_flag_link(flags, r'\+1', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            cross_fixed += 1
            print(f'Corectat RO {ro_filename}: EN link → {en_filename}')

    # Correct EN file: set +40 to mapped RO
    file_path = os.path.join(en_dir, en_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        current_link = extract_flag_link(flags, '+40')
        expected_href = f'https://neculaifantanaru.com/{ro_filename[:-5]}.html'
        if current_link != expected_href:
            new_flags = replace_flag_link(flags, r'\+40', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            cross_fixed += 1
            print(f'Corectat EN {en_filename}: RO link → {ro_filename}')

print(f'✅ Cross-references reparate: {cross_fixed}')

# Report invalid links and orphaned files
print('\n🚨 FIȘIERE CU PROBLEME:')
print('============================================================')

if invalid_links:
    print('Link-uri către fișiere inexistente:')
    for link in invalid_links:
        print(f'  {link}')

final_unmatched_ro = [f for f in ro_files if f not in [pair[0] for pair in all_pairs]]
final_unmatched_en = [f for f in en_files if f not in [pair[1] for pair in all_pairs]]

if final_unmatched_ro or final_unmatched_en:
    print('\nFișiere fără perechi valide:')
    for ro_file in final_unmatched_ro:
        print(f'  RO {ro_file}: fără pereche EN validă')
    for en_file in final_unmatched_en:
        print(f'  EN {en_file}: fără pereche RO validă')

if not invalid_links and not final_unmatched_ro and not final_unmatched_en:
    print('✅ Toate fișierele au perechi valide!')

# Final results
print('\n================================================================================')
print('REZULTATE FINALE')
print('================================================================================')
print(f'Pasul 1 - Canonical-uri reparate: {canonical_fixed_ro + canonical_fixed_en}')
print(f'Pasul 2 - FLAGS → canonical: {flags_fixed_ro + flags_fixed_en}')
print(f'Pasul 3 - Cross-references: {cross_fixed}')
print(f'🎉 TOTAL: {canonical_fixed_ro + canonical_fixed_en + flags_fixed_ro + flags_fixed_en + cross_fixed}')