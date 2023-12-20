from random import random

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.decorators.cache import cache_page

from myauth.models import Profile


class HelloView(View):
    welcome_message = _("welcome hello world")

    def get(self, request: HttpRequest) -> HttpResponse:
        items_str = request.GET.get("items") or 0
        items = int(items_str)
        products_line = ngettext(
            "one product",
            "{count} products",
            items,
        )
        products_line = products_line.format(count=items)
        return HttpResponse(
            f"<h1>{self.welcome_message}</h1>"
            f"\n<h2>{products_line}</h2>"
        )


class AboutMeView(TemplateView):
    template_name = 'myauth/about_me.html'


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "myauth/user_details.html"
    context_object_name = "us"


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "myauth/user_list.html"
    context_object_name = "users"


class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = Profile
    fields = "bio", "agreement_accepted", "avatar"
    template_name_suffix = "_update_form"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_staff or self.request.user == self.get_object().user:
            return True
        return self.request.user.has_perm("myauth.change_profile")

    def get_success_url(self):
        return reverse("myauth:about-user", kwargs={"pk": self.get_object().user.pk})


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'myauth/register.html'
    success_url = reverse_lazy('myauth:about-me')

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


# def login_view(request: HttpRequest):
#     if request.method == 'GET':
#         if request.user.is_authenticated:
#             return redirect('/admin/')
#
#         return render(request, 'myauth/login.html')
#
#     username = request.POST['username']
#     password = request.POST['password']
#
#     user = authenticate(request, username=username, password=password)
#     if user:
#         login(request, user)
#         return redirect('/admin/')
#
#     return render(request, 'myauth/login.html', {'error': 'Invalid login credentials'})

# def logout_view(request: HttpRequest) -> HttpResponse:
#     logout(request)
#     return redirect(reverse('myauth:login'))

class MyLogoutView(LogoutView):
    next_page = reverse_lazy('myauth:login')


def set_cookie_view(request: HttpRequest) -> HttpResponse:
    response = HttpResponse('Cookie set')
    response.set_cookie('fizz', 'buzz', max_age=3600)
    return response


@cache_page(60 * 2)
def get_cookie_view(request: HttpRequest) -> HttpResponse:
    value = request.COOKIES.get('fizz', 'default value')
    return HttpResponse(f'Cookie value: {value!r} + {random()}')


def set_session_view(request: HttpRequest) -> HttpResponse:
    request.session['foobar'] = 'spameggs'
    return HttpResponse('Session set!')


def get_session_view(request: HttpRequest) -> HttpResponse:
    value = request.session.get('foobar', 'default')
    return HttpResponse(f'Session value: {value!r}')


class FooBarView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'foo': 'bar', 'spam': 'eggs'})
