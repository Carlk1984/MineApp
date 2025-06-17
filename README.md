# Mine KPI Fullstack Application

A comprehensive mining KPI tracking system with FastAPI backend and Flutter frontend.

## Structure
- `backend/` - FastAPI backend with PostgreSQL, JWT auth, and role-based access
- `frontend/` - Flutter mobile/web application

## Features
- JWT Authentication
- Role-based access control (operator, manager, supervisor, admin)
- PostgreSQL database integration
- RESTful API for KPI data management
- Cross-platform Flutter frontend
- **Mobile Enhancements:**
  - Camera/photo capture for documentation
  - Geolocation tagging for location tracking
  - Digital signature input for validation
  - Offline storage of media files

## Backend Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)

### Installation
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env` file and update with your database credentials
   - For PostgreSQL: `DATABASE_URL=postgresql://username:password@localhost/mine_kpi_db`
   - For SQLite: `DATABASE_URL=sqlite:///./mine_kpi.db` (default)

4. Create initial admin user:
   ```bash
   python create_admin.py
   ```
   Default credentials: `admin@example.com` / `admin123`

5. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

### Railway Deployment
The backend is configured for Railway deployment with:
- `railway.toml` - Railway configuration
- `Procfile` - Process definition
- Environment variables support for DATABASE_URL and SECRET_KEY

## Frontend Setup

### Prerequisites
- Flutter SDK 3.10.0+
- Dart SDK 3.0.0+

### Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   flutter pub get
   ```

3. Generate model files:
   ```bash
   flutter packages pub run build_runner build
   ```

4. Run the app:
   ```bash
   flutter run
   ```

### Building Android APK
1. Build release APK:
   ```bash
   flutter build apk --release
   ```

2. The APK will be generated at:
   ```
   build/app/outputs/flutter-apk/app-release.apk
   ```

### Mobile Permissions
The app requires the following Android permissions:
- `CAMERA` - For photo capture functionality
- `ACCESS_FINE_LOCATION` - For GPS location tracking
- `ACCESS_COARSE_LOCATION` - For network-based location
- `WRITE_EXTERNAL_STORAGE` - For saving photos locally
- `READ_EXTERNAL_STORAGE` - For accessing saved photos

### Features
- **Authentication**: Secure login with JWT tokens
- **Dashboard**: Overview of user role and quick actions
- **Records Management**: Create, view, and manage KPI records
- **User Management**: View users (role-based access)
- **Responsive Design**: Works on mobile, tablet, and web
- **Mobile Features**:
  - Photo capture for equipment documentation, safety incidents, and quality control
  - Automatic geolocation tagging with GPS coordinates
  - Digital signature capture for operator validation
  - Offline storage and sync of media files

## API Endpoints

### Authentication
- `POST /token` - Login with email/password
- `POST /register` - Register new user (admin only)
- `GET /users/me` - Get current user info

### Records
- `GET /records` - Get records (filtered by role)
- `POST /record` - Create new record
- `GET /record/{id}` - Get specific record
- `POST /record/{id}/approve` - Approve record (manager+)
- `POST /record/{id}/reject` - Reject record (manager+)

### Users
- `GET /users` - List all users (manager+ access)

## User Roles

- **Operator**: Submit records, view own records
- **Manager**: Approve/reject records, view all records and users
- **Supervisor**: Same as manager (extensible)
- **Admin**: Full access including user registration

## Development

### Backend Development
- FastAPI with automatic API documentation
- SQLAlchemy ORM with PostgreSQL/SQLite support
- JWT authentication with role-based access control
- Environment-based configuration

### Frontend Development
- Flutter with Material Design 3
- Provider for state management
- GoRouter for navigation with auth guards
- HTTP client for API communication
- Secure storage for JWT tokens
- **Mobile Services**:
  - `CameraService` - Photo capture and gallery selection
  - `LocationService` - GPS location tracking with permissions
  - `SignatureService` - Digital signature capture and export

## Security Features
- Password hashing with bcrypt
- JWT tokens with expiration
- Role-based route protection
- Environment variable configuration
- CORS configuration for cross-origin requests
