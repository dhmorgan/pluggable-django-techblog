from django.core.mail import send_mail
from django.conf import settings


from django.template.loader import get_template, select_template
from django.template.context import Context

def send(template, template_data, subject, recipient):

    template = get_template(template)
    msg = template.render(Context(template_data))

    sender = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, msg, sender, [recipient], fail_silently=True)
