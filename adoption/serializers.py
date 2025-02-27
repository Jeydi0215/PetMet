from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Admin, PetAdoptionRequestTable, PetAdoptionTable, PendingPetForAdoption, TrackUpdateTable, Notification
from django.contrib.auth.hashers import make_password

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class PetAdoptionRequestTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetAdoptionRequestTable
        fields = '__all__'

class PetAdoptionTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetAdoptionTable
        fields = '__all__'

class PendingPetForAdoptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingPetForAdoption
        fields = '__all__'

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user

class TrackUpdateTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackUpdateTable
        fields = '__all__'

class UpdatePendingPetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingPetForAdoption
        fields = ['name', 'animal_type', 'breed', 'color', 'gender', 'age', 'location', 'additional_details', 'img']
        extra_kwargs = {
            'img': {'required': False}  # Make the img field optional
        }

    def update(self, instance, validated_data):
        # Check if the image is being updated
        img = validated_data.pop('img', None)  # Remove img from validated_data if it exists

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # If a new image is provided, update the instance's image
        if img:
            instance.img = img  # Assuming img is a FileField or ImageField

        instance.save()  # Save the updated instance
        return instance

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Notification
        fields = ['user', 'message', 'is_read']

    def create(self, validated_data):
        user = validated_data.pop('user')
        notification = Notification.objects.create(user=user, message=validated_data['message'])
        return notification
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']