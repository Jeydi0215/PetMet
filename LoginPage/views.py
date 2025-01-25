from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth import login
from adoption.models import PendingPetForAdoption, Admin, PetAdoptionTable, TrackUpdateTable, Notification
from django.core.paginator import Paginator
from .forms import PetAdoptionForm, SignUpForm, LoginForm, PetAdoptionFormRequest, AdminProfileForm, TrackUpdateForm, PendingPetForAdoptionForm
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
import pytz
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
# Create your views here.
import calendar

# Get the month names
months = list(calendar.month_name)

# Accessing the first month
print(months[1])  # Output: January
# views.py
from rest_framework import viewsets
from adoption.models import Admin, PetAdoptionRequestTable, PetAdoptionTable, PendingPetForAdoption
from adoption.serializers import AdminSerializer, PetAdoptionRequestTableSerializer, PetAdoptionTableSerializer, PendingPetForAdoptionSerializer, TrackUpdateTableSerializer, UpdatePendingPetSerializer

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

from rest_framework import generics
class PetCreateView(generics.CreateAPIView):
    queryset = PendingPetForAdoption.objects.all()
    serializer_class = PendingPetForAdoptionSerializer

    def create(self, request, *args, **kwargs):
        # Use the serializer to validate and save the incoming data
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the new pet record
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # Respond with the created data
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Return errors if validation fails
    
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
        form = PendingPetForAdoptionForm(request.POST, instance=pet)
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
        return redirect('adoption_list')

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

    elif new_status == 'rejected':
        req.approval_date_time = None  # Clear approval date if rejected

    # Save the changes to the PetAdoptionTable
    req.save()

    # Redirect to the view requests page or wherever you want to go after updating
    return redirect('view_requests')  # Make sure 'view_requests' is a valid URL name


                                                   
def admin_report_detail(request, report_id):
    report = get_object_or_404(TrackUpdateTable, id=report_id)
    return render(request, 'admin_report_detail.html', {'report': report})

  # Ensure only logged-in users can access this view
def admin_home(request):
    return render(request, 'admin_home.html')  # Render the admin home template

def home(request):
    return render(request, 'home.html')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Custom authentication logic
        try:
            user = Admin.objects.get(username=username)  # Fetch the user by username
            if user.check_password(password):  # Check the password
                # Specify the backend when logging in
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')  # Adjust backend as necessary
                return redirect('homepage_admin')  # Redirect to the admin home page
            else:
                messages.error(request, 'Invalid username or password.')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')  # Render the login template

def admin_homepage(request):
    # Get the current time in the Philippines
    philippines_tz = pytz.timezone('Asia/Manila')
    philippines_time = timezone.now().astimezone(philippines_tz).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, 'admin_homepage.html', {
        'user': request.user,  # This will still provide user info, even if not authenticated
        'philippines_time': philippines_time,
    })

def admin_signup(request):
    if request.method == 'POST':
        form = EmptyForm(request.POST)  # Use the empty form
        if form.is_valid():
            # You can add logic here to handle the form submission
            return redirect('homepage_admin')  # Redirect to a success page (adjust as needed)
    else:
        form = EmptyForm()  # Create a blank form

    return render(request, 'admin_signup.html', {'form': form})  # Pass the form to the template
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
        
        # Get all follow-up dates
        followup_dates = track_updates.values_list('followup_date', flat=True)

        # Prepare monthly reports
        current_month = timezone.now().month
        current_year = timezone.now().year

        # Create a structure to hold daily reports
        daily_reports = {}
        for followup_date in followup_dates:
            day = followup_date.day
            if day not in daily_reports:
                daily_reports[day] = []
            
            # Use filter instead of get to handle multiple reports
            reports_for_date = track_updates.filter(followup_date=followup_date)
            daily_reports[day].extend(reports_for_date)  # Add all reports for that day

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
    report = get_object_or_404(TrackUpdateTable, id=id)
    return render(request, 'report_details.html', {'report': report})

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

def search_results(request):
    query = request.GET.get('q')  # Get the search query from the URL parameters
    adoption_listings = []  # Initialize an empty list for adoption listings

    if query:  # If there is a search query
        # Tokenize the query into words
        tokens = word_tokenize(query.lower())  # Convert to lowercase and tokenize

        # Filter the PendingPetForAdoption model based on the search query
        # This is a simple example; you may want to enhance this logic
        adoption_listings = PendingPetForAdoption.objects.filter(
            name__icontains=query  # Adjust the field as necessary
        )

        # You can further refine the search using tokens
        for token in tokens:
            adoption_listings = adoption_listings.filter(
                additional_details__icontains=token  # Assuming you have a description field
            )

    return render(request, 'search_results.html', {'adoption_listings': adoption_listings})

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
            form.save()
            return redirect('homepage_admin')
    else:
        form = AdminProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

def admin_approved_pet_detail(request, pet_id):
    admin_approved_pet_detail = PendingPetForAdoption.objects.get(id=pet_id)
    return render(request, 'admin_approved_pet_detail.html', {'admin_approved_pet_detail': admin_approved_pet_detail})