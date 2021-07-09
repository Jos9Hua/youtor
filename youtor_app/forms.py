from django import forms

from django.contrib.auth.models import User
from .models import UserProfile, year_choices, TutorOffers, Tag
from phonenumber_field.formfields import PhoneNumberField


class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta():
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "password and confirm_password does not match"
            )

    def clean_email(self):
        # Get the email
        email = self.cleaned_data.get('email')

        # Check to see if any users already exist with this email as a username.
        try:
            match = User.objects.get(email=email)
        except User.DoesNotExist:
            # Unable to find a user, this is fine
            return email

        # A user was found with this as a username, raise an error.
        raise forms.ValidationError('This email address is already in use.')


class UserProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    contact = PhoneNumberField(label='Phone Number', required=True)
    year_of_study = forms.TypedChoiceField(label='Year of Study', coerce=int, choices=year_choices)
    major = forms.CharField(label='Major ', max_length=100, required=True)
    profile_image = forms.ImageField(label='Profile Image', required=False)

    class Meta():
        model = UserProfile
        exclude = ('confirmed', 'user', 'subject', 'slug')
        Widget = {'Role': forms.ModelChoiceField}

    def clean_contact(self):
        return self.cleaned_data.get('contact')



class UserEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)

    class Meta():
        model = User
        fields = ('first_name', 'last_name',)


class UserProfileEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserProfileEditForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    contact = PhoneNumberField(label='Phone Number', required=False)
    year_of_study = forms.TypedChoiceField(label='Year of Study', coerce=int, choices=year_choices)
    major = forms.CharField(label='Major ', max_length=100)
    profile_image = forms.ImageField(label='Profile Image', required=False)

    class Meta():
        model = UserProfile
        exclude = ('confirmed', 'user', 'role', 'subject', 'slug')

    def clean_contact(self):
        return self.cleaned_data.get('contact')



class TutorOffersForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TutorOffersForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    rate = forms.DecimalField(max_digits=5, decimal_places=2, help_text='Rates are in CA$ per hour.', required=False)
    bio = forms.Textarea() #help_text='You can describe yourself, mention your skills. Describe what you will be offering in this tution session.'
    transcript = forms.FileField(label="Upload your transcript file", help_text='Upload your transcript for verification.', required=False)

    class Meta():
        model = TutorOffers
        exclude = ('status', 'user', 'tags',)


class TagForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    class Meta():
        model = Tag
        fields = ('name', )