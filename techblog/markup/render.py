#!/usr/bin/env python
import postmarkup
import markuptags
from techblog.markup.fields import PickledObjectField, MarkupField
from techblog import broadcast
from techblog.markup import extendedmarkup
from BeautifulSoup import BeautifulSoup


from markuprender import *

VERSION = 1


def render(markup, markup_type):

    markup = markup or ""

    if markup_type == "postmarkup":

        tag_data = {}
        html = post_render( markup,
                            paragraphs=True,
                            clean=True,
                            tag_data=tag_data )


        text = postmarkup.textilize(html)
        output = tag_data.get('output', {})
        sections = output.get("sections", {})
        for key, value in sections.items():
            sections[key] = [post_markup(s, paragraphs=True, clean=True) for s in value]
        data = output

        summary_markup = output.get("summary", "")
        summary_html = ""
        if summary_markup.strip():
            summary = post_markup(output.get("summary" , ""), paragraphs=True, clean=True)
            summary_html = summary

    elif markup_type == "emarkup":

        sections = extendedmarkup.parse(markup)

        html = extendedmarkup.chunks_to_html(sections['main'])
        summary_html = html
        text = postmarkup.textilize(html)
        data = dict(sections = sections)


    elif markup_type == "comment_bbcode":

        html = postmarkup.render_bbcode(markup, paragraphs=True, clean=True)
        text = postmarkup.textilize(html)
        return html, html, text, {}

    elif markup_type == "comment_wordpress":

        html = markup
        summary_html = html
        text = postmarkup.textilize(html)
        data = {}

    elif markup_type == "text":

        html = "<p>%s</p>" % postmarkup._escape(markup)
        summary_html = html
        text = postmarkup.textilize(markup)
        data = {}

    else:

        html = markup
        summary_html = html
        text = postmarkup.textilize(html)
        data = {}

    more_i = html.find('<!--more-->')
    if more_i == -1:
        more_i = html.find('<!-- more -->')

    if more_i != -1:
        summary_html = html[:more_i]
        summary_html = unicode(BeautifulSoup(summary_html))

    return html, summary_html, text, data


@broadcast.recieve()
def render_comment(markup, markup_type):

    return render(markup, markup_type)
