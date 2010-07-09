from django.core.management.base import NoArgsCommand

from techblog.apps.blog.external_updates import update


class Command(NoArgsCommand):
    help = "Updates external items in the blog"

    def handle_noargs(self, **options):
        update()
