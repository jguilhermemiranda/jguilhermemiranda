from pathlib import Path
import re
for base in [Path(r'C:\Users\joaog\Documents\pagina do github\assets\glitch\pt'), Path(r'C:\Users\joaog\Documents\pagina do github\assets\glitch\en')]:
    for p in base.rglob('*.svg'):
        s = p.read_text(encoding='utf-8')
        s = s.replace('fill="#C4B5FD"', 'fill="#C4B5FD" stroke="#C4B5FD" stroke-width="0.7" paint-order="stroke"')
        s = s.replace('fill="#8B5CF6" opacity=".8"', 'fill="#8B5CF6" opacity=".8" stroke="#8B5CF6" stroke-width="0.7" paint-order="stroke"')
        def add_typewriter(m):
            tag = m.group(1)
            inner = m.group(2)
            end = m.group(3)
            if '<animate' in tag:
                return m.group(0)
            return f'{tag}\n<animate attributeName="stroke-dasharray" values="0 2000;2000 0;2000 0" dur="1.2s" repeatCount="indefinite"/>\n<animate attributeName="fill-opacity" values="0;1;1;1" dur="1.2s" repeatCount="indefinite"/>\n{inner}{end}'
        s = re.sub(r'(<text\s+[^>]*>)(.*?)(</text>)', add_typewriter, s, flags=re.S)
        p.write_text(s, encoding='utf-8')
print('updated')
