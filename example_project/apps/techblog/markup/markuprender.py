#!/usr/bin/env python

#!/usr/bin/env python
import postmarkup
import markuptags

post_render = postmarkup.create(exlude=["url", "link"], annotate_links=False, auto_url=False)
#post_render.add_tag(postmarkup.SectionTag, "in")


# Auto register markup tags...
for symbol in dir(markuptags):
    if symbol.startswith('__'):
        continue

    if symbol.endswith('Tag'):
        obj = getattr(markuptags, symbol)
        default_name = getattr(obj, 'DEFAULT_NAME', '')
        if default_name:
            post_render.add_tag(obj, default_name)

if __name__ == "__main__":

    test = """[summary]
This is a [b]summary[/b]...[/summary]
Article [py]import postmarkup
print postmarkup.__version__[/py]
[eval safe]range(10)[/eval]
[py]x=1[/py]
X is [eval]x[/eval], [py]import datetime[/py][eval]datetime.datetime.now()[/eval]

[py]import this[/py]
Another paragraph"""

    tag_data = {}
    html = post_render(test, paragraphs=True, clean=True, tag_data=tag_data)
    print html
    from pprint import pprint
    pprint(tag_data)