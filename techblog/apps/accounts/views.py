from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import auth


def login(request):

    td = {}
    td['sections'] = {}
    td['next'] = request.GET.get('next', '')

    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next = request.POST.get('next')

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return HttpResponseRedirect(next)


    return render_to_response("accounts/login.html",
                              td,
                              context_instance=RequestContext(request))

def logout(request):

    auth.logout(request)
    next = request.GET.get('next', '/accounts/login/')

    return HttpResponseRedirect(next)