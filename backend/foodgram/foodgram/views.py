from django.shortcuts import redirect
from django.urls import reverse


def url(request, short):
    return redirect(reverse('recipe-list'), user_id=request.user.id)
