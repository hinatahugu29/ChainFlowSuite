import json
from markdown_it import MarkdownIt
from mdit_py_plugins.container import container_plugin
from urllib.parse import unquote

def render_stamp(self_md, tokens, idx, options, env):
    token = tokens[idx]
    if token.nesting == 1:
        info = token.info.strip()[5:].strip()
        blend = "multiply" if "normal" not in info else "normal"
        style = f'style="{info.replace("normal","")}"' if info else ""
        return f'<div class="stamp {blend}" {style}>'
    return '</div>'

def custom_normalize(url):
    # original markdown_it normalizeLink percent-encodes.
    # We can unquote it and replace backslashes if it looks like a Windows path
    url = unquote(url)
    if url.startswith("C:\\") or url.startswith("D:\\"):
         url = "file:///" + url.replace("\\", "/")
    return url

md = MarkdownIt('commonmark')
md.use(container_plugin, name="stamp", render=render_stamp)
md.normalizeLink = custom_normalize
md.validateLink = lambda url: True

test_md = """::: stamp
![a](C:\\Users\\T03000\\Desktop\\rect1.png)
:::"""

print(md.render(test_md))
