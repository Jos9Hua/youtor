import string
import random
import json
import time
import pytz
import datetime as dt

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from .models import User, UserProfile, TutorOffers, Tag, TutorOfferSlots, Subject, TutionSlotBooking, TutorReview
from .forms import UserForm, UserProfileForm, UserEditForm, UserProfileEditForm, TutorOffersForm, TagForm
from django.contrib.auth.forms import PasswordChangeForm

from django.db.models import Q

from django.core.mail import EmailMessage, EmailMultiAlternatives
from youtor_app.tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.utils import timezone
from django.db.models import Count, Min, Sum, Avg, Max

import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


def randomString(stringLength=6):
    """Generate a random string with the combination of lowercase and uppercase letters """
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))


# Public views
def index(request):
    return render(request, 'youtor_app/index.html')


# email View
def account_activation_sent(request):
    return HttpResponseRedirect(request, './youtor_app/account_activation_sent.html', {})


def create_unique_id():
    return ''.join(random.choices(string.digits, k=8))


def register(request):
    context_dict = {}
    registered = False
    user_form = UserForm()
    profile_form = UserProfileForm()

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.username = user.email
            user.is_active = False

            user.set_password(user.password)  # Hash the password
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user  # Set One to One relationship between UserForm and UserProfileForm
            profile.contact = str(profile.contact)
            print(profile)
            if 'profile_image' in request.FILES:
                print('profile image found.')
                profile.profile_image = request.FILES['profile_image']
            profile.save()

            current_site = get_current_site(request)
            mail_subject = 'Activate your Youtor account.'
            message = render_to_string('./youtor_app/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = request.POST.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.content_subtype = "html"
            email.send()
            # return redirect('login')
            registered = True
            return render(request, 'youtor_app/registration.html', {'registered': registered})

        else:
            if profile_form.errors:
                error = profile_form.errors
            elif user_form.errors:
                error = user_form.errors
            registered = False
            return render(request, 'youtor_app/registration.html', {'registered': registered, 'error': error})

    context_dict['user_form'] = user_form
    context_dict['profile_form'] = profile_form

    return render(request, 'youtor_app/registration.html', {'registered': registered})


def activate(request, user_id, token):
    try:
        user_id = force_text(urlsafe_base64_decode(user_id))
        user = User.objects.get(pk=user_id)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('login')
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = authenticate(username=email, password=password)
        except User.DoesNotExist as e:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(email, password))
            return render(request, 'youtor_app/login.html', {'login_error': 'Username/Password incorrect, please try again!'})

        if user is not None:
            if user.is_active:
                login(request, user)
                user_profile = UserProfile.objects.get(user_id=user.id)

                if user_profile.role == 1:
                    request.session['user_type'] = "Tutor"
                elif user_profile.role == 0:
                    request.session['user_type'] = "Student"

                return redirect('dashboard')

            else:
                return render(request, 'youtor_app/login.html', {'login_error': 'Your account is not active.'})

        else:
            print("Someone tried to login and failed.")
            print("They used username: {} and password: {}".format(email, password))
            return render(request, 'youtor_app/login.html', {'login_error': 'Username/Password incorrect, please try again!'})

    else:
        # Nothing has been provided for username or password.
        return render(request, 'youtor_app/login.html', {})


@login_required
def user_logout(request):
    logout(request)
    # Return to Landing page
    return redirect('')


def contact(request):
    return render(request, 'youtor_app/contact.html', {})
    
def faq(request):
    return render(request, 'youtor_app/faq.html', {})


@login_required
def change_password(request):
    form_error = False
    current_user_email = request.user.email
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            # send email on password change..
            subject, from_email, to = 'Password Changed', settings.EMAIL_HOST_USER, current_user_email,
            text_content = 'This is an important message.'
            html_content = '<h3 style="color:blue;">Your Password Changed</h3><p>The Password for the youtr system was just changed.</p><p>if this was you, then you can safely ignored this email.</p><hr><p>Thanks</p>,Youtor'
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            return render(request, 'youtor_app/login.html', {})
        else:
            form_error = True
            return render(request, 'youtor_app/forgot_password.html', {'form': form,'form_error':form_error})
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'youtor_app/forgot_password.html', {
        'form': form,'form_error':form_error
    })
# ------------------public views ends-------------------------

# Common Dashboard views

from django.db.models import OuterRef, Subquery


