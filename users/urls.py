from django.urls import path

from . import views

urlpatterns = [
    # path() для страницы регистрации нового пользователя
    # ее полный адрес будет auth/signup/, но префикс auth/ обрабатывается
    # в головном urls.py
    path('signup/', views.SignUp.as_view(), name='signup'),

]
