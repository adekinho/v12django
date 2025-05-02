from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('results/', views.results_view, name='results'),
    path('sell/', views.sell_view, name='sell'),
    path('respond/<int:request_id>/', views.respond_view, name='respond'),
    path('delete_search/<int:search_id>/', views.delete_search_view, name='delete_search'),
    path('update_search/<int:search_id>/', views.update_search_view, name='update_search'),
]