@login_required
def dashboard_view(request):
    context_dict = {}

    all_tags = Tag.objects.all()
    context_dict['available_tags'] = all_tags

    min_val = TutorOffers.objects.aggregate(Min('rate')).values()
    max_val = TutorOffers.objects.aggregate(Max('rate')).values()
    context_dict['min_val'] = min_val
    context_dict['max_val'] = max_val


    tutor_ids = TutorReview.objects.all().values('tutor_id')
    result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(Avg('rating'))
    print("result:",result)
    context_dict['average'] = result

    all_subs = Subject.objects.all()
    context_dict['all_subjects'] = all_subs

    try:
        upcoming_booking_instance = TutionSlotBooking.objects.filter(tutor_id=request.user.id, start_time__gte=dt.datetime.now()).order_by('start_time')
        past_booking_instance = TutionSlotBooking.objects.filter(tutor_id=request.user.id, end_time__lte=dt.datetime.now()).order_by('start_time')
        print(upcoming_booking_instance)
    except Exception as e:
        print("No Bookings!:", e)
        upcoming_booking_instance = None
        past_booking_instance = None

    context_dict['upcoming_bookings'] = upcoming_booking_instance
    context_dict['past_bookings'] = past_booking_instance

    try:
        user_profile_instance = UserProfile.objects.get(
            user_id=request.user.id)
    except UserProfile.DoesNotExist:
        user_profile_instance = None

    if user_profile_instance.role == 1:
        try:
            tutor_offer = TutorOffers.objects.get(user_id=request.user.id)
            context_dict['tutor_offer'] = tutor_offer
        except TutorOffers.DoesNotExist:
            context_dict['tutor_offer'] = None
    else:
        all_offers = TutorOffers.objects.filter(status=1)
        context_dict['all_offers'] = all_offers

    return render(request, 'youtor_app/dashboard.html', context_dict)


@login_required
def user_profile_view(request):
    context_dict = {}

    all_tags = Tag.objects.all()
    context_dict['available_tags'] = all_tags

    all_subs = Subject.objects.all()
    context_dict['all_subjects'] = all_subs

    user_profile_instance = get_object_or_404(UserProfile, user=request.user)
    user_instance = get_object_or_404(User, id=user_profile_instance.user_id)

    user_data = {
        'id': user_profile_instance,
        'first_name': user_profile_instance.user.first_name,
        'last_name': user_profile_instance.user.last_name,
        'email': user_profile_instance.user.email,
        'contact': user_profile_instance.contact,
        'year_of_study': user_profile_instance.year_of_study,
        'major': user_profile_instance.major,
        'profile_image': user_profile_instance.profile_image
    }
    user_form = UserEditForm(instance=user_instance)
    profile_form = UserProfileEditForm(data=user_data)

    if TutorOffers.objects.filter(user_id=user_instance.id).exists():
        offer_instance = TutorOffers.objects.get(user_id=user_instance.id)
        offer_form = TutorOffersForm(instance=offer_instance)
    else:
        offer_instance = None
        offer_form = TutorOffersForm()

    if request.method == "POST" and 'submitPersonalInfo' in request.POST:
        user_form = UserEditForm(request.POST, instance=user_instance)
        profile_form = UserProfileEditForm(
            request.POST, request.FILES, instance=user_profile_instance)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.username = user.email
                user.save()

                profile_form.save(commit=False)
                profile_form.contact = profile_form.clean_contact()
                profile_form.profile_image = request.FILES.get('profile_image')
                profile_form.save()

                context_dict['status'] = 200

            except Exception as e:
                context_dict['status'] = 500
                print("Exception occured while saving user personal details: ", e)
        else:
            if profile_form.errors:
                context_dict['profile_form_errors'] = profile_form.errors

            if user_form.errors:
                context_dict['user_form_errors'] = user_form.errors

            context_dict['status'] = 400

    elif request.method == 'POST' and 'submitOfferInfo' in request.POST:
        if offer_instance:
            offer_form = TutorOffersForm(
                request.POST, request.FILES, instance=offer_instance)
        else:
            offer_form = TutorOffersForm(request.POST, request.FILES)

        if offer_form.is_valid():
            try:
                # saving offer instance
                offer = offer_form.save(commit=False)
                if offer_instance == None:
                    offer.user = user_instance

                transc = request.FILES.get('transcript', None)
                if transc:
                    offer.transcript = transc
                else:
                    offer.transcript = offer_instance.transcript
                offer.save()

                # tags mapping with offer instance
                tags_in_post = request.POST.get('tags', None).split(',')
                if tags_in_post:
                    print(tags_in_post)
                    for tag_name in tags_in_post:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        offer.tags.add(tag)

                # subjects mapping with the user profile instance
                subjects_by_user = request.POST.get(
                    'subjects', None).split(',')
                if subjects_by_user:
                    print(subjects_by_user)
                    for sub in subjects_by_user:
                        subj_to_add = Subject.objects.get(
                            subject_name=sub.strip())
                        user_profile_instance.subject.add(subj_to_add)

                context_dict['status'] = 200
            except Exception as e:
                context_dict['status'] = 500
                print("Exception occured while saving offer details: ", e)

        else:
            if offer_form.errors:
                context_dict['status'] = 400
                context_dict['offer_form_errors'] = offer_form.errors

    context_dict['user_form'] = user_form
    context_dict['offer_form'] = offer_form
    context_dict['user_profile_form'] = profile_form
    context_dict['available_tags'] = all_tags
    context_dict['available_subjects'] = all_subs
    context_dict['offer_instance'] = offer_instance
    context_dict['user_profile_instance'] = user_profile_instance

    return render(request, 'youtor_app/user_profile.html', context=context_dict)


