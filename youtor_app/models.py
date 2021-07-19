import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.utils.text import slugify
from django.db.models.signals import post_save
from phonenumber_field.modelfields import PhoneNumberField
# from paypal.standard.ipn.models import PayPalIPN


def current_year():
    return datetime.date.today().year

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)

def year_choices():
    return [(r,r) for r in range(1, 7)]

USER_ROLES =  ((0, 'Student'), (1, 'Tutor'))
TUTOR_OFFER_STATUS =  ((0, 'Pending'), (1, 'Accepted'), (2, 'Rejected'))
DAYS = ((0, 'sun'), (1, 'mon'), (2, 'tue'), (3, 'wed'), (4, 'thu'), (5, 'fri'), (6, 'sat'))


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    # other fields...

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length = 250, unique=True) 
    role = models.IntegerField(choices=USER_ROLES, null=True, default=0)
    contact = models.CharField(max_length=12, null=True, blank=True, unique=True)
    year_of_study = models.IntegerField('year', null=True, validators=[MinValueValidator(1), MaxValueValidator(6)])
    profile_image = models.ImageField(upload_to='profile_images', null=True, blank=True)
    major = models.CharField(max_length=100, blank=True)
    subject = models.ManyToManyField('Subject', related_name='user_subjects')
    confirmed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.user.first_name + ' ' + self.user.last_name + ' ' + str(self.user.id))
        super(UserProfile, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "User Profile"
    

class Subject(models.Model):
    subject_name = models.CharField(max_length=100, blank=True)
    # subject_code = models.CharField(max_length=20, blank=True)
    # course_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.subject_name

    class Meta:
        verbose_name = "Subjects"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tags"


class TutorOffers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(5)])
    bio = models.TextField(blank=True)
    transcript = models.FileField(upload_to='tutor_transcripts')
    status = models.IntegerField(choices=TUTOR_OFFER_STATUS, null=True, default=0)
    tags = models.ManyToManyField('Tag', related_name='tutor_offers')

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "Tutor Offers"


class TutorOfferSlots(models.Model):
    tutor_offers = models.ForeignKey(TutorOffers, on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS, null=False)
    start_time = models.DateTimeField(default=datetime.datetime.now())
    end_time = models.DateTimeField(default=datetime.datetime.now())
    start_recurr = models.DateTimeField(default=None, blank=True, null=True)
    end_recurr = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.tutor_offers) + str(self.id)

    class Meta:
        verbose_name = "Tutor Offer Slots"


STATUS =  ((0, 'Pending'), (1, 'Paid'), (2, 'Failed'))
class OfferSlotBooking(models.Model):
    booked_slots = models.ForeignKey(TutorOfferSlots, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    booking_status = models.IntegerField(choices=STATUS, null=True, default=0)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor')
    transaction_id = models.CharField(max_length=50, unique=True, null=False, blank=False)

    class Meta:
        verbose_name = "Offer Slot Booking"


STATUS =  ((0, 'Pending'), (1, 'Paid'), (2, 'Failed'))
TUTION_SESSION_STATUS = ((0, 'Pending'), (1, 'Completed'), (2, 'Cancelled'))
class TutionSlotBooking(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    booking_date = models.DateTimeField(auto_now_add=True)
    booking_status = models.IntegerField(choices=STATUS, null=True, default=0)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_who_booked')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_session')
    transaction_id = models.CharField(max_length=50, unique=True, null=False, blank=False)
    total_session_amount = models.FloatField()
    notes = models.TextField()
    tution_session_status = models.IntegerField(choices=TUTION_SESSION_STATUS, null=True, default=0)


    class Meta:
        verbose_name = "Tution Slot Booking"


class TutorReview(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_r')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutor_r')
    review = models.TextField()
    rating = models.FloatField(default=0, null=True, validators=[MaxValueValidator(5), MinValueValidator(1)])
    booking = models.ForeignKey(TutionSlotBooking, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Tutor Reviews"