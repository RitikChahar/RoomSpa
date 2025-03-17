from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import os
from django.conf import settings
from User.permissions import IsTherapist
from .models import Location, Pictures, Services, BankDetails
from .serializers import (
    LocationSerializer, 
    PicturesSerializer, 
    ServicesSerializer, 
    BankDetailsSerializer,
    TherapistProfileSerializer
)
from User.functions.image_handler import upload_image

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def location_view(request):
    if request.method == 'GET':
        try:
            location = Location.objects.get(user=request.user)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except Location.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            location, created = Location.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(LocationSerializer(location).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
@parser_classes([MultiPartParser, FormParser])
def pictures_view(request):
    if request.method == 'GET':
        try:
            pictures = Pictures.objects.get(user=request.user)
            serializer = PicturesSerializer(pictures)
            return Response(serializer.data)
        except Pictures.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        
    elif request.method == 'POST':
        uploaded_urls = {}

        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            profile_pic_url = upload_image(file_path, "therapist/profile")
            if profile_pic_url:
                uploaded_urls['profile_picture'] = profile_pic_url

        if 'certificate' in request.FILES:
            file = request.FILES['certificate']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            certificate_url = upload_image(file_path, "therapist/certificates")
            if certificate_url:
                uploaded_urls['certificate'] = certificate_url

        if 'national_id' in request.FILES:
            file = request.FILES['national_id']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            national_id_url = upload_image(file_path, "therapist/documents")
            if national_id_url:
                uploaded_urls['national_id'] = national_id_url

        if 'more_pictures' in request.FILES:
            more_pictures = request.FILES.getlist('more_pictures')
            more_picture_urls = []

            for picture in more_pictures:
                file_path = os.path.join(settings.MEDIA_ROOT, picture.name)
                with open(file_path, "wb+") as destination:
                    for chunk in picture.chunks():
                        destination.write(chunk)
                pic_url = upload_image(file_path, "therapist/additional")
                if pic_url:
                    more_picture_urls.append(pic_url)

            if more_picture_urls:
                uploaded_urls['more_pictures'] = more_picture_urls

        try:
            pictures = Pictures.objects.get(user=request.user)
            
            if 'profile_picture' in uploaded_urls:
                pictures.profile_picture = uploaded_urls['profile_picture']
            
            if 'certificate' in uploaded_urls:
                pictures.certificate = uploaded_urls['certificate']
            
            if 'national_id' in uploaded_urls:
                pictures.national_id = uploaded_urls['national_id']
            
            if 'more_pictures' in uploaded_urls:
                pictures.more_pictures.extend(uploaded_urls['more_pictures'])
            
            pictures.save()

        except Pictures.DoesNotExist:
            required_fields = ['profile_picture', 'certificate', 'national_id']

            for field in required_fields:
                if field not in uploaded_urls and field not in request.data:
                    return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
            
            pictures_data = {'user': request.user, **uploaded_urls}
            
            for field in ['profile_picture', 'certificate', 'national_id']:
                if field not in uploaded_urls and field in request.data:
                    pictures_data[field] = request.data[field]
            
            if 'more_pictures' not in uploaded_urls and 'more_pictures' in request.data:
                if isinstance(request.data['more_pictures'], list):
                    pictures_data['more_pictures'] = request.data['more_pictures']
                else:
                    try:
                        import json
                        pictures_data['more_pictures'] = json.loads(request.data['more_pictures'])
                    except:
                        pictures_data['more_pictures'] = []
            
            pictures = Pictures.objects.create(**pictures_data)
        
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def services_view(request):
    if request.method == 'GET':
        try:
            services = Services.objects.get(user=request.user)
            serializer = ServicesSerializer(services)
            return Response(serializer.data)
        except Services.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        serializer = ServicesSerializer(data=request.data)
        if serializer.is_valid():
            services, created = Services.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(ServicesSerializer(services).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def bank_details_view(request):
    if request.method == 'GET':
        try:
            bank_details = BankDetails.objects.get(user=request.user)
            serializer = BankDetailsSerializer(bank_details)
            return Response(serializer.data)
        except BankDetails.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        serializer = BankDetailsSerializer(data=request.data)
        if serializer.is_valid():
            bank_details, created = BankDetails.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(BankDetailsSerializer(bank_details).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def therapist_profile_view(request):
    if request.method == 'GET':
        try:
            location = Location.objects.get(user=request.user)
            location_data = LocationSerializer(location).data
        except Location.DoesNotExist:
            location_data = {}
            
        try:
            pictures = Pictures.objects.get(user=request.user)
            pictures_data = PicturesSerializer(pictures).data
        except Pictures.DoesNotExist:
            pictures_data = {}
            
        try:
            services = Services.objects.get(user=request.user)
            services_data = ServicesSerializer(services).data
        except Services.DoesNotExist:
            services_data = {}
            
        try:
            bank_details = BankDetails.objects.get(user=request.user)
            bank_details_data = BankDetailsSerializer(bank_details).data
        except BankDetails.DoesNotExist:
            bank_details_data = {}
        
        profile_data = {
            'location': location_data,
            'pictures': pictures_data,
            'services': services_data,
            'bank_details': bank_details_data
        }
        
        return Response(profile_data)
    
    elif request.method == 'POST':
        serializer = TherapistProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)