# ------------------common views ends-------------------------


# Tutor related views
@login_required
def remove_subs_tags(request):
    if request.method == 'POST':
        sub_to_remove = request.POST.get('sub_to_remove', None)
        user_id = request.POST.get('user_id', None)
        tag_to_remove = request.POST.get('tag_to_remove', None)
        offer_id = request.POST.get('offer_id', None)

        try:
            if sub_to_remove:
                sub_to_remove = sub_to_remove.split(',')
                print(
                    f"sub_to_remove: {sub_to_remove[0]} -- type: {type(sub_to_remove[0])}")
                user_prof_instance = UserProfile.objects.get(user_id=user_id)
                sub_instance = Subject.objects.get(
                    subject_name=sub_to_remove[0])
                user_prof_instance.subject.remove(sub_instance)

            if tag_to_remove:
                tag_to_remove = tag_to_remove.split(',')
                print(
                    f"tag_to_remove: {tag_to_remove[0]} -- type: {type(tag_to_remove[0])}")
                offer_instance = TutorOffers.objects.get(id=offer_id)
                tag_instance = Tag.objects.get(name=tag_to_remove[0])
                offer_instance.tags.remove(tag_instance)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print("Exception Occured when deleting subects or tags: ", e)
            return JsonResponse({'status': 'error'})


@login_required
def create_tutor_profile(request):
    context_dict = {}
    if request.method == 'POST' and request.FILES:
        print('get.')
        print(request)
        subject = request.POST.get('subjects', None).split(',')
        tutor_bio = request.POST.get('bio', None)
        offer_tags = request.POST.get('tags', None).split(',')
        offer_rate = request.POST.get('rate', None)
        tutor_profile_image = request.FILES.get('profile_image', None)
        tutor_transcript = request.FILES.get('transcript', None)

        if subject != None and tutor_bio !=None and offer_rate != None and tutor_transcript != None:

            print(f"tutor_profile_image: {tutor_profile_image}")
            try:
                tutor_profile_instance = UserProfile.objects.get(user_id=request.user.id)
                if tutor_profile_instance:
                    tutor_profile_instance.profile_image = tutor_profile_image
                    tutor_profile_instance.save()

                    try:
                        old_offer = TutorOffers.objects.get(user_id=request.user.id, status=2).delete()
                    except Exception as e:
                        old_offer = None
                        print("Old Offer not found for the user, new offer will be created: ", e)

                    if len(subject) != 0:
                        for sub in subject:
                            print(sub)
                            # subj_to_add = Subject.objects.get(subject_name=sub.strip())
                            # if (not subj_to_add):
                            try:
                                subj_to_add = Subject.objects.get(subject_name=sub.strip())
                                tutor_profile_instance.subject.add(subj_to_add)
                            except Exception as s:
                                s = Subject.objects.create(subject_name = sub)
                                tutor_profile_instance.subject.add(s)

                            # tutor_profile_instance.subject.add(subj_to_add)

                        tutor_offer = TutorOffers.objects.create(
                            user_id=tutor_profile_instance.user_id,
                            rate=offer_rate,
                            bio=tutor_bio,
                            transcript=tutor_transcript,
                        )
                        # Tags will be added if they are
                        if len(offer_tags) != 0:
                            print(offer_tags)
                            for tag_name in offer_tags:
                                tag, created = Tag.objects.get_or_create(
                                    name=tag_name)
                                tutor_offer.tags.add(tag)

                        return JsonResponse({'status': 200})

                    else:
                        context_dict['status'] = 'error'
                        context_dict['message'] = 'Subjects cannot be empty, please select atleast one subjects you can teach.'

                        return JsonResponse(context_dict)

            except Exception as e:
                print("Exception Occured: ", e)
                return JsonResponse({'status': 'error', 'message': e})

        else:
            return JsonResponse({'status': 'error', 'message': "Please enter value for all the fields"})
    else:
        return JsonResponse({'status': 'error', 'message': "Not Allowed"})

