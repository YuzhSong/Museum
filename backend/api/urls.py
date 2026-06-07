from django.urls import path

from . import views

urlpatterns = [
    path("api/register/", views.register),
    path("api/login/", views.login),
    path("api/logout/", views.logout),
    path("api/profile/", views.profile),
    path("api/exhibitions/", views.exhibition_list),
    path("api/exhibitions/<int:pk>/", views.exhibition_detail),
    path("api/exhibitions/<int:pk>/collections/", views.exhibition_collections),
    path("api/collections/<int:pk>/", views.collection_detail),
    path("api/visit-slots/", views.visit_slots),
    path("api/reservations/", views.reservations),
    path("api/reservations/<int:pk>/cancel/", views.cancel_reservation),
    path("api/admin/reservations/", views.admin_reservations),
    path("api/activities/", views.activity_list),
    path("api/activities/<int:pk>/", views.activity_detail),
    path("api/activities/<int:pk>/register/", views.register_activity),
    path("api/my/activity-registrations/", views.my_activity_registrations),
    path("api/volunteer/activities/", views.volunteer_activities),
    path("api/volunteer/activities/<int:pk>/registrations/", views.volunteer_activity_registrations),
    path("api/guides/", views.guide_list),
    path("api/guides/<int:pk>/", views.guide_detail),
    path("api/admin/exhibitions/", views.admin_exhibitions),
    path("api/admin/exhibitions/<int:pk>/", views.admin_exhibition_detail),
    path("api/admin/collections/", views.admin_collections),
    path("api/admin/collections/<int:pk>/", views.admin_collection_detail),
    path("api/admin/activities/", views.admin_activities),
    path("api/admin/activities/<int:pk>/", views.admin_activity_detail),
    path("api/admin/guides/", views.admin_guides),
    path("api/admin/guides/<int:pk>/", views.admin_guide_detail),
]
