from django.contrib import admin

from .models import (
    ActivityRegistration,
    ActivityVolunteer,
    AuthToken,
    CollectionItem,
    Exhibition,
    GuideInfo,
    MuseumActivity,
    Profile,
    Reservation,
    VisitSlot,
)


admin.site.register(Profile)
admin.site.register(AuthToken)
admin.site.register(Exhibition)
admin.site.register(CollectionItem)
admin.site.register(VisitSlot)
admin.site.register(Reservation)
admin.site.register(MuseumActivity)
admin.site.register(ActivityRegistration)
admin.site.register(GuideInfo)
admin.site.register(ActivityVolunteer)

# Register your models here.