@login_required
def offer_scheduling(request):
    context_dict = {}

    try:
        tutor_offer = TutorOffers.objects.get(user_id=request.user.id)
        if tutor_offer:
            offer_slot_list = TutorOfferSlots.objects.filter(tutor_offers_id=tutor_offer.id)

            available_slots_list = []
            for slot in offer_slot_list:
                print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
                if slot.start_recurr:
                    available_slots_list.append({
                        'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                        'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                        'id': slot.id,
                        'day': slot.day,
                        'start_recurr': slot.start_recurr.strftime("%Y-%m-%dT%H:%M"),
                        'end_recurr': slot.end_recurr.strftime("%Y-%m-%dT%H:%M")
                    })
                else:
                    available_slots_list.append({
                        'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                        'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                        'id': slot.id,
                        'day': slot.day
                    })

    except TutorOffers.DoesNotExist as e:
        tutor_offer = None
        available_slots_list = None
        print("Exception Occured :", e)


    # fetch booked slots on available slots if any
    try:
        booked_slots = TutionSlotBooking.objects.filter(tutor_id=request.user.id, start_time__gt=timezone.now())

        booked_slots_list = []
        for slot in booked_slots:
            print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
            booked_slots_list.append({
                'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                'id': slot.id
            })
    except Exception as e:
        booked_slots_list = None
        print("Exception Occured in fetching booked slots:", e)

    # delete past slots

    TutorOfferSlots.objects.filter(start_recurr__isnull=True).filter(start_time__lt=timezone.now()).delete()
    TutorOfferSlots.objects.filter(end_recurr__lt=timezone.now()).delete()
    # TutionSlotBooking.objects.filter(start_time__lt=timezone.now()).delete()

    context_dict['tutor_offer'] = tutor_offer
    context_dict['booked_slots'] = booked_slots_list
    context_dict['offer_slot_list'] = available_slots_list
    return render(request, 'youtor_app/slot_scheduling.html', context_dict)

@login_required
def upcoming_bookings(request):
    context_dict = {}

    try:
        tutor_offer = TutorOffers.objects.get(user_id=request.user.id)
        if tutor_offer:
            offer_slot_list = TutorOfferSlots.objects.filter(tutor_offers_id=tutor_offer.id)

            available_slots_list = []
            for slot in offer_slot_list:
                print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
                available_slots_list.append({
                    'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                    'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                    'id': slot.id
                })

    except TutorOffers.DoesNotExist as e:
        tutor_offer = None
        available_slots_list = None
        print("Exception Occured :", e)


    # fetch booked slots on available slots if any
    try:
        booked_slots = TutionSlotBooking.objects.filter(tutor_id=request.user.id, start_time__gt=timezone.now())

        booked_slots_list = []
        for slot in booked_slots:
            print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
            booked_slots_list.append({
                'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                'id': slot.id
            })
    except Exception as e:
        booked_slots_list = None
        print("Exception Occured in fetching booked slots:", e)

    # delete past slots

    TutorOfferSlots.objects.filter(start_time__lt=timezone.now()).delete()
    # TutionSlotBooking.objects.filter(start_time__lt=timezone.now()).delete()

    context_dict['tutor_offer'] = tutor_offer
    context_dict['booked_slots'] = booked_slots_list
    context_dict['offer_slot_list'] = available_slots_list
    return render(request, 'youtor_app/booking_upcoming.html', context_dict)

@login_required
def past_bookings(request):
    context_dict = {}

    try:
        tutor_offer = TutorOffers.objects.get(user_id=request.user.id)
        if tutor_offer:
            offer_slot_list = TutorOfferSlots.objects.filter(tutor_offers_id=tutor_offer.id)

            available_slots_list = []
            for slot in offer_slot_list:
                print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
                available_slots_list.append({
                    'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                    'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                    'id': slot.id
                })

    except TutorOffers.DoesNotExist as e:
        tutor_offer = None
        available_slots_list = None
        print("Exception Occured :", e)


    # fetch booked slots on available slots if any
    try:
        booked_slots = TutionSlotBooking.objects.filter(tutor_id=request.user.id, start_time__gt=timezone.now())

        booked_slots_list = []
        for slot in booked_slots:
            print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
            booked_slots_list.append({
                'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                'id': slot.id
            })
    except Exception as e:
        booked_slots_list = None
        print("Exception Occured in fetching booked slots:", e)

    # delete past slots

    TutorOfferSlots.objects.filter(start_time__lt=timezone.now()).delete()
    # TutionSlotBooking.objects.filter(start_time__lt=timezone.now()).delete()

    context_dict['tutor_offer'] = tutor_offer
    context_dict['booked_slots'] = booked_slots_list
    context_dict['offer_slot_list'] = available_slots_list
    return render(request, 'youtor_app/booking_past.html', context_dict)


