import json
from markdown_it import MarkdownIt
from mdit_py_plugins.container import container_plugin

def render_stamp(self_md, tokens, idx, options, env):
    token = tokens[idx]
    if token.nesting == 1:
        info = token.info.strip()[5:].strip()
        blend = "multiply" if "normal" not in info else "normal"
        style = f'style="{info.replace("normal","")}"' if info else ""
        return f'<div class="stamp {blend}" {style}>'
    return '</div>'

md = MarkdownIt('commonmark')
md.use(container_plugin, name="stamp", render=render_stamp)

test_md = """::: stamp right:10mm; transform: rotate(5deg);
![a](C:\\Users\\T03000\\Desktop\\rect1.png)
:::"""

print(md.render(test_md))
