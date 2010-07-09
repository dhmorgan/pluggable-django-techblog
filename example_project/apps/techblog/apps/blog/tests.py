#!/usr/bin/env python
import models
from random import randint, sample, choice
from datetime import datetime, timedelta
from django.template.defaultfilters import slugify

text = """Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Duis vitae eros. Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Praesent lacus mauris, lacinia vitae, suscipit ac, dignissim ut, massa. Sed rutrum, magna consectetuer sollicitudin auctor, urna tortor suscipit dolor, ac suscipit dui eros gravida erat. Morbi molestie, ligula vitae sagittis adipiscing, felis risus laoreet metus, nec accumsan sem libero ut elit. Pellentesque augue nibh, sollicitudin eu, porttitor sit amet, ultricies quis, odio. Nam id est. Nunc libero urna, hendrerit ut, suscipit et, mollis id, mi. Praesent lobortis leo at neque. Vivamus mattis aliquet ligula. Duis dui sem, posuere eu, porta ac, hendrerit et, ante. Nulla porttitor magna vel ante pharetra viverra."""


test_post = """[summary]
This is a new post, on my [link http://www.willmcgugan.com]blog[/link]...

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.[pullquote]This is a pullquote, doesn't it look pretty? Any blog without pullquotes is clearly inferior![/pullquote] Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Duis vitae eros.
[/summary]

[pullout][b]This is a pull-out.[/b] A pullout give extra information without breaking the text. Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.[/pullout]
Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Duis vitae eros. Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam.

This is something somebody said... Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.

[quote]
This is something somebody said... Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
[/quote]

This is something somebody said... Phasellus dui nisl, porta sed, tristique non, feugiat eu, metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Duis tincidunt est sit amet quam. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Cras non tortor. Sed nunc. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.


[code css]
h2
{
    font-size:90%;
    font-weight:bold;
    margin:10px -2px;
    color:#555;
    color:#0066cc;
    font-family:'Trebuchet MS','Lucida Grande',Verdana,Arial,Sans-Serif;

    border-top:1px solid #ccc;
    border-bottom:1px solid #ccc;
    background-image:url("/media/images/subtlegradient.png");
    background-position:0 1px;
    background-repeat:repeat-x;
    padding:5px;
    clear:both;
}
[/code]"""

def create_blog(title="Test Blog", num_posts = 100):

    def paragraphs(count):
        return "\n".join("%s"% text for _ in xrange(count))

    blog = models.Blog(title = title,
                description = paragraphs(1),
                tagline = "A blog about Life, the Universe and Everything Else",
                slug = slugify(title) )

    blog.save()

    words = """random python I You like code life universe everything god """\
    """atheism hot very difficult easy hard dynamic of the in is under on through """\
    """extremely strangely hardly plainly transparently incredibly """\
    """goes remarkable not if interesting words phone computer will she he are is """\
    """entry base css html games demons juggling brown chess steal this computer """\
    """brave heart motor storm ruby on rails running beginning code plus minus are """


    words = words.split()

    def random_tags():
        num_words = randint(4,8)
        tags = ", ".join(sample(words, num_words))
        return tags


    post = models.Post( blog=blog,
                        published=True,
                        title="Totally Excellent Blog Post",
                        tags_text=random_tags(),
                        slug= "test-post",
                        content = test_post)
    post.save()

    def random_title():
        num_words = randint(2,8)
        title = " ".join(sample(words, num_words))
        title += choice("!? ")
        return title.strip().title()

    display_time = datetime.now()
    for _ in xrange(num_posts):

        display_time -= timedelta(days = randint(2, 15))

        while True:
            title = random_title()
            slug = slugify(title)
            try:
                models.Post.objects.get(slug=slug)
            except models.Post.DoesNotExist:
                break

        post = models.Post(     blog=blog,
                                published=True,
                                created_time = display_time,
                                display_time = display_time,
                                edit_time = display_time,
                                title = title,
                                tags_text=random_tags(),
                                slug=slugify(title),
                                content = paragraphs(randint(1,5)) )
        post.save()

    return blog