content = open('+page.svelte').read()
lines = content.split('\n')
for i in range(1880, 1912):
    print(f'{i+1}: {lines[i]}')