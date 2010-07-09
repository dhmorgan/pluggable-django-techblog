from django.core.management.base import NoArgsCommand
from django.db import transaction

class Command(NoArgsCommand):
    help = "Refreshes tag counts if they get out of sync"

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        from techblog.apps.blog.models import Tag, Post
        for tag in Tag.objects.all():
            tag.count=0
            tag.save()
        for p in Post.objects.all():
            p.tags.clear()
            p.save()
