import os, re

files = sorted(f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('__'))
for f in files:
    content = open(f).read()
    # Match down_revision with optional type annotation
    m = re.search(r'down_revision(?:\s*:\s*[^=]+)?\s*=\s*([^\n]+)', content)
    if m:
        val = m.group(1).strip()
        # Extract string value from quotes
        quote_match = re.search(r"['\"]([^'\"]*)['\"]", val)
        if quote_match:
            val = quote_match.group(1)
        print(f'{f}: {val}')
    else:
        print(f'{f}: None')