#!/usr/bin/env python

import postmarkup

import sys
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class PyTag(postmarkup.TagBase):

    DEFAULT_NAME = "py"

    def __init__(self, name, **kwargs):
        postmarkup.TagBase.__init__(self, name, enclosed=True, inline=True, strip_first_newline=True)

    def render_open(self, parser, node_index):

        tag_data = parser.tag_data
        globals = tag_data.setdefault("EvalTag.globals", {})
        locals = tag_data.setdefault("EvalTag.locals", {})

        contents = self.get_contents(parser).strip()
        self.skip_contents(parser)

        stdout = sys.stdout
        contents = "\n".join(contents.split('\r\n')) + "\n"

        sys.stdout = StringIO()

        try:
            try:
                try:
                    exec contents in globals, locals
                except Exception, e:
                    result = str(e)
            except:
                result = ""
        finally:
            result = sys.stdout.getvalue()
            sys.stdout = stdout

        if not self.params.lower() == "safe":
            result = postmarkup._escape(result)

        return result.rstrip()


class EvalTag(postmarkup.TagBase):

    DEFAULT_NAME = "eval"

    def __init__(self, name, **kwargs):
        postmarkup.TagBase.__init__(self, name, inline=True, enclosed=True, strip_first_newline=True)

    def render_open(self, parser, node_index):

        tag_data = parser.tag_data
        globals = tag_data.setdefault("EvalTag.globals", {})
        locals = tag_data.setdefault("EvalTag.locals", {})

        contents = self.get_contents(parser).strip()
        self.skip_contents(parser)

        try:
            result = str(eval(contents, globals, locals))
        except Exception, e:
            try:
                result = str(e)
            except:
                result = "(Error in eval tag)"

        if not self.params.lower() == "safe":
            result = postmarkup._escape(result)

        return result.rstrip()

class InlineCodeTag(postmarkup.TagBase):

    DEFAULT_NAME = "c"

    def __init__(self, name, **kwargs):
        postmarkup.TagBase.__init__(self, name, inline=True, enclosed=True)

    def render_open(self, parser, node_index):
        contents = postmarkup._escape_no_breaks(self.get_contents(parser))
        self.skip_contents(parser)
        return u"<code>%s</code>"%contents

#class PostLinkTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "url"
#
#    _safe_chars = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
#               'abcdefghijklmnopqrstuvwxyz'
#               '0123456789'
#               '_.-=/&?:%&')
#
#    _re_domain = re.compile(r"//([a-z0-9-\.]*)", re.UNICODE)
#
#    def __init__(self, name, annotate_links=False, **kwargs):
#        postmarkup.TagBase.__init__(self, name, inline=True)
#
#        self.annotate_links = annotate_links
#
#
#    def render_open(self, parser, node_index):
#
#        self.domain = u''
#        tag_data = parser.tag_data
#        nest_level = tag_data['link_nest_level'] = tag_data.setdefault('link_nest_level', 0) + 1
#
#        if nest_level > 1:
#            return u""
#
#        if self.params:
#            url = self.params.strip()
#        else:
#            url = self.get_contents_text(parser).strip()
#            url = _unescape(url)
#
#        if ':' in self.params:
#            return u'<a href="%s" class="external-link">'%url
#        else:
#            return u'<a href="%s">'%url
#
#
#
#    def render_close(self, parser, node_index):
#
#        tag_data = parser.tag_data
#        tag_data['link_nest_level'] -= 1
#
#        if tag_data['link_nest_level'] > 0:
#            return u''
#
#        if self.domain:
#            return u'</a>'+self.annotate_link(self.domain)
#        else:
#            return u''
#
#    def annotate_link(self, domain=None):
#
#        if domain and self.annotate_links:
#            return annotate_link(domain)
#        else:
#            return u""


class PostLinkTag(postmarkup.TagBase):

    DEFAULT_NAME = "url"

    def __init__(self, name, **kwargs):
        super(PostLinkTag, self).__init__(name, annotate_links=False, inline=True, **kwargs)

    def render_open(self, parser, node_index):

        tag_data = parser.tag_data
        nest_level = tag_data['link_nest_level'] = tag_data.setdefault('link_nest_level', 0) + 1

        if nest_level > 1:
            return u''

        external_link = ':' in self.params

        if external_link:
            domain = postmarkup.LinkTag._re_domain.search(self.params.lower()).group(1)
            return u'<a href="%s" class="external-link" title="%s">' % (self.params, domain)
        else:
            return u'<a href="%s">' % (self.params)

    def render_close(self, parser, node_index):

        tag_data = parser.tag_data
        tag_data['link_nest_level'] -= 1

        if tag_data['link_nest_level'] > 0:
            return u''

        return u'</a>'



class MoreTag(postmarkup.TagBase):

    DEFAULT_NAME = "more"

    def __init__(self, name, **kwargs):
        super(MoreTag, self).__init__(name, auto_close=True, **kwargs)

    def render_open(self, parser, node_index):
        return u"<!-- more -->"


def OffsettedHeaderTag(level, offset):

    class HTag(postmarkup.TagBase):

        """A simple tag that is replaces with a div and a style."""

        DEFAULT_NAME = "h" + str(level)

        def render_open(self, parser, node_index):
            return u'<%s>' % self.DEFAULT_NAME

        def render_close(self, parser, node_index):
            return u'</%s>' % self.DEFAULT_NAME

    return HTag

H1Tag = OffsettedHeaderTag(1, 2)
H2Tag = OffsettedHeaderTag(2, 2)
H3Tag = OffsettedHeaderTag(3, 2)


#
#class HTMLTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "html"
#
#    def __init__(self, name, **kwargs):
#        postmarkup.TagBase.__init__(self, name, enclosed=True, strip_first_newline=True)
#
#
#    def render_open(self, parser, node_index):
#        contents = self.get_contents(parser).strip()
#        self.skip_contents(parser)
#        return contents
#
#class SummaryTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "summary"
#
#    def __init__(self, name, **kwargs):
#        postmarkup.TagBase.__init__(self, name, inline=True)
#
#    def render_close(self, parser, node_index):
#        contents = self.get_contents(parser).strip()
#        tag_data = parser.tag_data
#        summary = tag_data["output"].setdefault("summary", "")
#        tag_data["output"]["summary"] = contents
#        return u""
#
#class AnchorTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "anchor"
#
#    def __init__(self, name, **kwargs):
#        postmarkup.TagBase.__init__(self, name, autoclose=True, inline=True)
#
#    def render_open(self, parser, node_index):
#        anchor_name = self.params.lower().replace(' ', '_')
#        return u"""<a name="%s" />""" % anchor_name
#
#class PullquoteTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "pullquote"
#
#    def __init__(self, name, **kwargs):
#        postmarkup.TagBase.__init__(self, name, inline=False)
#
#    def render_open(self, parser, node_index):
#        contents = self.get_contents(parser).strip()
#        self.skip_contents(parser)
#        txt = postmarkup._escape(contents)
#        html = u"""<div class="pullquote">"%s"</div>""" % txt
#        return html
#
#class PulloutTag(postmarkup.TagBase):
#
#    DEFAULT_NAME = "pullout"
#
#    def __init__(self, name, **kwargs):
#        postmarkup.TagBase.__init__(self, name, inline=False)
#
#    def render_open(self, parser, node_index):
#        left = self.params.lower() != 'right'
#        if left:
#            return """<div class="pullout-left">"""
#        else:
#            return """<div class="pullout-right">"""
#
#    def render_close(self, parser, node_index):
#        return """</div>"""
