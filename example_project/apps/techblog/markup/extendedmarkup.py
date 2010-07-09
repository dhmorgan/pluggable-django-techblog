#!/usr/bin/env python

#!/usr/bin/env python

import postmarkup

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.template.loader import get_template, select_template
from django.template.context import Context

import re
from collections import defaultdict

import xml.etree.ElementTree as ET

postmarkup_renderer = postmarkup.create()

class ExtendedMarkupError(Exception):
    pass

class Chunk(object):

    def __init__(self, text, chunk_type='text'):
        self.text = text
        self.chunk_type = chunk_type
        #self.vars = defaultdict(lambda: None)
        self.vars = {}

    def __str__(self):
        return "%s: %s, %s" % (self.chunk_type, repr(self.text), repr(self.vars))

    def __iter__(self):
        return iter(self.text)

    def __nonzero__(self):
        return any(l.strip() for l in self.text)

    def __cmp__(self, other):
        def priority(s):
            try:
                return int(s)
            except:
                return s
        return cmp( self.get_priority(), other.get_priority() )

    def get_priority(self):
        try:
            return int(self.vars.get('priority', '100'))
        except:
            return 100

    __repr__ = __str__

class SectionsDictionary(dict):

    def __init__(self, *args, **kwargs):
        self.vars = {}
        dict.__init__(self, *args, **kwargs)

