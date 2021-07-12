from django import template
from youtor_app.models import UserProfile, User

register = template.Library()

@register.simple_tag
def get_profile(offer):
    user_instance = User.objects.get(id=offer.user_id)
    tutor_instance = UserProfile.objects.get(user_id=user_instance.id)

    tutor_details = {
        'id':user_instance.id,
        'name': user_instance.first_name + ' ' + user_instance.last_name,
        'contact_no': tutor_instance.contact,
        'email': user_instance.email,
        'major': tutor_instance.major,
        'profile_img': tutor_instance.profile_image,
        'year_of_study': tutor_instance.year_of_study,
        'slug': tutor_instance.slug,
    }
    return tutor_details

@register.simple_tag
def get_user_type(user):
    user_profile_instance = UserProfile.objects.get(user_id=user.id)

    if user_profile_instance.role == 0:
        user_type = 'Student'
    elif user_profile_instance.role == 1:
        user_type = 'Tutor'
        
    return user_type
