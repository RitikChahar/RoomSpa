from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import UserProfile
from .serializers import UserProfileUpdateSerializer
from .functions.generate_verification import generate_verification_token
from .functions.generate_otp import generate_verification_otp
from .functions.send_mail import send_registration_link
from .functions.encryption import encrypt_password, decrypt_password

@api_view(['POST'])
def login(request):
    identifier = request.data.get('identifier', '').strip()
    password = request.data.get('password')
    
    from django.contrib.auth import get_backends

    backend = get_backends()[0]  
    
    user = backend.authenticate(request, username=identifier, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        return Response({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    response_data = {
        "user": {
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "gender": user.gender,
            "role": user.role,
        },
        "status": {
            "verification_status": user.verification_status,
            "consent": user.consent,
        }
    }
    return Response(response_data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()  
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'message': 'Invalid refresh token'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register(request):
    data = request.data
    name = data.get('name', '').strip()
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')
    gender = data.get('gender', 'prefer_not_to_say')
    role = data.get('role', 'customer')
    consent = data.get('consent', False)
    verification_method = data.get('verification_method')
    
    if UserProfile.objects.filter(email=email, verification_status=True).exists():
        return Response({'message': 'Email address already exists. Please choose another one.'}, status=status.HTTP_400_BAD_REQUEST)
    elif UserProfile.objects.filter(phone_number=phone_number, verification_status=True).exists():
        return Response({'message': 'Phone number already exists. Please choose another one.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        verification_token = generate_verification_otp()
        
        if verification_method == 'email' and email:
            send_registration_link(name, email, verification_token, "registration")
        elif verification_method == 'phone' and phone_number:
            send_registration_link(name, email, verification_token, "registration")
        else:
            return Response({'message': 'Invalid verification method or missing email/phone number.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if email and UserProfile.objects.filter(email=email).exists():
            user_profile = UserProfile.objects.get(email=email)
            user_profile.name = name
            user_profile.phone_number = phone_number
            user_profile.gender = gender
            user_profile.role = role
            user_profile.consent = consent
            user_profile.verification_token = verification_token
            if password:
                user_profile.set_password(password)
            user_profile.save()
        elif phone_number and UserProfile.objects.filter(phone_number=phone_number).exists():
            user_profile = UserProfile.objects.get(phone_number=phone_number)
            user_profile.name = name
            user_profile.email = email
            user_profile.gender = gender
            user_profile.role = role
            user_profile.consent = consent
            user_profile.verification_token = verification_token
            if password:
                user_profile.set_password(password)
            user_profile.save()
        else:
            UserProfile.objects.create_user(
                name=name,
                email=email,
                password=password,
                phone_number=phone_number,
                gender=gender,
                role=role,
                consent=consent,
                verification_token=verification_token
            )
        return Response({'message': 'Your account has been created successfully. Please verify your email or phone number!'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def email_verification(request):
    identifier = request.data.get('identifier', '').strip()
    verification_token = request.data.get('verification_token')

    if '@' in identifier:
        user_profile = UserProfile.objects.filter(
            email=identifier,
            verification_token=verification_token
        ).first()
    else:
        user_profile = UserProfile.objects.filter(
            phone_number=identifier,
            verification_token=verification_token
        ).first()

    
    if user_profile:
        user_profile.verification_status = True
        user_profile.verification_token = None
        user_profile.save()
        return Response({'message': 'Account verified successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def forgot_password(request):
    identifier = request.data.get('identifier', '').strip()
    method = ''
    if '@' in identifier:
        method = 'email'
        user_profile = UserProfile.objects.filter(email=identifier).first()
    else:
        user_profile = UserProfile.objects.filter(phone_number=identifier).first()
        
    if not user_profile:
        return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    verification_token = generate_verification_otp()
    user_profile.verification_token = verification_token
    user_profile.save()

    if method == 'email':
        send_registration_link(user_profile.name, user_profile.email, verification_token, "password_reset")
        return Response({'message': 'An email to reset your password has been sent.'}, status=status.HTTP_200_OK)
    else:
        # Handle phone verification if email is not provided
        return Response({'message': 'An sms to reset your password has been sent to your phone number.'}, 
                       status=status.HTTP_200_OK)

@api_view(['POST'])
def reset_password(request):
    identifier = request.data.get('identifier', '').strip()
    verification_token = request.data.get('verification_token')

    if '@' in identifier:
        user_profile = UserProfile.objects.filter(
            email=identifier,
            verification_token=verification_token
        ).first()
    else:
        user_profile = UserProfile.objects.filter(
            phone_number=identifier,
            verification_token=verification_token
        ).first()
        
    if not user_profile:
        return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    new_password = request.data.get('new_password')
    
    if user_profile:
        user_profile.verification_token = None
        user_profile.set_password(new_password)
        user_profile.save()
        return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Password reset failed.'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    new_email = request.data.get("email")
    new_phone = request.data.get("phone_number")
    new_password = request.data.get("new_password")
    
    if new_email and new_email != user.email:
        verification_token = generate_verification_token()
        encrypted_new_email = encrypt_password(new_email)
        encrypted_phone_number = encrypt_password(user.phone_number)
        verification_link = f"{settings.BASE_URL}/update-email/?identifier={encrypted_phone_number}&verification-token={verification_token}&update-id={encrypted_new_email}"
        send_registration_link(user.name, new_email, verification_link, "email_update")
        
        user.verification_token = verification_token
        user.save()
        return Response({"message": "An email to update your email has been sent."}, status=status.HTTP_202_ACCEPTED)
    
    if new_phone and new_phone != user.phone_number:
        verification_token = generate_verification_token()
        encrypted_new_phone = encrypt_password(new_phone)
        user.verification_token = verification_token
        user.save()
        
        # Handle phone verification flow
        return Response({"message": "A verification code has been sent to your new phone number."}, 
                       status=status.HTTP_202_ACCEPTED)
    
    if new_password and not user.check_password(new_password):
        encrypted_password = encrypt_password(new_password)
        reset_link = f"{settings.BASE_URL}/reset-password/?name={user.name}&verification-token={encrypted_password}"
        user.verification_token = encrypted_password
        user.save()
        
        if user.email:
            send_registration_link(user.name, user.email, reset_link, "password_reset")
        
        return Response({"message": "A verification link to update your password has been sent."}, 
                       status=status.HTTP_200_OK)
    
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully", "data": serializer.data}, 
                       status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def update_email(request):
    identifier = request.query_params.get('identifier', '').strip()
    verification_token = request.query_params.get('verification-token', '').strip()
    encrypted_new_email = request.query_params.get('update-id', '').strip()
    new_email = decrypt_password(encrypted_new_email)
    phone_number = decrypt_password(identifier)
    
    user_profile = UserProfile.objects.filter(phone_number=phone_number, verification_token=verification_token).first()
    
    if user_profile and new_email['success']:
        user_profile.email = new_email['decrypted_password']
        user_profile.verification_token = None
        user_profile.save()
        return Response({"message": "Email updated successfully."}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Email verification failed."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def update_phone(request):
    name = request.query_params.get('name', '').strip()
    verification_token = request.query_params.get('verification-token', '').strip()
    encrypted_new_phone = request.query_params.get('update-id', '').strip()
    new_phone = decrypt_password(encrypted_new_phone)
    
    user_profile = UserProfile.objects.filter(name=name, verification_token=verification_token).first()
    
    if user_profile and new_phone['success']:
        user_profile.phone_number = new_phone['decrypted_password']
        user_profile.verification_token = None
        user_profile.save()
        return Response({"message": "Phone number updated successfully."}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Phone verification failed."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_profile(request):
    user = request.user
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def verify_token(request):
    token = request.data.get('access_token')

    if not token:
        return Response({
            "success": False,
            "message": "Token is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        UntypedToken(token)
        return Response({
            "success": True,
            "message": "Token is valid"
        }, status=status.HTTP_200_OK)
    except (TokenError, InvalidToken) as e:
        return Response({
            "success": False,
            "message": str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({
            "success": False,
            "message": "Refresh token is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)
        
        return Response({
            "success": True,
            "access_token": new_access_token,
            "message": "Access token refreshed successfully"
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "success": False,
            "message": "Invalid refresh token",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)