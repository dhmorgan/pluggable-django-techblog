from django.core.management.base import NoArgsCommand
from django.db import transaction

import re

re_broken_a=re.compile(r'<a href="<a (href="(.*?)".*?</a>.*?)>')

class Command(NoArgsCommand):
    help = "Fixes an issue in the wxr import script"

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        from techblog.apps.comments.models import Comment

        count = 0

        for c in Comment.objects.all():

            if re_broken_a.findall(c.content):
                new_content = re_broken_a.sub(r'<a href="\2">', c.content)
                c.content = new_content
                c.save()

                count += 1

        print count, "substitutions"