@login_required
def create_event(request):
    if request.method == 'POST':
        is_recur = request.POST.get('recur')
        print(request.POST)
        if is_recur == 'true':
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            day_of_week = request.POST.get('day_of_week')
            offer_id = request.POST.get('offer_id')
            time_format = '%H:%M'
            date_format = '%Y-%m-%d'
            start_time = dt.datetime.strptime(start_time, time_format)
            end_time = dt.datetime.strptime(end_time, time_format)
            start_date = dt.datetime.strptime(start_date, date_format)
            end_date = dt.datetime.strptime(end_date, date_format)
            aware_start_time = pytz.utc.localize(start_time)
            aware_end_time = pytz.utc.localize(end_time)
            aware_start_date = pytz.utc.localize(start_date)
            aware_end_date = pytz.utc.localize(end_date)
            try:
                new_slot = TutorOfferSlots.objects.create(
                    tutor_offers_id = offer_id,
                    day = day_of_week,
                    end_time = aware_end_time, 
                    start_time = aware_start_time,
                    start_recurr = aware_start_date,
                    end_recurr = aware_end_date
                )
                print('here')
                new_slot = {'start_time':new_slot.start_time, 'end_time':new_slot.end_time, 'id':new_slot.id}

                return redirect('/schedule')
            except Exception as err:
                print("\n\nException Occured: ", err)
                return JsonResponse({'status': 500, 'message': 'error', 'success': False})



        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        tutor_offer_id = request.POST.get('offer_id')
        offer_slot_id = request.POST.get('slot_id')
        day = request.POST.get('day_of_week')
        is_created = request.POST.get('created')
        

        date_format = '%a, %d %b %Y %H:%M:%S %Z'
        unaware_start_time = dt.datetime.strptime(start_time, date_format)
        aware_start_time = pytz.utc.localize(unaware_start_time)

        unaware_end_time = dt.datetime.strptime(end_time, date_format)
        aware_end_time = pytz.utc.localize(unaware_end_time)

        print("offer_slot_id:", offer_slot_id)
        print("is_created:", is_created)
        print(request.POST)
        try:
            if offer_slot_id and is_created == 'false':
                new_slot = TutorOfferSlots.objects.filter(id=offer_slot_id).update(
                    day=day, end_time=aware_end_time, start_time=aware_start_time)
            elif is_created == 'true':
                new_slot = TutorOfferSlots.objects.create(
                    tutor_offers_id=tutor_offer_id, day=day, end_time=aware_end_time, start_time=aware_start_time)

            new_slot = {'start_time':new_slot.start_time, 'end_time':new_slot.end_time, 'id':new_slot.id}

            return JsonResponse({'status': 200, 'new_slot': new_slot, 'success': True})
        except Exception as err:
            print("\n\nException Occured: ", err)
            return JsonResponse({'status': 500, 'message': 'error', 'success': False})


@login_required
def delete_events(request):
    if request.method == 'POST':
        offer_slot_id = request.POST.get('slot_id', None)
        offer_id = request.POST.get('offer_id', None)
        print("offer_slot_id: ", offer_slot_id)
        # Deleteing offer slot
        try:
            deleted_slot = TutorOfferSlots.objects.get(id=offer_slot_id)
            del_slot_id = deleted_slot.id
            deleted_slot.delete()
            return JsonResponse({'status': 200, 'slot_id': del_slot_id, 'success': True})
        except Exception as err:
            print("\n\nException Occured: ", err)
            return JsonResponse({'status': 500, 'message': 'Error', 'success': False})


# ------------------tutor views ends-------------------------


# Student related views

@login_required
def tutor_search_result(request):
    context_dict = {}
    if request.method == 'GET' and 'suggestion' in request.GET.keys():
        starts_with = request.GET['suggestion']
        search_by = request.GET['search_by']
        try:
            if search_by == 'name':
                tutorlist = tutor_search(starts_with)

            elif search_by == 'subject':
                tutorlist = tutor_search_subject(starts_with)

            elif search_by == 'tags':
                tutorlist = tutor_search_tags(starts_with)

            context_dict['all_offers'] = tutorlist
        except Exception as e:
            print("\nException occured while tutor search: ", e)

    else:
        tutorlist = TutorOffers.objects.all()
        context_dict['all_offers'] = tutorlist

    return render(request, 'youtor_app/offer_list.html', context_dict)


# search offer by name and bio
def tutor_search(suggestion=None):
    if suggestion:
        r1_list = TutorOffers.objects.filter(
            Q(user__first_name__icontains=suggestion)
            | Q(user__last_name__icontains=suggestion),
            status=1).order_by('user__first_name')

    elif suggestion == '':
        r1_list = TutorOffers.objects.filter(status=1)

    return r1_list

