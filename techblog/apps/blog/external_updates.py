from models import Microblog
from models import Post
import postmarkup

from datetime import datetime
import twitter
import re

from django.template.defaultfilters import slugify

def update():
    update_microblogs();


re_microblog_reply = re.compile(r'^@\w+')

_hash_tags = re.compile(r'(?:^|\s)#(\w+)')
def parse_hashtags(microblog):

    for match in _hash_tags.findall(microblog):
        if match.strip():
            yield match

_microblog_user = re.compile(r'(^|\s)\@\w+')

def microblog_microformat(txt, url):

    def repl_hash(match):
        user_name = unicode(match.group(0))[2:].lower()
        return ' @<a href="%s%s">%s</a>' % (url, user_name, user_name)

    return _microblog_user.sub(repl_hash, txt).lstrip()


def update_microblogs():


    def char_break(text, num_chars):
        if len(text) < num_chars:
            return text
        return text[:num_chars-3].rsplit(' ', 1)[0] + '...'

    twitter_api = twitter.Api();
    for microblog in Microblog.objects.all():
        if not microblog.enabled:
            continue
        for tweet in twitter_api.GetUserTimeline(microblog.username):

            if re_microblog_reply.match(tweet.text):
                continue

            tweet_guid = u"TWITTER:%s" % str(tweet.id)
            try:
                post = Post.objects.get(blog=microblog.blog, guid=tweet_guid)
            except Post.DoesNotExist:
                tweet_time = datetime.fromtimestamp(tweet.created_at_in_seconds)
                title = char_break(tweet.text, 50)

                tweet_text = tweet.text
                tweet_text = postmarkup.textilize(tweet_text)
                tweet_text = microblog_microformat(tweet_text, microblog.url)


                tags = [t.strip() for t in microblog.tags.split(',')]
                tags += list(parse_hashtags(tweet.text))
                if 'http' in tweet.text:
                    tags.append('link')
                tags = list(set(tags))

                post = Post(blog = microblog.blog,
                            title = "Microblog: " + title,
                            source = "microblog:" + microblog.service,
                            tags_text = ",".join(tags),
                            slug = slugify(title),
                            published = True,
                            guid = tweet_guid,
                            allow_comments=True,
                            created_time=datetime.now(),
                            edit_time=datetime.now(),
                            display_time=tweet_time,
                            content = tweet_text,
                            content_markup_type = "html",
                            version = 'live',
                            template_path = microblog.template_path,
                            )
                post.save()
                post.display_time = tweet_time
                post.save()
