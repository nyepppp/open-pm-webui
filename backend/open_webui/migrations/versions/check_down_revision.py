content = open('f2e3d4c5b6a7_add_pm_tables.py').read()
print('down_revision' in content)
for i, line in enumerate(content.split('\n')):
    if 'down_revision' in line:
        print(f'Line {i+1}: {line}')