class Section(list):

    def __init__(self, name, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.vars = {}
        self.name = name

    def __str__(self):
        return "%s, %s" % ( repr(list(self)), self.vars )

    __repr__ = __str__


class EMarkupParser(object):


    re_extended_directive = re.compile(r"^\{(.+)\}(.*?)$")

    def __init__(self, renderer=None):
        if renderer is None:
            self.renderer = postmarkup.create()

    def parse(self, text, default_section = "main", default_chunk_type = "paragraph"):


        self._current_section = ""
        self._default_section = default_section
        self._current_chunk_type = ""
        self._default_chunk_type = default_chunk_type

        self.sections = SectionsDictionary()
        sections = self.sections

        self._chunks = []
        chunks = self._chunks

        self.current_lines = []
        current_lines = self.current_lines

        new_chunk = True

        vars = self.sections.vars

        self._section_vars = {}
        self._chunk_vars = {}

        comment_mode = 0

        def make_chunk():
            #if current_lines:
            chunk = current_lines[:]
            chunk = Chunk(chunk, self._current_chunk_type.strip() or self._default_chunk_type)
            chunk.vars.update(self._chunk_vars)
            self._chunk_vars.clear()
            chunks.append(chunk)
            del current_lines[:]


        def process_vars(vars, line):
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                vars[key] = value
                return True
            elif line.endswith('!'):
                vars[line[:-1].strip()] = '1'
                return True
            return False

        lines = [line.rstrip() for line in text.replace('\r', '').split('\n')]
        for line_no, line in enumerate(lines):

            if not line:
                current_lines.append("");
                new_chunk = True
                continue

            if new_chunk:

                if comment_mode:
                    continue

                if line.startswith(';//'):
                    continue

                m = self.re_extended_directive.match(line)
                if m:
                    line = m.group(1)
                    line_content = m.group(2).strip()
                    #line = line[1:]

                    if self.re_extended_directive.match(line):
                        current_lines.append(line)
                        continue

                    # Chunk type
                    if line.startswith('..'):
                        line = line[2:]
                        if not process_vars(self._chunk_vars, line):
                            chunk_type = self._current_chunk_type
                            make_chunk()
                            if line_content:
                                current_lines.append(line_content)
                                self._current_chunk_type = line or default_chunk_type
                                make_chunk()
                                self._current_chunk_type = chunk_type
                            else:
                                self._current_chunk_type = line or default_chunk_type
                        continue

                    # Section
                    elif line.startswith('.'):
                        line = line[1:]
                        if not process_vars(self._section_vars, line):
                            make_chunk()
                            section_name = line or default_section
                            self.set_section(section_name)
                        continue

                    else:
                        process_vars(sections.vars, line)
                        continue

                else:
                    current_lines.append(line.rstrip())
                    continue

                new_chunk = False

            current_lines.append(line.rstrip())
            new_chunk = False

        make_chunk()
        self.set_section(None)

        return sections

    __call__ = parse

    def set_section(self, section_name):

        current_section = self._current_section or self._default_section
        section = self.sections.setdefault(current_section, Section(current_section))

        section.vars.update(self._section_vars)
        section += self._chunks
        del self._chunks[:]

        self._current_section = section_name or self._default_section
        self._current_chunk_type = self._default_chunk_type

        self._section_vars = {}


def parse(markup, sections=None):

    parser = EMarkupParser()
    parser.parse(markup)
    sections = parser.sections

    rendered_sections = SectionsDictionary()

    error_template = select_template(['markupchunks/error.html'])

    rendered_sections.vars.update(sections.vars)

    for section, chunks in sections.iteritems():

        content_chunks = Section(chunks.name)
        content_chunks.vars.update(chunks.vars)

        for chunk in chunks:

            chunk_filename = "markupchunks/%s.html" % chunk.chunk_type.encode()
            chunk_template = select_template([chunk_filename, "markupchunks/paragraph.html"])

            chunk_data = dict(vars=vars, chunk=chunk, content="\n".join(chunk))
            try:
                chunk_html = chunk_template.render(Context(chunk_data))
            except Exception, e:
                error = str(e)
                chunk_html = unicode(error_template.render(Context(dict(error=error))))

            new_chunk = Chunk(chunk_html, chunk.chunk_type)
            new_chunk.vars.update(chunk.vars)
            content_chunks.append(new_chunk)

        rendered_sections[section] = content_chunks


    return rendered_sections

def process(sections, context_data):

    if sections is None:
        return sections

    error_template = select_template(['blog/modules/error.html'])

    for section, chunks in sections.iteritems():

        for chunk in chunks:
            module = chunk.vars.get('module')

            if module is not None:

                module_template = select_template(["blog/modules/%s.html"%module])

                td = {}
                td.update(context_data)

                td.update( dict(  vars = chunk.vars,
                                  content = chunk.text ) )

                try:
                    chunk_html = module_template.render(Context(td))
                except Exception, e:
                    error = str(e)
                    chunk_html = unicode(error_template.render(Context(dict(error=error))))

                chunk.text = chunk_html

    return sections

def chunks_to_html(chunks):
    return "\n".join( chunk.text for chunk in sorted(chunks, key=lambda chunk:chunk.vars.get('priority', 100), reverse=True) )

def combine_sections(*sections_list):

    combined = SectionsDictionary()
    for sections in filter(None, sections_list):

        combined.vars.update(sections.vars)

        for name_section in sections.iteritems():
            if name_section is None:
                continue

            section_name, section = name_section

            if section_name not in combined:
                new_section = Section(section_name)
                combined[section_name] = new_section

            if hasattr(section, 'vars') and 'replace' in section.vars:
                combined[section_name] = Section(section_name)

            combined[section_name] += section

    return combined


def serialize_xml(sections):

    root = ET.Element("extendedmarkup")

    sections_el = ET.SubElement(root, 'sections')

    for key, value in sections.vars.iteritems():
        var_el = ET.SubElement(root, 'var', name=key, value=value)

    for name, section in sections.iteritems():

        section_el = ET.SubElement(sections_el, 'section', name=name)

        for key, value in section.vars.iteritems():
            var_el = ET.SubElement(section_el, 'var', name=key, value=value)

        for chunk in section:
            chunk_el = ET.SubElement(section_el, 'chunk', type=chunk.chunk_type)
            chunk_el.text = chunk.text

            for key, value in chunk.vars.iteritems():
                var_el = ET.SubElement(chunk_el, 'var', name=key, value=value or u"")

    return ET.tostring(root)



if __name__ == "__main__":
    test = """{hello=world}

{.title}
This is the title

{.body}
{.template=test.html}
{..bold!}

This is in the body

This is also in the body

{..pullquote}
{..location=left}

This is in a pullquote

This is also in a pullquote


"""




    #emarkup = EMarkupParser()
    #sections = emarkup(test)

    import os
    import sys
    sys.path.append("/home/will/projects/djangotechblog")
    os.environ["DJANGO_SETTINGS_MODULE"] = "techblog.settings"


    test1 = """
{doc_level_var!}
{.body}
{.test=1}
Hello, World
{..quote}
{..chunkvar!}
A second chunk type

{.footer}
This is the footer
"""

    test2 = """
{.body}
{.replace=True}
Second body text
"""

    sections1 = parse(test1)
    sections2 = parse(test2)

    xml = serialize_xml(sections1)
    print xml
    open("sections.xml", "w").write(xml)


    #print chunks_to_html(combine_sections(sections1, sections2)['body'])


    #print combined['body']

    print
    print

    #sections = parse(test)
    #
    #import pprint
    ##pprint.pprint(sections)
    #
    #for section, html in sections.iteritems():
    #    print "<h1>%s</h1>" % section
    #    print html
    #pprint.pprint(sections)
    ##pprint.pprint(emarkup.vars)
