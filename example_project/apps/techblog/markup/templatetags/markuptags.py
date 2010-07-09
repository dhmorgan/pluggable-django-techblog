from __future__ import absolute_import

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import re

from pygments import highlight
from pygments.lexers import get_lexer_by_name, ClassNotFound
from pygments.formatters import HtmlFormatter

from techblog.markup.markuprender import post_render


        #try:
        #    lexer = get_lexer_by_name(self.params, stripall=True)
        #except ClassNotFound:
        #    contents = _escape(contents)
        #    return '<div class="code"><pre>%s</pre></div>' % contents
        #
        #formatter = HtmlFormatter(linenos=self.line_numbers, cssclass="code")
        #return highlight(contents, lexer, formatter).strip().replace("\n", "<br/>")

register = template.Library()

from postmarkup import _escape
#from postmarkup import render_bbcode

@register.filter
@stringfilter
def postmarkup(value):
    if not value:
        return u""
    html = mark_safe(post_render(value))
    return html

@register.filter
@stringfilter
def paragraphize(value):
    try:
        v = value.strip().lower()
        if not v:
            return u""
        if not v.startswith("<"):
            return "<p>%s</p>" % value
        return value
    except Exception, e:
        print e

@register.simple_tag
def markupsection(sections, key):

    if not sections:
        return u""
    chunks = sections.get(key)

    if chunks is None:
        return u""

    return mark_safe( u"\n".join(chunk.text for chunk in sorted(chunks, key=lambda chunk:chunk.get_priority(), reverse=True) if chunk )  )

@register.simple_tag
def code(content, language):
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except ClassNotFound:
        content = _escape(content)
        return '<div class="code"><pre>%s</pre></div>' % content

    formatter = HtmlFormatter(linenos=False, cssclass="code")
    highlighted = highlight(content, lexer, formatter).strip()

    return mark_safe( highlighted )

@register.simple_tag
def code_linenumbers(content, language):
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except ClassNotFound:
        content = _escape(content)
        return '<div class="code"><pre>%s</pre></div>' % content

    formatter = HtmlFormatter(linenos=True, cssclass="code")
    return mark_safe( highlight(content, lexer, formatter).strip() )

@register.filter
@stringfilter
def link(link):
    if '|' not in link:
        return link
    text, url = link.split('|', 1)
    text = text.strip()
    url = url.strip()

    return mark_safe('<a href="%s">%s</a>' % (url, text))