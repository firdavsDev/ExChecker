"""exchecker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from exchecker_app import views

#---------------------- PAGE NOT FOUND (404) ---------------------#
handler404 = 'exchecker_app.views.handler404'

#---------------------- SERVER ERROR (500) ---------------------#
handler500 = 'exchecker_app.views.handler500'

urlpatterns = [
    path('', views.main, name='main'),
    path('get_template', views.get_template, name='get_template'),
    path('check_exams', views.check_exams, name='check_exams'),
    path('my_templates', views.my_templates, name='my_templates'),
    path('download_all_templates', views.download_all_templates, name='download_all_templates'),
    
    #----------------------SETTER PATHS----------------------#
    path('upload_exams/', views.upload_exams),
    
    #----------------------GETTER PATHS----------------------#
    path('get_progress_template/', views.get_progress_template),

    re_path(r'\.js$', views.serve_js),
    re_path(r'\.css$', views.serve_css),
    
    #----------------------USER PATHS----------------------#
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register, name='register'),
    #path('accounts/forgot_password/', views.forgot_password, name='forgot_password'),
    #path('accounts/restore_password/', views.restore_password, name='restore_password'),
    #path('accounts/verify_account/', views.verify_account, name='verify_account'),
    path('admin/', admin.site.urls),
]
