from markdown_it import MarkdownIt
from mdit_py_plugins.texmath import texmath_plugin

md = MarkdownIt().use(texmath_plugin, delimiters='dollars')
print("--- Result 1 ($$x=1$$) ---")
print(md.render("$$x=1$$"))

print("--- Result 2 ($x=1$) ---")
print(md.render("$x=1$"))

content = """
# Test
$$
y = mx + c
$$
"""
print("--- Result 3 (Block) ---")
print(md.render(content))
