from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, admin
from django.contrib.auth.models import User, auth
from django.contrib.auth import login
from adoption.models import PendingPetForAdoption, Admin, PetAdoptionTable, TrackUpdateTable, Notification, AdminUser
from django.core.paginator import Paginator
from .forms import PetAdoptionForm, SignUpForm, LoginForm, PetAdoptionFormRequest, AdminProfileForm, TrackUpdateForm, PendingPetForAdoptionForm,AdminSignupForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.hashers import make_password
from django.urls import reverse_lazy, reverse
from django.views.generic import View
from django.contrib.auth import login as auth_login, authenticate
from django.utils import timezone
from django.contrib.auth.views import LogoutView
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import BasePermission
from rest_framework import authentication
import spacy
import pytz
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# Create your views here.
import calendar

# Get the month names
months = list(calendar.month_name)


def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'adminuser'):
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to access this page.")
    return _wrapped_view

# Accessing the first month
print(months[1])  # Output: January
# views.py
from rest_framework import viewsets
from adoption.models import Admin, PetAdoptionRequestTable, PetAdoptionTable, PendingPetForAdoption
from adoption.serializers import AdminSerializer, PetAdoptionRequestTableSerializer, PetAdoptionTableSerializer, PendingPetForAdoptionSerializer, TrackUpdateTableSerializer, UpdatePendingPetSerializer, NotificationSerializer

class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer

class PetAdoptionRequestTableViewSet(viewsets.ModelViewSet):
    queryset = PetAdoptionRequestTable.objects.all()
    serializer_class = PetAdoptionRequestTableSerializer

class PetAdoptionTableViewSet(viewsets.ModelViewSet):
    queryset = PetAdoptionTable.objects.all()
    serializer_class = PetAdoptionTableSerializer

class PendingPetForAdoptionViewSet(viewsets.ModelViewSet):
    queryset = PendingPetForAdoption.objects.all()
    serializer_class = PendingPetForAdoptionSerializer


from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from adoption.serializers import PendingPetForAdoptionSerializer

class PendingPetForAdoptionViewSet(viewsets.ModelViewSet):
    queryset = PendingPetForAdoption.objects.all()  # Ensure this line is present
    serializer_class = PendingPetForAdoptionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # Call the superclass's get_queryset method
        adoption_status = self.request.query_params.get('adoption_status', None)
        if adoption_status is not None:
            queryset = queryset.filter(adoption_status=adoption_status)
        return queryset
    
def landing(request):
    return render(request, 'landing.html')  # Ensure 'landing.html' is the correct path

def mobileTermsandConsitions(request):
    return render(request, 'terms_conditions.html')  # Ensure 'landing.html' is the correct path