# search offer by tags
def tutor_search_tags(suggestion=None):
    if suggestion:
        r1_list = TutorOffers.objects.filter(
            tags__name__icontains=suggestion, status=1).order_by('tags__name')

    elif suggestion == '':
        r1_list = TutorOffers.objects.filter(status=1)

    return set(r1_list)


# search offer by subject
def tutor_search_subject(suggestion=None):
    if suggestion:
        subject_related_users = UserProfile.objects.filter(
            subject__subject_name__icontains=suggestion, role=1)

        data_list = []
        for offer in TutorOffers.objects.filter(status=1):
            for user_prof in subject_related_users:
                if offer.user_id == user_prof.user_id:
                    data_list.append(offer)
        # print("\n\n\n",type(data_list))
    elif suggestion == '':
        data_list = TutorOffers.objects.filter(status=1)
    # print("\n\n\n",set(data_list))
    return set(data_list)


# Search by price
def tutor_search_price(minv=None, maxv=None):
    r1_list = TutorOffers.objects.filter(status=1)
    r1_list = []
    if minv and maxv:
        min_if = minv
        max_if = maxv
        r1_list = TutorOffers.objects.filter(rate__range=(minv, maxv))
    else:
        r1_list = TutorOffers.objects.all()
    return r1_list


@login_required
def tutor_search_result_price(request):
    tutorlist = []
    try:
        if request.method == 'GET':
            if 'maxv' and 'minv' in request.GET.keys():
                max_val = request.GET['maxv']
                min_val = request.GET['minv']
                tutorlist = tutor_search_price(min_val, max_val)
    except Exception as e:
        print("Exception occured: ", e)

    return render(request, 'youtor_app/offer_list.html', {'all_offers': tutorlist})


@login_required
def tutor_detailed_view(request, slug):
    context_dict = {}

    # fetch tutor details for his profile
    user_profile = UserProfile.objects.get(slug=slug)

    try:
        tutor_offer = TutorOffers.objects.get(user_id=user_profile.user_id)
        if tutor_offer:
            offer_slot_list = TutorOfferSlots.objects.filter(tutor_offers_id=tutor_offer.id)

            available_slots_list = []
            for slot in offer_slot_list:
                print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
                available_slots_list.append({
                    'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                    'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                    'id': slot.id,
                    'tutor_offers_id':slot.tutor_offers_id,
                    'tutor_user_id': slot.tutor_offers.user_id
                })

    except TutorOffers.DoesNotExist as e:
        tutor_offer = None
        available_slots_list = None
        print("Exception Occured :", e)


    # fetch booked slots on available slots if any
    try:
        booked_slots = TutionSlotBooking.objects.filter(tutor_id=user_profile.user_id)

        booked_slots_list = []
        for slot in booked_slots:
            print("newTime:",slot.start_time.strftime("%Y-%m-%dT%H:%M"))
            booked_slots_list.append({
                'start_time':slot.start_time.strftime("%Y-%m-%dT%H:%M"),
                'end_time': slot.end_time.strftime("%Y-%m-%dT%H:%M"),
                'id': slot.id,
                'tutor_id': slot.tutor_id,
            })
    except Exception as e:
        booked_slots_list = None
        print("Exception Occured in fetching booked slots:", e)

    context_dict['tutor_offer'] = tutor_offer
    context_dict['booked_slots'] = booked_slots_list
    context_dict['offer_slot_list'] = available_slots_list
    context_dict['tutor_profile'] = user_profile

    return render(request, 'youtor_app/tutor_detailed_profile.html', context_dict)


# ------------------student views ends-------------------------

# Booking related views

@login_required
def proceed_to_checkout(request):
    if request.method == 'POST':
        tutor_user_id = request.POST.get('tutor_user_id', None)
        request.session['tutor_user_id'] = tutor_user_id
        selected_slots = json.loads(request.POST.get('selected_slots'))
        print(f"selected_slots:{selected_slots} - Type: {type(selected_slots)}")

        request.session['slots_to_book'] = selected_slots

    return JsonResponse({'status': 200, 'success': True})


def tz_aware_it(dt_obj):
    date_format = '%a, %d %b %Y %H:%M:%S %Z'
    unaware_dt = dt.datetime.strptime(dt_obj, date_format)
    aware_dt = pytz.utc.localize(unaware_dt)

    return aware_dt

