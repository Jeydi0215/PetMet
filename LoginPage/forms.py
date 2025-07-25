from django import forms
from django.contrib.auth.models import User
from adoption.models import PendingPetForAdoption, Admin, PetAdoptionTable, TrackUpdateTable
from django.contrib.auth.forms import UserCreationForm

ADOPTER_TYPE_CHOICES = [
    ('Individual', 'Individual'),
    ('Family', 'Family'),
    ('Organization', 'Organization')
]

LIVING_SITUATION_CHOICES = [
    ('Apartment', 'Apartment'),
    ('House', 'House'),
    ('Condo', 'Condo')
]

class AdminSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Add email field
    is_staff = forms.BooleanField(required=False, initial=True)  # Checkbox to set user as admin

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_staff']  # Include is_staff in the fields

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Admin
        fields = ('username', 'email', 'role', 'status')

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)


class PetAdoptionForm(forms.ModelForm):
    adoption_id = forms.CharField(max_length=10, required=False)

    class Meta:
        model = PendingPetForAdoption
        fields = ('name', 'animal_type', 'breed', 'color', 'gender', 'age', 'location', 'additional_details', 'img')

    def __init__(self, *args, **kwargs):
        super(PetAdoptionForm, self).__init__(*args, **kwargs)
        self.fields['adoption_id'].initial = self.generate_id()

    def generate_id(self):
        last_id = PendingPetForAdoption.objects.all().order_by('-adoption_id').first()
        if last_id and last_id.adoption_id:  # Add this check
            return str(int(last_id.adoption_id) + 1).zfill(6)
        else:
            return '000001'

    def save(self, commit=True):
        instance = super(PetAdoptionForm, self).save(commit=False)
        instance.adoption_id = self.cleaned_data['adoption_id']
        if commit:
            instance.save()
        return instance
    
class PetAdoptionFormRequest(forms.ModelForm):
    class Meta:
        model = PetAdoptionTable
        fields = (
            'first_name', 
            'last_name', 
            'contact_number', 
            'address', 
            'adopter_type', 
            'living_situation', 
            'previous_pet_experience', 
            'owns_other_pets', 
            'facebook_profile_link',
            'id_type',  # Add ID type to the fields
            'id_number'  # Add ID number to the fields
        )
        widgets = {
            'previous_pet_experience': forms.Textarea(attrs={'rows': 5, 'cols': 30}),
            'owns_other_pets': forms.TextInput(attrs={'rows': 4, 'cols': 30}),
            'id_number': forms.TextInput(attrs={'placeholder': 'Enter your ID number'}),  # Optional placeholder
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'This field is required.')
        return cleaned_data
    
class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = Admin
        fields = ('username', 'email')

class TrackUpdateForm(forms.ModelForm):
    class Meta:
        model = TrackUpdateTable
        fields = [
            'living_situation',
            'housing_type',
            'behavioral_changes',
            'health_issues',
            'notes',
            'photos',
        ]

class PendingPetForAdoptionForm(forms.ModelForm):
    class Meta:
        model = PendingPetForAdoption
        fields = ['name', 'animal_type', 'location', 'breed', 'color', 'gender', 'age', 'additional_details', 'img']
        widgets = {
            'additional_details': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'img': 'Upload Image',
        }