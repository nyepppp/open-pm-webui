import re
content = open('f2e3d4c5b6a7_add_pm_tables.py').read()
pattern = r'down_revision\s*=\s*([^\n]+)'
print('Pattern:', pattern)
print('Content has down_revision:', 'down_revision' in content)

# Check each line
for i, line in enumerate(content.split('\n')):
    if 'down_revision' in line:
        print(f'Line {i+1}: {repr(line)}')
        m = re.search(pattern, line)
        print('  Match on line:', m.group(1) if m else 'None')

m = re.search(pattern, content)
print('Match in full content:', m.group(1) if m else 'None')