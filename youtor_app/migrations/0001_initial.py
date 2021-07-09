# Generated by Django 3.2.5 on 2021-07-09 04:00

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_name', models.CharField(blank=True, max_length=100)),
                ('subject_code', models.CharField(blank=True, max_length=20)),
                ('course_number', models.CharField(blank=True, max_length=20)),
            ],
            options={
                'verbose_name': 'Subjects',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50, unique=True)),
            ],
            options={
                'verbose_name': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='TutionSlotBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('booking_date', models.DateTimeField(auto_now_add=True)),
                ('booking_status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Paid'), (2, 'Failed')], default=0, null=True)),
                ('transaction_id', models.CharField(max_length=50, unique=True)),
                ('total_session_amount', models.FloatField()),
                ('notes', models.TextField()),
                ('tution_session_status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Completed'), (2, 'Cancelled')], default=0, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_who_booked', to=settings.AUTH_USER_MODEL)),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_session', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tution Slot Booking',
            },
        ),
        migrations.CreateModel(
            name='TutorOffers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(5)])),
                ('bio', models.TextField(blank=True)),
                ('transcript', models.FileField(upload_to='tutor_transcripts')),
                ('status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Accepted'), (2, 'Rejected')], default=0, null=True)),
                ('tags', models.ManyToManyField(related_name='tutor_offers', to='youtor_app.Tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tutor Offers',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=250, unique=True)),
                ('role', models.IntegerField(choices=[(0, 'Student'), (1, 'Tutor')], default=0, null=True)),
                ('contact', models.CharField(blank=True, max_length=12, null=True, unique=True)),
                ('year_of_study', models.IntegerField(null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(6)], verbose_name='year')),
                ('profile_image', models.ImageField(blank=True, null=True, upload_to='profile_images')),
                ('major', models.CharField(blank=True, max_length=100)),
                ('confirmed', models.DateTimeField(auto_now_add=True)),
                ('subject', models.ManyToManyField(related_name='user_subjects', to='youtor_app.Subject')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
            },
        ),
        migrations.CreateModel(
            name='TutorReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review', models.TextField()),
                ('rating', models.FloatField(default=0, null=True, validators=[django.core.validators.MaxValueValidator(5), django.core.validators.MinValueValidator(1)])),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='youtor_app.tutionslotbooking')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_r', to=settings.AUTH_USER_MODEL)),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor_r', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tutor Reviews',
            },
        ),
        migrations.CreateModel(
            name='TutorOfferSlots',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'sun'), (1, 'mon'), (2, 'tue'), (3, 'wed'), (4, 'thu'), (5, 'fri'), (6, 'sat')])),
                ('start_time', models.DateTimeField(default=datetime.datetime(2021, 7, 9, 4, 0, 21, 134895))),
                ('end_time', models.DateTimeField(default=datetime.datetime(2021, 7, 9, 4, 0, 21, 134916))),
                ('start_recurr', models.DateTimeField(blank=True, default=None, null=True)),
                ('end_recurr', models.DateTimeField(blank=True, default=None, null=True)),
                ('tutor_offers', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='youtor_app.tutoroffers')),
            ],
            options={
                'verbose_name': 'Tutor Offer Slots',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_confirmed', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OfferSlotBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_date', models.DateTimeField(auto_now_add=True)),
                ('booking_status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Paid'), (2, 'Failed')], default=0, null=True)),
                ('transaction_id', models.CharField(max_length=50, unique=True)),
                ('booked_slots', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='youtor_app.tutorofferslots')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL)),
                ('tutor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tutor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Offer Slot Booking',
            },
        ),
    ]