@login_required
def process_tution_booking(request):
    context_dict = {}

    slots_to_book = request.session.get('slots_to_book')
    tutor_user_id = request.session.get('tutor_user_id', None)
    tutor_offer_instance = TutorOffers.objects.get(user_id=tutor_user_id)

    total_rate = 0.00
    for slot in slots_to_book:
        slot['start'] = tz_aware_it(slot['start'])
        slot['end'] = tz_aware_it(slot['end'])
        print(f"Slot: {slot['start']}, and it's Type: {type(slot['start'])}")

        # to get session duration
        sess_duration = slot['end'] - slot['start']
        sess_total_secs = int(sess_duration.total_seconds())
        hours, remainder = divmod(sess_total_secs, 60*60)
        minutes, seconds = divmod(remainder, 60)
        slot['session_duration'] = '{} hrs {} mins'.format(hours,minutes)

        slot['session_date'] = str(slot['start'].date())
        slot['session_timings'] = '{} to {}'.format(slot['start'].time(), slot['end'].time())

        # to get session rate
        sess_rate = (sess_duration/dt.timedelta(minutes=30)) * \
            float(tutor_offer_instance.rate)
        total_rate += sess_rate
        slot['session_rate'] = "{0:.2f}".format(sess_rate)
        slot['start'] = str(slot['start'])
        slot['end'] = str(slot['end'])

    # get total rate for all selected sessions
    total_rate = "{0:.2f}".format(total_rate)
    print("total_rate :", total_rate)
    print(f"\n\n NEW_SLOTs:{slots_to_book}\n\n")

    request.session['total_rate'] = total_rate
    request.session['to_pay'] = str(total_rate).replace('.', '')
    request.session['slots_to_book'] = slots_to_book

    context_dict['all_slots'] = slots_to_book
    context_dict['total_rate'] = total_rate
    context_dict['slot_details'] = tutor_offer_instance
    context_dict['key'] = settings.STRIPE_PUBLISHABLE_KEY

    return render(request, 'youtor_app/process_payment.html', context_dict)


@csrf_exempt
@login_required
def payment_done(request):
    context_dict = {}

    if request.method == 'POST':
        tutor_user_id = request.session.get('tutor_user_id', None)
        slots_to_book = request.session.get('slots_to_book', None)

        for slots in slots_to_book:
            print("Payment Done Slots:", slots)
        date_format = '%a, %d %b %Y %H:%M:%S %Z'
        start_time = request.session.get('session_start_time', None)
        unaware_start_time = dt.datetime.strptime(start_time, date_format)
        start_time = pytz.utc.localize(unaware_start_time)

        end_time = request.session.get('session_end_time', None)
        unaware_end_time = dt.datetime.strptime(end_time, date_format)
        end_time = pytz.utc.localize(unaware_end_time)

        print(f"payment_done>>>\n start_time: {start_time}\n type: {type(start_time)}\n")

        description = 'Tutor Slot Booking - {} - {}'.format(
            request.user.first_name, start_time.date())

        try: # try payment
            charge = stripe.Charge.create(
                amount=request.session.get('to_pay'),
                currency='CAD',
                description='Tutor Slot Booking nine',
                source=request.POST['stripeToken']
            )

        except Exception as e:
            print("Error occured while processing payment with Stripe: ", e)

        if charge.paid: # if payment success
            booking_slot_obj = TutionSlotBooking.objects.create(
                start_time = start_time,
                end_time = end_time,
                booking_date=dt.datetime.now(),
                booking_status=1,
                student_id=request.user.id,
                tutor_id=tutor_user_id,
                transaction_id=charge.id,
                total_session_amount=request.session.get('total_rate', None),
            )
            context_dict['booking_info'] = booking_slot_obj
            return render(request, 'youtor_app/payment_done.html', context_dict)

        else: # if payment fails
            booking_slot_obj = TutionSlotBooking.objects.create(
                start_time = slot_timing.start_time,
                end_time = slot_timing.end_time,
                booking_date=dt.datetime.now(),
                booking_status=2,
                student_id=request.user.id,
                tutor_id=tutor_user_id,
                transaction_id=charge.id,
                total_session_amount=request.session.get('total_rate', None),
            )
            context_dict['booking_info'] = booking_slot_obj
            return render(request, 'youtor_app/payment_cancelled.html', booking_slot_obj)

    return redirect('dashboard')


@csrf_exempt
@login_required
def payment_canceled(request):
    return render(request, 'youtor_app/payment_cancelled.html')




# ----------------------------
@login_required
def booking(request):
    context_dict = {}

    try:
        upcoming_booking_instance = TutionSlotBooking.objects.filter(tutor_id=request.user.id).order_by('-booking_date')
        print(upcoming_booking_instance)
    except Exception as e:
        print("No Bookings!:", e)
        upcoming_booking_instance = None

    context_dict['upcoming_bookings'] = upcoming_booking_instance
    # try:
    #     user_profile_instance = UserProfile.objects.filter(role=0)
    #     print("\n\n", user_profile_instance)
    # except UserProfile.DoesNotExist:
    #     user_profile_instance = None
    return render(request, 'youtor_app/booking_1.html', context_dict)

