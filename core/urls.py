from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Main URLs
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tracker/', views.tracker_view, name='tracker'),
    path('tracker/<int:year>/<int:month>/', views.tracker_view, name='tracker'),
    path('categories/', views.categories_view, name='categories'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('penalties/', views.penalties_view, name='penalties'),
    path('profile/', views.profile_view, name='profile'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('chart-data/', views.get_chart_data, name='chart_data'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
]