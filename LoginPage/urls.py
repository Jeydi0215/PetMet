from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import PetCreateView, PostPendingPetViewSet, PendingPetList, ReactAdoptedPetsView, ReactAdoptPetDetailView, ReactTrackUpdateList, UpdatePendingPetView,  ReactCustomUserDetailView, ReactCreateUserView
#, PetSearchView, AdoptionRequestList,, RequestAdoptionRequestList, AdoptionRequestUpdateView, UserSignupView, AdminLoginView, AdminPendingPetList,AdminPetViewSet, AdminApprovedPetsList, AdminAdoptedPetsList, AdoptionDetailView,AdminAdoptedPetDetailView,
router = DefaultRouter()
router.register(r'admins', views.AdminViewSet)
router.register(r'adoption-requests', views.PetAdoptionRequestTableViewSet)
router.register(r'adoptions', views.PetAdoptionTableViewSet)
router.register(r'pending-pets', views.PendingPetForAdoptionViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('home', views.home, name='home'),
    path('admin/', views.admin_home, name='admin_home'),  # Add this line
    path('accounts/login/', views.custom_login, name='admin_login'),  # Use the custom login view
    path('admin/home_page/', views.admin_homepage, name='homepage_admin'),  # Admin homepage view
    #path('about', views.about, name='about'),
    path('', views.landing, name='landing'),
     path('pets/', views.pet_list, name='pet_list'),  # URL pattern for the pet list
    #path('admin', views.admin, name='admin'),
    path('logout_admin', views.logout_admin, name='logout_admin'),
    path('admin_signup', views.admin_signup, name='admin_signup'),
    path('signup', views.signup, name='signup'),
    path('login', views.user_login, name='login'),
    #path('article/<pk>/', views.article_detail, name='article_detail'),
    path('homepage', views.homepage, name='homepage'),
    path('logout', views.logout, name='logout'),
    path('pets/<pk>/', views.pet_detail_view, name='pet_detail'),
    path('add_pet', views.add_pet, name='add_pet'),
    path('search_results/', views.search_results, name='search_results'),
    #path('success/', views.success, name='success'),
    #path('login/', views.CustomLoginView.as_view(), name='login_custom'),
    #path('home/', views.HomeView.as_view(), name='homepage_admin'),
    path('pending_pets/', views.pending_pets, name='pending_pets'),
    path('pet/<pk>/', views.pet_detail_view, name='pet_detail_view'),
    path('approve/<pk>/', views.approve_pet, name='approve_pet'),
    path('adopt/<pk>/', views.adopt_pet, name='adopt_pet'),
    path('admin_approved_pet/', views.admin_approved_pet, name='admin_approved_pet'),
    path('adoption-requests/', views.list_adoption_requests, name='adoption_requests'),
    path('adoption-requests/<int:request_id>/', views.view_adoption_request, name='view_adoption_request'),
    path('adoption-table/', views.adoption_table_view, name='adoption_table'),
    path('adoption-detail/<int:pk>/', views.adoption_detail_view, name='adoption_detail'),
    path('requests/', views.view_requests, name='view_requests'),
    path('requests/<int:request_id>/', views.view_request, name='view_request'),
    path('requests/<int:request_id>/update_status/<str:new_status>/', views.update_status, name='update_status'),
    path('adopted-history/', views.adopted_history, name='adopted_history'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('admin_approved_pet_detail/<int:pet_id>/', views.admin_approved_pet_detail, name='admin_approved_pet_detail'),
    #path('api/login_react/', views.login_react, name='login_react'),
    path('api/create_adoption_request/', views.create_adoption_request, name='create_adoption_request'),
    #path('api/adoption-id/', views.get_latest_adoption_id, name='get_latest_adoption_id'),
    path('api/pendingpetsforadoption/', PetCreateView.as_view(), name='pending_pets_for_adoption'),
    #path('api/pet_search/', PetSearchView.as_view(), name='pet-search'),
    #path('api/adoption_requests/<str:user_id>/', AdoptionRequestList.as_view(), name='adoption-requests'),
    path('api/postpending-pets/', PostPendingPetViewSet.as_view({'get': 'list'}), name='postpending-pets'),
    path('api/requestpendingpetforadoption/', PendingPetList.as_view(), name='pending-pets'),
    #path('api/requestpetadoptiontable/', RequestAdoptionRequestList.as_view(), name='adoption-requests'),
    #path('api/petadoptiontable-requests/<int:pk>/', AdoptionRequestUpdateView.as_view(), name='petadoption-request-update'),
    #path('api/auth/signup/', UserSignupView.as_view(), name='user-signup'),
    #path('api/admin_login/', AdminLoginView.as_view(), name='admin_login'),
    #path('api/pets/pending/', AdminPendingPetList.as_view(), name='admin_pending-pets'),
    #path('api/admin_pets/<str:pk>/', AdminPetViewSet.as_view({'patch': 'partial_update'}), name='admin_pet-detail'),
    #path('api/pets/admin_approved/', AdminApprovedPetsList.as_view(), name='admin_approved-pets-list'),
    #path('api/pets/admin_adopted/', AdminAdoptedPetsList.as_view(), name='admin_adopted-pets-list'),
    path('reportadopted_pets/', views.reportadopted_pets, name='reportadopted_pets'),
    path('reportRequestpet_detail/<int:pet_id>/', views.reportRequestpet_detail, name='reportRequestpet_detail'),  # Detail view for a specific pet
    path('add_report/<int:pet_id>/', views.add_report, name='add_report'),
    path('report_details/<int:pet_adoption_id>/', views.report_details, name='report_details'),
    path('report/<int:id>/', views.report_detail, name='report_detail'),
    path('adoption/<int:id>/', views.AdoptionDetailView, name='admin_adoption_detail_history'),
    path('admin_report/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    path('post_adoption/<int:id>/edit/', views.post_adoption_edit, name='post_adoption_edit'),
    path('post_adoption/<int:id>/delete/', views.post_adoption_delete, name='post_adoption_delete'),
    path('api/react_adopted-pets/<int:user_id>/', ReactAdoptedPetsView.as_view(), name='react_adopted-pets'),
    path('api/react_adopt_pet_adoption_table/<int:pk>/', ReactAdoptPetDetailView.as_view(), name='react_adopt_pet-detail'),
    path('api/react_add_report/', views.react_add_report, name='react_add_report'),
    path('api/react_track_update_table/', ReactTrackUpdateList.as_view(), name='react_track-update-list'),
    path('api/react_edit_postpending-pets/<int:pk>/', UpdatePendingPetView.as_view(), name='update_pending_pet'),
    path('api/postpending-pets/<int:post_id>/', views.delete_pending_pet, name='delete_pending_pet'),
    #path('api/pets/admin_pet_adoption/<int:pk>/', AdminAdoptedPetDetailView.as_view(), name='admin_pet_adoption-detail'),
    path('api/react_admin_user/<int:pk>/', ReactCustomUserDetailView.as_view(), name='react_customuser-detail'),
    path('api/react_create_users/', ReactCreateUserView.as_view()),
    path('terms/', views.terms_conditions_view, name='terms_conditions'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),
    #path('api/get_notifications/', views.get_notifications, name='get_notifications'),
]