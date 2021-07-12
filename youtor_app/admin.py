from django.contrib import admin
from .models import UserProfile, Subject, TutorOffers, TutorOfferSlots, TutorReview, Tag, TutionSlotBooking


class TutorOffersAdmin(admin.ModelAdmin):
    list_display = ('user', 'status')



admin.site.register(UserProfile)
admin.site.register(Subject)
admin.site.register(TutorOffers, TutorOffersAdmin)
admin.site.register(TutorOfferSlots)
admin.site.register(TutionSlotBooking)
admin.site.register(TutorReview)
admin.site.register(Tag)
