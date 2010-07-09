from django.db import models

from techblog import markup
from techblog.markup.fields import MarkupField
from techblog.markup.extendedmarkup import combine_sections
from techblog.markup.render import render

class PageBase(models.Model):

    name = models.CharField("Name", default="", blank=True, max_length=255)
    template = models.CharField("Page template", default="", blank=True, max_length=255)

    def __unicode__(self):
        return self.name

class PublishedPageManager(models.Manager):

    def get_query_set(self):
        return super(PublishedPageManager, self).get_query_set().filter(published=True, version='live')


class Page(models.Model):

    base = models.ForeignKey(PageBase, blank=True, null=True)
    parent = models.ForeignKey("Page", blank=True, null=True)
    path = models.CharField("Page path", max_length=255, blank=True)

    title = models.CharField("Page Title", max_length=100)
    slug = models.SlugField("Slug", max_length=100, db_index=True)

    inherit = models.BooleanField("Inherit parent's content?", default=False)
    created_time = models.DateTimeField(auto_now_add=True)
    edit_time = models.DateTimeField(auto_now=True)
    published = models.BooleanField("Display on site?", default=False)
    promoted = models.BooleanField("Display in children list?", default=True)


    content = MarkupField(default="", blank=True, renderer=render)

    objects = models.Manager()
    published_pages = PublishedPageManager()


    version = models.CharField("Version", max_length=100, default="live")
    version_id = models.IntegerField("Parent Page ID", blank=True, null=True)


    allow_comments = models.BooleanField(default=True)
    show_comments = models.BooleanField(default=True)


    def __unicode__(self):
        if self.version != 'live':
            return "%s (%s)" % (self.path, self.version)
        return self.path

    def get_sections(self):

        visited = set()

        sections_to_combine = []
        page = self
        while page is not None and page.id not in visited:
            visited.add(page.id)
            sections_to_combine.append(page.content_data.get('sections'))
            if not page.inherit:
                break
            page = page.parent

        sections_to_combine = sections_to_combine[::-1]

        if self.base is not None:
            sections_to_combine.append(self.base.content_data.get('sections'))

        sections = combine_sections( *sections_to_combine )

        return sections

    def get_template_names(self):

        templates = ["page/page.html"]
        if self.base and self.base.template:
            templates.insert(0, self.base.template)

        return templates

    @models.permalink
    def get_absolute_url(self):

        return ("page", (self.path,))

    def save(self, *args, **kwargs):
        self.create_path()
        return super(Page, self).save(*args, **kwargs)

    def create_path(self):

        pages_checked = set()
        page = self
        page_components = []

        while page is not None and page.id not in pages_checked:
            page_components.append(page.slug)
            pages_checked.add(page.id)
            page = page.parent

        path = "/".join(page_components[::-1])
        self.path = path


    @classmethod
    def page_from_path(cls, path):

        components = path.split('/')

        page = None
        for component in components:
            try:
                page = Page.objects.get(slug=component, parent=page, published=True, version='live')
            except Page.DoesNotExist:
                return None
        return page

    def get_children(self):

        children = Page.published_pages.all()
        return children

    def get_promoted_children(self):

        children = self.get_children().filter(promoted=True)
        return children



    def get_parent_version(self):

        if self.version_id is None:
            return self
        parent_page = Page.objects.get(self.version_id)
        return parent_page


    def get_version(self, version):

        """ Retrieve a versioned page. """

        if self.version == version:
            return self

        parent_version_id = self.get_parent_version().id

        try:
            versioned_page = Page.objects.get(version_id=parent_version_id, version=version)
            return versioned_page
        except Page.DoesNotExist:
            versioned_page = Page(version_id=parent_version_id, published=False, version=version)
            versioned_page.save()

        copy_attribs = ['parent',
                        'path',
                        'title',
                        'slug',
                        'inherit',
                        'created_time',
                        'edit_time',
                        'promoted']

        for attrib in copy_attribs:
            setattr(versioned_page, attrib, getattr(self, attrib))
        versioned_page.save()

        return versioned_page

    def delete_version(self, version):

        """Removes the draft object associated with a page."""

        parent_version_id = self.get_parent_version().id

        try:
            versioned_page = Page.objects.get(version_id=parent_version_id,
                                              version=version)
            versioned_page.delete()
        except Page.DoesNotExist:
            pass

    def version_exists(self, version):

        parent_version_id = self.get_parent_version().id

        try:
            versioned_page = Page.objects.get(version_id=parent_version_id, version=version)
            return True
        except Page.DoesNotExist:
            return False
