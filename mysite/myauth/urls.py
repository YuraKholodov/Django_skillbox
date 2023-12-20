from django.contrib.auth.views import LoginView
from django.urls import path

from .views import (
    get_cookie_view,
    set_cookie_view,
    set_session_view,
    get_session_view,
    MyLogoutView,
    AboutMeView,
    ProfileUpdateView,
    RegisterView,
    FooBarView,
    UserDetailView,
    UserListView,
    HelloView,
)

app_name = 'myauth'

urlpatterns = [
    # path('login/', login_view, name='login'),
    path(
        'login/',
        LoginView.as_view(
            template_name='myauth/login.html',
            redirect_authenticated_user=True,
        ),
        name='login'),

    path('hello/', HelloView.as_view(), name='hello'),
    # path('logout/', logout_view, name='logout'),
    path('logout/', MyLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    path('about-me/', AboutMeView.as_view(), name='about-me'),
    path('user-list/', UserListView.as_view(), name='user-list'),
    path('about-user/<int:pk>/', UserDetailView.as_view(), name='about-user'),
    path('user/<int:pk>/update/', ProfileUpdateView.as_view(), name='update-profile'),



    path('cookie/get/', get_cookie_view, name='cookie_get'),
    path('cookie/set/', set_cookie_view, name='cookie_set'),

    path('session/set/', set_session_view, name='session_set'),
    path('session/get/', get_session_view, name='session_get'),

    path('foo-bar/', FooBarView.as_view(), name='foo-bar'),
]
