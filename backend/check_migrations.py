import os
import sys
sys.path.insert(0, os.getcwd())

# Get all migration files
versions_dir = 'open_webui/migrations/versions'
files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]

# Read each file and find down_revision
migrations = {}
for f in sorted(files):
    with open(os.path.join(versions_dir, f), 'r') as file:
        content = file.read()
        for line in content.split('\n'):
            if 'down_revision' in line and '=' in line:
                rev = line.split('=')[1].strip().strip("'")
                if rev and rev != 'None':
                    migrations[f] = rev
                break

print('Migration dependencies:')
for k, v in list(migrations.items())[:10]:
    print(f'  {k} -> {v}')