@login_required
def StudentBooking(request):
    context_dict = {}

    try:
        upcoming_booking_instance = TutionSlotBooking.objects.filter(student_id=request.user.id, start_time__gte=dt.datetime.today()).order_by('start_time')
        past_booking_instance = TutionSlotBooking.objects.filter(student_id=request.user.id, end_time__lte=dt.datetime.today()).order_by('start_time')
        print("\n\n\n\n",upcoming_booking_instance)
    except Exception as e:
        print("No Bookings!:", e)
        upcoming_booking_instance = None
        past_booking_instance = None

    context_dict['upcoming_bookings'] = upcoming_booking_instance
    context_dict['past_bookings'] = past_booking_instance
    return render(request, 'youtor_app/student_booking.html', context_dict)

@login_required
def UserReview(request):
    if request.method == 'POST':
        tb_id = request.POST.get('eventId')
        print(tb_id)
        try:
            tution_slote_booking = TutionSlotBooking.objects.get(id=tb_id)
        except Exception as e:       
            tution_slote_booking = None

        # TODO: This is common rating view, need to differentiate tutor & student rating view
        if tution_slote_booking:
            user_review = TutorReview()
            user_review.student_id = tution_slote_booking.student_id
            user_review.tutor_id = tution_slote_booking.tutor_id
            user_review.rating = request.POST['rating']
            user_review.review = request.POST['txt_review']
            user_review.booking_id = tb_id
            user_review.save()
            tution_slote_booking.tution_session_status = 1
            tution_slote_booking.save()
            return redirect('dashboard')
        else:
            error = "Something went wrong"
            return redirect('dashboard')

# ------------------booking views ends-------------------------

# ------------------ Star Rating ---------------------------
def TutorRate(request):
    tutor_rate = request.GET.get('stars_value')
    print("\n\n\n\n\n\n",tutor_rate)
    return HttpResponse('')

# ------------------ Star Dropdown Rating --------------------------- 
def TutorSearchRating(request):
    context_dict={}
    tutor_rating = request.GET.get('rating_val')
    tutor_ids = TutorReview.objects.all().values('tutor_id')
    
    result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(Avg('rating'))
    context_dict['average'] = result

    if tutor_rating == '5':
        result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(avg=Avg('rating')).filter(avg__gte=5)
        all_offers = TutorOffers.objects.filter(user_id=result[0][0])
        context_dict['all_offers'] = all_offers
    
    if tutor_rating == '4':
        result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(avg=Avg('rating')).filter(avg__gte=4.0,avg__lte=4.9)
        all_offers = TutorOffers.objects.filter(user_id=result[0][0])
        context_dict['all_offers'] = all_offers
    
    if tutor_rating == '3':
        result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(avg=Avg('rating')).filter(avg__gte=3.0,avg__lte=3.9)
        all_offers = TutorOffers.objects.filter(user_id=result[0][0])
        context_dict['all_offers'] = all_offers
    
    if tutor_rating == '2':
        result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(avg=Avg('rating')).filter(avg__gte=2.0,avg__lte=2.9)
        all_offers = TutorOffers.objects.filter(user_id=result[0][0])
        context_dict['all_offers'] = all_offers
    
    if tutor_rating == '1':
        result = TutorReview.objects.filter(tutor__id__in=tutor_ids).values_list('tutor__id').annotate(avg=Avg('rating')).filter(avg__gte=1.0,avg__lte=1.9)
        all_offers = TutorOffers.objects.filter(user_id=result[0][0])
        context_dict['all_offers'] = all_offers
    
    if tutor_rating == '':
        all_offers = TutorOffers.objects.filter(status=1)
        context_dict['all_offers'] = all_offers

    return render(request, 'youtor_app/offer_list.html', context_dict)

# ------------------ Sort By ---------------------------
def TutorSortBy(request):
    context_dict={}
    sort_val = request.GET.get('price_range_val')
    if sort_val == 'LTH':
        lth = TutorOffers.objects.all().order_by('rate')
        context_dict['all_offers'] = lth
    elif sort_val == 'HTL':
        htl = TutorOffers.objects.all().order_by('-rate')
        context_dict['all_offers'] = htl
    else:
        all_offers = TutorOffers.objects.filter(status=1)
        context_dict['all_offers'] = all_offers
    return render(request, 'youtor_app/offer_list.html', context_dict)