from rest_framework import status
@api_view(['POST'])
def create_adoption_request(request):
    data = request.data
    pet_id = data.get('pet')  # This should match the key you're sending from the frontend
    user_id = data.get('user')
    contact_number = data.get('contact_number')
    address = data.get('address')
    adopter_type = data.get('adopter_type')
    living_situation = data.get('living_situation')
    previous_pet_experience = data.get('previous_pet_experience')
    owns_other_pets = data.get('owns_other_pets')
    facebook_profile_link = data.get('facebook_profile_link')  # New field
    first_name = data.get('firstname')  # New field
    last_name = data.get('lastname')  # New field

    if not pet_id:
        return Response({"error": "pet_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Create the adoption request
    try:
        # Create the adoption request
        adoption_request = PetAdoptionTable.objects.create(
            pet_id=pet_id,
            user_id=user_id,
            contact_number=contact_number,
            address=address,
            adopter_type=adopter_type,
            living_situation=living_situation,
            previous_pet_experience=previous_pet_experience,
            owns_other_pets=owns_other_pets,
            facebook_profile_link=facebook_profile_link,  # Include the new field
            first_name=first_name,  # Include first_name
            last_name=last_name,  # Include last_name
            # Other fields...
        )

        # Find the pet owner using the pet_id
        pet = PendingPetForAdoption.objects.filter(id=pet_id).first()  # Adjust this if your pet model is different
        if pet:
            pet_owner_id = pet.user_id  # Assuming user_id is the owner of the pet

            # Create a notification for the pet owner
            Notification.objects.create(
                user_id=pet_owner_id,
                message=f"An adoption request for your pet (Name: {pet.name}) has been submitted."
            )

        # Create a notification for the user who submitted the request
        Notification.objects.create(
            user_id=user_id,
            message=f"Adoption request for pet Name {pet.name} has been submitted successfully."
        )

        return Response({"message": "Adoption request created"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def RequestAdoptionRequestList(request):
    user_id = request.GET.get('userId')  # Get the user ID from query parameters
    if not user_id:
        return Response({"error": "User  ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch pet IDs associated with the user from PendingPetForAdoption
    pending_pets = PendingPetForAdoption.objects.filter(user_id=user_id)
    pet_ids = pending_pets.values_list('id', flat=True)  # Get a list of pet IDs

    if not pet_ids:
        return Response({"message": "No pending pets found for this user."}, status=status.HTTP_404_NOT_FOUND)

    # Fetch adoption requests based on pet IDs and check for pending or review status
    adoption_requests = PetAdoptionTable.objects.filter(
        pet_id__in=pet_ids,
        adoption_request_status__in=['pending', 'review']  # Check for both 'pending' and 'review' statuses
    )

    # Serialize the data (assuming you have a serializer set up)
    serializer = PetAdoptionTableSerializer(adoption_requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

class PetCreateView(generics.CreateAPIView):
    queryset = PendingPetForAdoption.objects.all()
    serializer_class = PendingPetForAdoptionSerializer
    permission_classes = [IsAuthenticated]  # Require authentication

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PostPendingPetViewSet(viewsets.ViewSet):
    def list(self, request):
        user_id = request.query_params.get('user_id')

        if not user_id:
            return Response({'error': 'User  ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pets = PendingPetForAdoption.objects.filter(user_id=user_id)  # Adjust field name as necessary
            serializer = PendingPetForAdoptionSerializer(pets, many=True)

            return Response({
                'count': len(pets),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print('Error fetching pending pets:', e)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PendingPetList(generics.ListAPIView):
    serializer_class = PendingPetForAdoptionSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('userId', None)
        if user_id is not None:
            return PendingPetForAdoption.objects.filter(user_id=user_id)
        return PendingPetForAdoption.objects.none()
    
import logging

logger = logging.getLogger(__name__)

from rest_framework import serializers
def pet_detail_view(request, pk):
    pet = get_object_or_404(PendingPetForAdoption, pk=pk)
    return render(request, 'admin_pet_detail.html', {'pet': pet})

def approve_pet(request, pk):
    pet = get_object_or_404(PendingPetForAdoption, pk=pk)
    pet.adoption_status = 'approved'
    pet.save()
    return redirect(reverse('pending_pets'))

@login_required
def adopt_pet(request, pk):
    pet = PendingPetForAdoption.objects.get(pk=pk)
    if request.method == 'POST':
        form = PetAdoptionFormRequest(request.POST)
        print("Form data:", request.POST)  # Print the form data
        if form.is_valid():
            print("Form is valid")  # Print if the form is valid
            adoption_request = PetAdoptionTable()  # Create an instance of PetAdoptionTable
            adoption_request.pet_id = pet.id  # Assign the id of the pet to the pet_id field
            adoption_request.user_id = request.user.id  # Assign the id of the user to the user_id field
            adoption_request.adoption_status = 'pending'  # Set the adoption status to 'pending'
            adoption_request.first_name = form.cleaned_data['first_name']  # Save first name
            adoption_request.last_name = form.cleaned_data['last_name']  # Save last name
            adoption_request.contact_number = form.cleaned_data['contact_number']
            adoption_request.address = form.cleaned_data['address']
            adoption_request.adopter_type = form.cleaned_data['adopter_type']
            adoption_request.living_situation = form.cleaned_data['living_situation']
            adoption_request.previous_pet_experience = form.cleaned_data['previous_pet_experience']
            adoption_request.owns_other_pets = form.cleaned_data['owns_other_pets']
            adoption_request.facebook_profile_link = form.cleaned_data['facebook_profile_link']
            adoption_request.request_date_time = timezone.now().astimezone(pytz.timezone('Asia/Manila'))  # Save the current date and time in the Philippines timezone
            
            try:
                adoption_request.save()  # Save the instance to the database
                print("Adoption request saved successfully")  # Print if the adoption request is saved successfully
                
                # Notify the pet owner
                pet_owner = PendingPetForAdoption.objects.get(pk=pet.id).user  # Get the owner of the pet
                if pet_owner:
                    # Create a notification for the pet owner
                    notification_message = f"There is a new adoption request for your pet: {pet.name}."
                    Notification.objects.create(user=pet_owner, message=notification_message)
                    
                    # Optionally, you can send an email notification here
                    # send_mail(
                    #     'New Adoption Request',
                    #     notification_message,
                    #     'from@example.com',
                    #     [pet_owner.email],
                    #     fail_silently=False,
                    # )
                    
                    messages.success(request, f"Notification sent to {pet_owner.username} about the adoption request for {pet.name}.")
            except Exception as e:
                print("Error saving adoption request:", e)  # Print any errors when saving the adoption request
                messages.error(request, "There was an error saving your adoption request.")
            return redirect('homepage')  # redirect to a success page
        else:
            print("Form is not valid")  # Print if the form is not valid
            return render(request, 'adoption_form.html', {'form': form, 'pet': pet})
    else:
        form = PetAdoptionFormRequest()
    return render(request, 'adoption_form.html', {'form': form, 'pet': pet})

def list_adoption_requests(request):
    if request.user.is_authenticated:
        adoption_requests = PetAdoptionTable.objects.filter(user_id=request.user.id)
        adoption_request_list = []
        for adoption_request in adoption_requests:
            pending_pet = PendingPetForAdoption.objects.filter(id=adoption_request.pet_id).first()
            if pending_pet:
                adoption_request_list.append({
                    'id': pending_pet.id,
                    'name': pending_pet.name,
                    'adoption_request_id': adoption_request.id,
                    'adoption_request_status': adoption_request.adoption_request_status
                })
        return render(request, 'adoption_requests.html', {'adoption_requests': adoption_request_list})
    else:
        return redirect('homepage')  # or any other page you want to redirect to
    
def view_adoption_request(request, request_id):
    adoption_request = PetAdoptionTable.objects.get(id=request_id)
    pending_pet = PendingPetForAdoption.objects.get(id=adoption_request.pet_id)
    return render(request, 'adoption_request_detail.html', {'adoption_request': adoption_request, 'pending_pet': pending_pet})

def post_adoption_edit(request, id):
    pet = get_object_or_404(PendingPetForAdoption, id=id)
    
    if request.method == 'POST':
        form = PendingPetForAdoptionForm(request.POST, request.FILES, instance=pet)  # Include request.FILES
        if form.is_valid():
            form.save()
            return redirect('adoption_table')  # Redirect to the detail view after saving
    else:
        form = PendingPetForAdoptionForm(instance=pet)

    return render(request, 'post_edit_adoption.html', {'form': form, 'pet': pet})

def post_adoption_delete(request, id):
    pet = get_object_or_404(PendingPetForAdoption, id=id)
    
    if request.method == 'POST':
        try:
            # Attempt to find the related adoption record
            adoption_record = PetAdoptionTable.objects.get(pet_id=pet.id)
            # Update the adoption_request_status
            adoption_record.adoption_request_status = 'Pet is deleted'
            adoption_record.save()
            print(f"Updated adoption record for pet {pet.name} to 'Pet is deleted'.")
        except PetAdoptionTable.DoesNotExist:
            print(f"No adoption record found for pet {pet.name}.")
        
        # Delete the pet from the PendingPetForAdoption model
        pet.delete()
        print(f"Deleted pet: {pet.name}.")
        
        # Redirect to the adoption list after deletion
        return redirect('adoption_table')

    # Render the confirmation template if the request is not POST
    return render(request, 'post_confirm_delete.html', {'pet': pet})

@login_required
def adoption_table_view(request):
    user_id = request.user.id
    adoptions = PendingPetForAdoption.objects.filter(user_id=user_id)
    return render(request, 'adoption_table.html', {'adoptions': adoptions})

def adoption_detail_view(request, pk):
    adoption = PendingPetForAdoption.objects.get(pk=pk)
    return render(request, 'adoption_detail.html', {'adoption': adoption})

def logout_admin(request):
    # Log out the user
    logout(request)
    # Optionally, you can add a message to inform the user
    messages.success(request, "You have been logged out successfully.")
    # Redirect to a desired page after logout
    return redirect('admin_home')  # Change 'landing' to the name of the URL you want to redirect to

@login_required
def view_requests(request):
    user_requests = PendingPetForAdoption.objects.filter(user_id=request.user.id)
    adoption_requests = PetAdoptionTable.objects.filter(pet_id__in=user_requests.values_list('id', flat=True))
    request_list = []
    for req in adoption_requests:
        pet = PendingPetForAdoption.objects.get(id=req.pet_id)
        request_list.append({
            'id': req.id,
            'pet_name': pet.name,
            'pet_animal_type': pet.animal_type,
            'adoption_request_status': req.adoption_request_status,
        })
    return render(request, 'requests.html', {'requests': request_list})

from rest_framework.exceptions import NotFound

class ReactAdoptedPetsView(generics.ListAPIView):
    serializer_class = PendingPetForAdoptionSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']  # Get user_id from the URL
        logger.debug(f"Retrieved user ID from URL: {user_id}")

        queryset = PendingPetForAdoption.objects.filter(
            user_id=user_id,  # Filter by user_id
            adoption_status__in=['Pet_is_already_adopt', 'Pet is already adopt']
        )

        logger.debug(f"Queryset for user ID {user_id}: {queryset}")

        return queryset

class ReactAdoptPetDetailView(generics.RetrieveAPIView):
    queryset = PendingPetForAdoption.objects.all()
    serializer_class = PendingPetForAdoptionSerializer

    def get(self, request, *args, **kwargs):
        pet_id = kwargs.get('pk')
        try:
            # Retrieve the pet object using the primary key (pk)
            pet = self.get_object()
            
            # Filter the PetAdoptionTable for the matching pet_id
            adoption_details = PetAdoptionTable.objects.filter(pet_id=pet.id).first()

            # Initialize response data
            response_data = {
                'pet': PendingPetForAdoptionSerializer(pet).data,
                'adoption_details': None,
                'user_details': None,
                'follow_up_dates': None,  # Initialize follow_up_dates
                'reports': []  # Initialize reports
            }

            # Check if adoption details exist
            if adoption_details:
                # Check the adoption_request_status
                if adoption_details.adoption_request_status in ['approved', 'adopted']:
                    # Retrieve user details using the user_id from adoption_details
                    user = User.objects.filter(id=adoption_details.user_id).first()
                    user_data = {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                    } if user else None

                    response_data['adoption_details'] = PetAdoptionTableSerializer(adoption_details).data
                    response_data['user_details'] = user_data  # Include user details in the response

                    # Fetch follow-up dates from TrackUpdateTable
                    follow_up_records = TrackUpdateTable.objects.filter(
                        pet_adoption_request_id=adoption_details.id
                    ).order_by('followup_date')

                    if follow_up_records.exists():
                        # Get the first followup_date
                        first_followup_date = follow_up_records.first().followup_date
                        follow_up_dates = []

                        # Generate follow-up dates for the next six months
                        for i in range(6):
                            follow_up_dates.append(first_followup_date + timedelta(days=i * 30))  # Approximate month as 30 days

                        response_data['follow_up_dates'] = follow_up_dates
                    else:
                        response_data['follow_up_dates'] = 'No records yet'

                    # Fetch reports related to the pet adoption
                    reports = TrackUpdateTable.objects.filter(pet_adoption_request_id=adoption_details.id)
                    response_data['reports'] = [
                        {
                            'id': report.id,
                            'date': report.followup_date,
                            'description': report.notes,
                            'living_situation': report.living_situation,
                            'housing_type': report.housing_type,
                            'behavioral_changes': report.behavioral_changes,
                            'health_issues': report.health_issues,
                            'photos': report.photos.url if report.photos else None  # Handle binary data
                        } for report in reports
                    ]

            logger.debug("Response Data: %s", response_data)  # Log the response data
            return Response(response_data, status=status.HTTP_200_OK)

        except PendingPetForAdoption.DoesNotExist:
            return Response({'error': 'Pet not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error("An error occurred: %s", str(e))
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.permissions import AllowAny  # Import AllowAny
class ReactCustomUserDetailView(generics.RetrieveUpdateAPIView):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer

    def get_permissions(self):
        # Allow anyone to access both GET and PUT requests
        return [AllowAny()]

    def get_object(self):
        try:
            return self.get_queryset().get(pk=self.kwargs['pk'])
        except Admin.DoesNotExist:
            raise NotFound("User  not found")  # Use DRF's NotFound exception for consistency

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)  # Return validation errors

class ReactCreateUserView(APIView):
    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)  # Print out the serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import date
@api_view(['POST'])
def react_add_report(request):
    if request.method == 'POST':
        serializer = TrackUpdateTableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ReactTrackUpdateList(generics.ListAPIView):
    serializer_class = TrackUpdateTableSerializer

    def get_queryset(self):
        pet_adoption_request_id = self.request.query_params.get('pet_adoption_request_id', None)
        if pet_adoption_request_id is not None:
            return TrackUpdateTable.objects.filter(pet_adoption_request_id=pet_adoption_request_id)
        return TrackUpdateTable.objects.none()  # Return an empty queryset if no ID is provided
        
class UpdatePendingPetView(generics.UpdateAPIView):
    queryset = PendingPetForAdoption.objects.all()
    serializer_class = UpdatePendingPetSerializer  # Use the new serializer

    def update(self, request, *args, **kwargs):
        partial = True  # Allow partial updates
        instance = self.get_object()
        print("Incoming data:", request.data)  # Log incoming data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)  # Log validation errors
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
    
@api_view(['DELETE'])
def delete_pending_pet(request, post_id):
    try:
        post = PendingPetForAdoption.objects.get(id=post_id)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  # No content to return after deletion
    except PendingPetForAdoption.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

def view_request(request, request_id):
    # Retrieve the adoption request using the provided request_id
    req = get_object_or_404(PetAdoptionTable, pk=request_id)
    
    # Get the first name and last name directly from the adoption request
    user_first_name = req.first_name
    user_last_name = req.last_name
    
    # Pass the request and user details to the template
    return render(request, 'request_detail.html', {
        'request': req,
        'user_first_name': user_first_name,
        'user_last_name': user_last_name,
    })
def update_status(request, request_id, new_status):
    # Get the request object or return a 404 if not found
    req = get_object_or_404(PetAdoptionTable, pk=request_id)

    # Update the status of the request
    req.adoption_request_status = new_status

    # Set the approval date/time if the status is approved
    if new_status == 'approved':
        req.approval_date_time = timezone.now()  # Set current time as approval date
        # Notify the user about the reporting requirement
        message = "You need to report for 15 days starting from the approval date."
        messages.info(request, message)  # Pass the message to the next view

        # Create a notification for the user
        Notification.objects.create(
            user=req.user,  # Assuming you have a user field in your PetAdoptionTable
            message=message,
            created_at=timezone.now()
        )

        # Retrieve the pet_id from the request
        pet_id = req.pet_id  # Assuming pet_id is a field in PetAdoptionTable

        # Check if the pet exists in PendingPetForAdoption
        pending_pet = PendingPetForAdoption.objects.filter(id=pet_id).first()
        if pending_pet:
            # Update the adoption status to indicate the pet is already adopted
            pending_pet.adoption_status = 'Pet is already adopted'
            pending_pet.save()  # Save the changes to the database

        # Call the new function to update other requests
        update_other_requests(pet_id)

    elif new_status == 'rejected':
        req.approval_date_time = None  # Clear approval date if rejected

    # Save the changes to the PetAdoptionTable
    req.save()

    # Redirect to the view requests page or wherever you want to go after updating
    return redirect('view_requests')  # Make sure 'view_requests' is a valid URL name

def update_other_requests(pet_id):
    # Filter PetAdoptionTable for requests with the same pet_id and status 'pending' or 'deny'
    other_requests = PetAdoptionTable.objects.filter(pet_id=pet_id, adoption_request_status__in=['pending', 'deny'])
    for other_request in other_requests:
        # Update the adoption status to indicate the pet is already adopted
        other_request.adoption_request_status = 'Pet is already adopted'
        other_request.save()  # Save the changes to the database

                                                   
def admin_report_detail(request, report_id):
    report = get_object_or_404(TrackUpdateTable, id=report_id)
    return render(request, 'admin_report_detail.html', {'report': report})

  # Ensure only logged-in users can access this view
def admin_home(request):
    return render(request, 'admin_home.html')  # Render the admin home template

def home(request):
    return render(request, 'home.html')


@csrf_exempt  # Temporarily disable CSRF for debugging
def admin_login(request):
    if request.method == 'POST':
        print("CSRF Token from request:", request.POST.get('csrfmiddlewaretoken'))
        print("CSRF Token from session:", request.META.get('CSRF_COOKIE'))
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', 'homepage_admin')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            print("Invalid login attempt.")
    
    return render(request, 'admin_home.html')

@login_required
@admin_required
def admin_homepage(request):
    print("Current user:", request.user)  # Debugging line
    print("Is user authenticated?", request.user.is_authenticated)  # Check if user is authenticated
    print("Session data:", request.session.items())  # Log session data

    # Get the current time in the Philippines
    philippines_tz = pytz.timezone('Asia/Manila')
    philippines_time = timezone.now().astimezone(philippines_tz).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, 'admin_homepage.html', {
        'user': request.user,
        'philippines_time': philippines_time,
    })

def admin_signup(request):
    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            # Create the user
            user = form.save(commit=False)  # Don't save yet
            user.is_staff = form.cleaned_data.get('is_staff')  # Set is_staff based on form input
            user.save()  # Now save the user
            
            # Create an AdminUser  instance
            AdminUser .objects.create(user=user)  # Create the associated AdminUser 
            
            messages.success(request, 'User  created successfully! You can now log in.')
            return redirect('admin_home')  # Redirect to the login page after successful signup
    else:
        form = AdminSignupForm()
    
    return render(request, 'admin_signup.html', {'form': form})

def admin_approved_pet(request):
    # Query the PendingPetForAdoption model for pets with adoption_status 'approved'
    approved_pets_list = PendingPetForAdoption.objects.filter(adoption_status='approved')

    return render(request, 'admin_approved_pets.html', {
        'admin_approved_pet': approved_pets_list,  # Pass the list to the template
    })

import datetime
def AdoptionDetailView(request, id):
    # Step 1: Filter the PendingPetForAdoption model by the received id
    adoption = PendingPetForAdoption.objects.filter(id=id).first()

    if adoption:
        # Step 2: Get the adopter's details using the pet_id from the adoption
        adopter = PetAdoptionTable.objects.filter(pet_id=adoption.id).first()

        if adopter:  # Check if an adopter was found
            # Step 3: Get the track updates for the adoption using the adopter's id
            track_updates = TrackUpdateTable.objects.filter(pet_adoption_request_id=adopter.id)

            # Step 4: Calculate the tracking period
            tracking_period = []
            for update in track_updates:
                followup_date = update.followup_date
                tracking_period.append(followup_date)
                tracking_period.append(followup_date + datetime.timedelta(days=183))  # 6 months

            # Render the template with the retrieved data
            return render(request, 'admin_adoption_detail_history.html', {
                'adoption': adoption,
                'adopter': adopter,
                'track_updates': track_updates,
                'tracking_period': tracking_period,
            })
        else:
            # If no adopter is found, you might want to handle this case
            return render(request, '404.html')  # Return a 404 page if no adopter is found
    else:
        return render(request, '404.html')  # Return a 404 page if no adoption is found

def adopted_history(request):
    # Query the PendingPetForAdoption model for pets with adoption_status 'Pet is already adopted'
    adopted_pets_list = PendingPetForAdoption.objects.filter(adoption_status='Pet is already adopt')

    # Get the IDs of the adopted pets
    adopted_pet_ids = adopted_pets_list.values_list('id', flat=True)  # This will give you a flat list of IDs

    # Filter the PetAdoptionTable for approved requests matching the adopted pet IDs
    approved_adoptions = PetAdoptionTable.objects.filter(
        pet_id__in=adopted_pet_ids,
        adoption_request_status='approved'
    ).values('id', 'pet_id', 'approval_date_time')  # Retrieve id, pet_id, and approval_date_time

    # Render the template with the adopted pets, their IDs, and approved adoption details
    return render(request, 'adopted_history.html', {
        'adopted_pets': adopted_pets_list,  # Pass the list to the template
        'adopted_pet_ids': adopted_pet_ids,  # Pass the list of IDs to the template
        'approved_adoptions': approved_adoptions,  # Pass the approved adoption details
    })

def pending_pets(request):
    # Query the PendingPetForAdoption model for pets with adoption_status 'pending'
    pending_pets_list = PendingPetForAdoption.objects.filter(adoption_status='pending')

    return render(request, 'admin_pending_pets.html', {
        'pending_pets': pending_pets_list,  # Pass the list to the template
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User is authenticated, log them in
            auth_login(request, user)
            return redirect('homepage')  # Redirect to the homepage URL pattern
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'home.html')

@login_required
def homepage(request):
    username = request.user.username if request.user.is_authenticated else None
    notifications = Notification.objects.filter(user=request.user, is_read=False)  # Get unread notifications
    notifications_count = notifications.count()  # Count unread notifications

    # Get approved pets for the homepage (you can choose to paginate or not)
    pets = get_approved_pets()  # You can pass a page number if needed

    return render(request, 'homepage.html', {
        'username': username,
        'notifications': notifications,
        'notifications_count': notifications_count,
        'pets': pets,  # Pass the pets to the homepage context
    })

def get_approved_pets(page_number=None):
    # Filter pets where adoption_status is 'approved'
    pets = PendingPetForAdoption.objects.filter(adoption_status='approved')
    
    # Set up pagination if a page number is provided
    if page_number is not None:
        paginator = Paginator(pets, 10)  # Show 10 pets per page
        pets = paginator.get_page(page_number)
    
    return pets

def terms_conditions_view(request):
    return render(request, 'terms_conditions.html')

from django.shortcuts import render 
# Get an instance of a logger

logger = logging.getLogger(__name__)

def pet_list(request):
    page_number = request.GET.get('page')
    pets = get_approved_pets(page_number)

    # Log the number of pets found
    if pets:
        logger.info(f"Found {pets.paginator.count} approved pets for adoption.")
    else:
        logger.info("No approved pets found for adoption.")

    # Debug log to check if data is received
    logger.debug(f"Pets data received: {list(pets)}")  # Log the details of the pets found

    context = {
        'page_obj': pets,  # Pass the paginated pets to the template context
    }
    return render(request, 'article.html', context)

def add_pet(request):
    if request.method == 'POST':
        form = PendingPetForAdoptionForm(request.POST, request.FILES)  # Include request.FILES for image uploads
        if form.is_valid():
            # Create the PendingPetForAdoption instance
            pending_pet = form.save(commit=False)
            pending_pet.user = request.user  # Assign the user
            pending_pet.save()  # Save the instance to the database
            
            # Add a success message
            messages.success(request, 'Pet added successfully!')
            # Render the same template with the form and the success message
            form = PendingPetForAdoptionForm()  # Reset the form for a new entry
        else:
            # If the form is not valid, you can add an error message
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PendingPetForAdoptionForm()  # Create a new form instance for GET requests

    return render(request, 'add_pet.html', {'form': form})  # Render the template with the form

@login_required  # Require the user to be logged in to access this view
def reportadopted_pets(request):
    # Retrieve adopted pets for the logged-in user
    adopted_pets = PendingPetForAdoption.objects.filter(
        adoption_status__in=['Pet_is_already_adopt', 'Pet is already adopt'],
        user=request.user  # Check if the user ID matches
    )

    return render(request, 'adopted_pets.html', {'adopted_pets': adopted_pets})


@login_required
def reportRequestpet_detail(request, pet_id):
    # Get the pet object
    pet = get_object_or_404(PendingPetForAdoption, id=pet_id)

    # Filter the PetAdoptionTable for the given pet
    pet_adoption = PetAdoptionTable.objects.filter(pet=pet).first()  # Get the first matching adoption

    if pet_adoption:
        # Filter the TrackUpdateTable for the matching pet adoption request
        track_updates = TrackUpdateTable.objects.filter(pet_adoption_request=pet_adoption)

        # Check if there are no track updates
        if not track_updates.exists():
            Notification.objects.create(user=request.user, message="No track updates found for this pet.")
        
        # Determine the current month and year or use the provided month and year from the request
        current_month = int(request.GET.get('month', timezone.now().month))
        current_year = int(request.GET.get('year', timezone.now().year))

        # Calculate the starting date for the tracking period
        followup_dates = track_updates.values_list('followup_date', flat=True)
        if followup_dates:
            first_followup_date = min(followup_dates)
            tracking_start_date = first_followup_date  # Just use the first follow-up date as the starting point
        else:
            tracking_start_date = timezone.now()  # Fallback if no follow-up dates

        # Filter track updates for the selected month and year
        filtered_updates = track_updates.filter(
            followup_date__year=current_year,
            followup_date__month=current_month
        )

        # Count the number of reports for the month
        report_count = filtered_updates.count()

        # Create a notification if reports are less than 2
        if report_count < 2:
            Notification.objects.create(user=request.user, message=f"Only {report_count} reports found for {pet.name} in {current_month}/{current_year}.")

        # Create a structure to hold daily reports for the selected month
        daily_reports = {}
        for followup_date in filtered_updates.values_list('followup_date', flat=True).distinct():  # Use distinct to avoid duplicates
            day = followup_date.day
            if day not in daily_reports:
                daily_reports[day] = []
            
            # Use filter instead of get to handle multiple reports
            reports_for_date = filtered_updates.filter(followup_date=followup_date)
            
            # Add unique reports for the day
            for report in reports_for_date:
                if report not in daily_reports[day]:  # Check for uniqueness
                    daily_reports[day].append(report)  # Add the report if it's not already in the list

        # Calculate empty cells for the calendar
        first_day_of_month = timezone.datetime(current_year, current_month, 1)
        last_day_of_month = timezone.datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1])

        # Calculate the number of empty cells before the first day of the month
        empty_cells_before = (first_day_of_month.weekday() + 1) % 7  # Adjust for Sunday as the first day of the week
        empty_cells_after = (6 - last_day_of_month.weekday())  # Calculate empty cells after the last day

        # Prepare the monthly reports context
        monthly_reports = {
            'year': current_year,
            'month': current_month,
            'days_list': list(range(1, 32)),  # Days of the month
            'daily_reports': daily_reports,
            'empty_cells_before': [None] * empty_cells_before,  # Create a list of None for empty cells
            'empty_cells_after': [None] * empty_cells_after,  # Create a list of None for empty cells
            'tracking_start_date': tracking_start_date,  # Add tracking start date to context
        }

    else:
        track_updates = []  # No adoption found
        monthly_reports = None

    return render(request, 'reportRequest.html', {
        'pet': pet,
        'pet_adoption': pet_adoption,
        'track_updates': track_updates,
        'monthly_reports': monthly_reports,
    })

def report_detail(request, id):
    # Assuming you have an adoption_id field in your TrackUpdateTable model
    reports = TrackUpdateTable.objects.filter(id=id)  # Change 'adoption_id' to the actual field name
    return render(request, 'report_details.html', {'reports': reports})

from django import template
register = template.Library()

@register.filter
def month_name(month_number):
    """Return the full month name for a given month number."""
    try:
        month_number = int(month_number)  # Ensure the input is an integer
        if 1 <= month_number <= 12:
            return calendar.month_name[month_number]  # Returns full month name
    except (ValueError, TypeError):
        pass  # Handle cases where conversion to int fails
    return ""  # Return an empty string for invalid month numbers


def report_details(request, pet_adoption_id):
    # Get the pet adoption request using the provided ID
    pet_adoption = get_object_or_404(PetAdoptionTable, id=pet_adoption_id)
    
    # Retrieve all reports associated with this pet adoption request
    reports = TrackUpdateTable.objects.filter(pet_adoption_request=pet_adoption)

    # Render the template with the reports and pet adoption details
    return render(request, 'report_details.html', {
        'pet_adoption': pet_adoption,
        'reports': reports,
    })

@login_required  # Ensure the user is logged in
def add_report(request, pet_id):
    pet_adoption_request = get_object_or_404(PetAdoptionTable, id=pet_id)  # Get the pet adoption request

    if request.method == 'POST':
        form = TrackUpdateForm(request.POST, request.FILES)  # Include FILES for image uploads
        if form.is_valid():
            track_update = form.save(commit=False)  # Create an instance but don't save yet
            track_update.pet_adoption_request = pet_adoption_request  # Set the foreign key
            track_update.author = request.user  # Set the author to the logged-in user
            track_update.followup_date = date.today()  # Set today's date as followup_date
            track_update.save()  # Save the instance to the database
            return redirect('reportadopted_pets')  # Redirect to the desired page after saving
    else:
        form = TrackUpdateForm()  # Create a new form instance

    return render(request, 'add_report.html', {'form': form, 'pet_id': pet_id})

from datetime import timedelta
@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# Ensure you have the necessary NLTK resources
nltk.download('punkt')

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def search_results(request):
    query = request.GET.get('q')  # Get the search query from the URL parameters
    adoption_listings = None  # Initialize adoption_listings to None

    if query:  # If there is a search query
        # Process the query with spaCy
        doc = nlp(query.lower())

        # Extract meaningful tokens (e.g., nouns, adjectives, entities)
        keywords = [token.text for token in doc if not token.is_stop and not token.is_punct]

        # Optional: Expand keywords with synonyms or related terms
        synonyms = {
            "dog": ["dog", "canine", "puppy"],
            "cat": ["cat", "feline", "kitten"],
            "small": ["small", "tiny", "little"],
            "black": ["black", "dark", "ebony"],
        }
        expanded_keywords = []
        for keyword in keywords:
            expanded_keywords.append(keyword)
            if keyword in synonyms:
                expanded_keywords.extend(synonyms[keyword])

        # Filter the PendingPetForAdoption model using the expanded keywords
        q_objects = Q()
        for keyword in expanded_keywords:
            q_objects |= Q(animal_type__icontains=keyword) | \
                        Q(breed__icontains=keyword) | \
                        Q(color__icontains=keyword) | \
                        Q(gender__icontains=keyword) | \
                        Q(age__icontains=keyword) | \
                        Q(location__icontains=keyword) | \
                        Q(additional_details__icontains=keyword) | \
                        Q(author__icontains=keyword)

        adoption_listings = PendingPetForAdoption.objects.filter(q_objects, adoption_status='approved')

    return render(request, 'homepage.html', {'adoption_listings': adoption_listings, 'query': query})


from django.contrib.auth import logout as auth_logout
def logout(request):
    auth_logout(request)  # Log the user out
    messages.success(request, 'You have been logged out successfully.')  # Optional: Add a success message
    return redirect('home')  # Redirect to the homepage after logout

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        # Create a new user
        try:
            user = User.objects.create_user(username=username, password=password1, email=email)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('home')  # Redirect to the login page after successful signup
        except Exception as e:
            messages.error(request, f'Error creating account: {e}')

    return render(request, 'signup.html')
    
    
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = AdminProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()  # Save the updated user profile
            messages.success(request, 'Profile updated successfully!')  # Success message
            return redirect('homepage_admin')  # Redirect to the admin homepage after successful update
    else:
        form = AdminProfileForm(instance=request.user)  # Pre-fill the form with the current user's data

    return render(request, 'edit_profile.html', {'form': form})  # Render the form in the template

def admin_approved_pet_detail(request, pet_id):
    admin_approved_pet_detail = PendingPetForAdoption.objects.get(id=pet_id)
    return render(request, 'admin_approved_pet_detail.html', {'admin_approved_pet_detail': admin_approved_pet_detail})

@require_http_methods(['POST'])
def send_notification(request):
    recipient_id = request.POST.get('recipient_id')
    message = request.POST.get('message')
    try:
        recipient = User.objects.get(id=recipient_id)
        notification = Notification(user=recipient, message=message)
        notification.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False})

###################################   API SECTION    ###################################################################
from django.middleware.csrf import get_token
def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

import json
from django.views import View
from rest_framework_simplejwt.tokens import RefreshToken
class login_react(View):
    def post(self, request, *args, **kwargs):
        try:
            # Parse the JSON body
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            # Check if username and password are provided
            if not username or not password:
                return JsonResponse({'error': 'Username and password are required.'}, status=400)

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Generate token
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    'message': 'Login successful',
                    'user_id': user.id,
                    'username': user.username,
                    'token': str(refresh.access_token)  # Include the access token
                })
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
@csrf_exempt  # Use this for testing; consider using CSRF protection in production
def api_signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')

        # Create the user
        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email)
        return JsonResponse({'message': 'User  created successfully'}, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

class AdoptionRequestUpdateView(generics.UpdateAPIView):
    queryset = PetAdoptionTable.objects.all()
    serializer_class = PetAdoptionTableSerializer

    def put(self, request, *args, **kwargs):
        # Get the adoption request object by ID
        try:
            adoption_request = self.get_object()
        except PetAdoptionTable.DoesNotExist:
            return Response({'error': 'Adoption request not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Update the adoption_request_status
        adoption_request_status = request.data.get('adoption_request_status')
        if adoption_request_status:
            adoption_request.adoption_request_status = adoption_request_status

            # If the status is set to "review", you can add any additional logic here if needed
            if adoption_request_status == 'review':
                # You can add any specific logic for when the status is set to "review"
                pass

            # If approving, set the approval date and time and update the pet status
            elif adoption_request_status == 'approved':
                adoption_request.approval_date_time = timezone.now()  # Assuming you have this field

                # Update the corresponding pet's adoption status
                pet_id = adoption_request.pet_id  # Assuming pet_id is a field in PetAdoptionTable
                try:
                    pending_pet = PendingPetForAdoption.objects.get(id=pet_id)
                    pending_pet.adoption_status = 'Pet is already adopt'  # Update the adoption status
                    pending_pet.save()  # Save the changes
                except PendingPetForAdoption.DoesNotExist:
                    return Response({'error': 'Pending pet not found.'}, status=status.HTTP_404_NOT_FOUND)

            # If denying, you can add any additional logic here if needed
            elif adoption_request_status == 'rejected':
                adoption_request.approval_date_time = timezone.now()  # Assuming you have this field

        # Save the updated object
        adoption_request.save()

        # Serialize the updated object and return the response
        serializer = self.get_serializer(adoption_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AdoptionRequestList(generics.ListAPIView):
    """
    View to list all pending pets for a specific user.
    """
    serializer_class = PetAdoptionTableSerializer
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get_queryset(self):
        """
        This view should return a list of all the pending pets
        for the user as determined by the user_id in the URL.
        """
        user_id = self.kwargs['user_id']  # Get user_id from the URL
        return PetAdoptionTable.objects.filter(user_id=user_id)  # Filter by user_id and status
    

def get_pending_pets(request):
    geolocator = Nominatim(user_agent="pet_adoption_app")
    pending_pets = PendingPetForAdoption.objects.filter(adoption_status='approved')
    
    pet_data = []
    for pet in pending_pets:
        try:
            # Get coordinates from location string
            location = geolocator.geocode(pet.location)
            latitude = location.latitude if location else None
            longitude = location.longitude if location else None
        except GeocoderTimedOut:
            # Handle timeout error
            latitude = None
            longitude = None
            print(f"Geocoding timed out for location: {pet.location}")

        pet_data.append({
            'id':pet.id,
            'name': pet.name,
            'animal_type': pet.animal_type,
            'breed': pet.breed,
            'color': pet.color,
            'gender': pet.gender,
            'age': pet.age,
            'location': pet.location,
            'latitude': latitude,
            'longitude': longitude,
            'additional_details': pet.additional_details,
            'img': pet.img.url if pet.img else None,
            'author': pet.author,
            'created_at': pet.created_at.isoformat(),
        })
    
    return JsonResponse(pet_data, safe=False)

def get_traffic_data(request, pet_id):
    try:
        logging.info(f"Fetching traffic data for pet ID: {pet_id}")
        pet = PendingPetForAdoption.objects.get(id=pet_id)
        logging.info(f"Pet object: {pet}")

        geolocator = Nominatim(user_agent="petmet_app")
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            try:
                location = geolocator.geocode(pet.location, timeout=10)  # Set a timeout of 10 seconds
                logging.info(f"Geocoded location: {location}")
                break
            except GeocoderTimedOut:
                logging.error("Geocoding service timed out. Retrying...")
                attempt += 1
            except GeocoderServiceError as e:
                logging.error(f"Geocoding service error: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)

        if location:
            traffic_data = {
                'coordinates': [
                    {'latitude': location.latitude, 'longitude': location.longitude},
                    # Add more coordinates as needed
                ]
            }
            logging.info(f"Traffic data: {traffic_data}")
            return JsonResponse(traffic_data)
        else:
            logging.error("Location not found")
            return JsonResponse({'error': 'Location not found'}, status=404)
    except PendingPetForAdoption.DoesNotExist:
        logging.error(f"Pet not found with ID: {pet_id}")
        return JsonResponse({'error': 'Pet not found'}, status=404)
    except Exception as e:
        logging.error(f"Error fetching traffic data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def search_pending_pets(request):
    if request.method == 'GET':
        search_term = request.GET.get('search')
        if search_term:
            pending_pets = PendingPetForAdoption.objects.filter(
                Q(adoption_status='approved') &
                (
                    Q(name__icontains=search_term) |
                    Q(animal_type__icontains=search_term) |
                    Q(breed__icontains=search_term) |
                    Q(color__icontains=search_term) |
                    Q(gender__icontains=search_term) |
                    Q(age__icontains=search_term) |
                    Q(location__icontains=search_term) |
                    Q(additional_details__icontains=search_term)
                )
            )
        else:
            pending_pets = PendingPetForAdoption.objects.filter(adoption_status='approved')
        results = []
        for pet in pending_pets:
            results.append({
                'id': pet.id,
                'name': pet.name,
                'animal_type': pet.animal_type,
                'breed': pet.breed,
                'color': pet.color,
                'gender': pet.gender,
                'age': pet.age,
                'location': pet.location,
                'additional_details': pet.additional_details,
                'img': pet.img.url,
                'author': pet.author,
            })
        return JsonResponse({'results': results}, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications_data = [{'id': n.id, 'message': n.message, 'created_at': n.created_at} for n in notifications]
    return Response({'notifications': notifications_data, 'count': notifications.count()})

class GetNotificationsView(APIView):
  def get(self, request):
    user_id = request.query_params.get('user_id', None)
    
    if user_id:
      # Fetch notifications for the specified user ID
      notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')
      unread_notifications = notifications.filter(is_read=False)
      
      serializer = NotificationSerializer(notifications, many=True)
      
      # Return the notifications and count
      return Response({
        'notifications': serializer.data,
        'count': unread_notifications.count(),
      }, status=200)
    else:
      # Return an error if no user_id is provided
      return Response({'error': 'User   ID is required'}, status=400)
    
def create_user_and_token(username, password):
    user = User.objects.create_user(username=username, password=password)
    token = Token.objects.create(user=user)
    return token.key

class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        user_id = request.data.get('user_id', None)
        if not user_id:
            return False
        user = request.user
        if user.id != int(user_id):
            return False
        return True

class ReactMarkNotificationAsReadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        notification_id = request.query_params.get('notification_id', None)

        if not notification_id:
            return Response({'error': 'Notification ID is required'}, status=400)

        try:
            notification = Notification.objects.filter(id=notification_id).first()
            if notification:
                notification.is_read = True  # Mark the notification as read
                notification.save()
                return Response({'message': 'Notification marked as read'}, status=200)
            else:
                return Response({'error': 'Notification not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)