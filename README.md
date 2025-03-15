# RoomSpa

This project supports the operations of a spa center, a location offering health and beauty treatments, or a mineral spring or resort known for its mineral water and health benefits. It handles appointments, services, client management, and more.

## Tech Stack

- **Backend:** Django, Django Rest Framework (DRF), Postgres, Firebase
- **Frontend:** Flutter

# User Authentication API

This project provides user authentication and profile management APIs using Django Rest Framework and JWT authentication.

## API Endpoints

### 1. User Login
**Endpoint:** `POST /api/login/`
- **Description:** Logs in the user and returns access and refresh tokens.
- **Request Body:**
  ```json
  {
    "identifier": "user@example.com or phone number",
    "password": "password123"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Login successful",
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token"
  }
  ```

### 2. Get User Profile
**Endpoint:** `GET /api/user-profile/`
- **Description:** Retrieves the authenticated user's profile.
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "user": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone_number": "1234567890",
      "gender": "Male",
      "role": "User"
    },
    "status": {
      "verification_status": true,
      "consent": true
    }
  }
  ```

### 3. User Logout
**Endpoint:** `POST /api/logout/`
- **Description:** Logs out the user by blacklisting the refresh token.
- **Request Body:**
  ```json
  {
    "refresh_token": "jwt-refresh-token"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Logout successful"
  }
  ```

### 4. User Registration
**Endpoint:** `POST /api/register/`
- **Description:** Registers a new user.
- **Request Body:**
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "phone_number": "1234567890",
    "gender": "Male",
    "role": "User",
    "consent": true,
    "password": "password123",
    "verification_method": "email"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Your account has been created successfully. Please verify your email!"
  }
  ```

### 5. Verify Email
**Endpoint:** `GET /api/verify-email/`
- **Description:** Verifies the user's email.
- **Query Params:** `name=<name>&verification-token=<token>`
- **Response:**
  ```json
  {
    "message": "Account verified successfully."
  }
  ```

### 6. Forgot Password
**Endpoint:** `POST /api/forgot-password/`
- **Description:** Initiates the password reset process.
- **Request Body:**
  ```json
  {
    "identifier": "user@example.com or phone number",
    "password": "newpassword"
  }
  ```
- **Response:**
  ```json
  {
    "message": "An email to reset your password has been sent."
  }
  ```

### 7. Reset Password
**Endpoint:** `POST /api/reset-password/`
- **Description:** Resets the user's password.
- **Request Body:**
  ```json
  {
    "name": "John Doe",
    "verification-token": "reset-token"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Password reset successful."
  }
  ```

### 8. Verify Token
**Endpoint:** `POST /api/verify-token/`
- **Description:** Checks if an access token is valid.
- **Request Body:**
  ```json
  {
    "access_token": "jwt-access-token"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Token is valid"
  }
  ```

### 9. Refresh Token
**Endpoint:** `POST /api/refresh-token/`
- **Description:** Refreshes an access token.
- **Request Body:**
  ```json
  {
    "refresh_token": "jwt-refresh-token"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "access_token": "new-jwt-access-token",
    "message": "Access token refreshed successfully"
  }
  ```

### 10. Update User Profile
**Endpoint:** `PUT /api/update-profile/`
- **Description:** Updates user profile details.
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "name": "New Name",
    "gender": "Female",
    "consent": true
  }
  ```
- **Response:**
  ```json
  {
    "message": "Profile updated successfully",
    "data": {
      "name": "New Name",
      "gender": "Female",
      "consent": true
    }
  }
  ```

### 11. Update Email
**Endpoint:** `GET /api/update-email/`
- **Description:** Updates the user's email after verification.
- **Query Params:** `name=<name>&verification-token=<token>&update-id=<encrypted-email>`
- **Response:**
  ```json
  {
    "message": "Email updated successfully."
  }
  ```

### 12. Delete User Profile
**Endpoint:** `DELETE /api/delete-profile/`
- **Description:** Deletes the authenticated user's profile.
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "message": "User deleted successfully"
  }
  ```

## Postman Collection
You can access the Postman collection for testing the APIs using the following link:
[Postman Collection](https://documenter.getpostman.com/view/27523601/2sAYkBsgUF)