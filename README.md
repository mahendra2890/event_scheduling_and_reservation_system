USED  AI to write most of the tests, and these docs:

Here's a summary:

- Clone to your local, and run "docker compose up -d"
<!-- Install required items if this does not work for you -->


If you don't want to go the docker container way. Install a virtual environment with Python 3.9, and then activate the virtual environment (source venv/bin/activate on mac)
- pip install -r requirements.txt to install requirements
- python manage.py makemigrations for creating migrations
- python manage.py migrate to apply these migrations.
- python manage.py runserver to run the server on localhost.
- Find swagger here: http://127.0.0.1:8000/api/docs/ ; and test all APIs; see all schemas and what not

<img width="784" height="762" alt="Screenshot 2025-08-16 at 12 30 17 AM" src="https://github.com/user-attachments/assets/2145df26-f55b-42b0-9a78-5955c8a009a7" />



Please note that it is advisable to delete the db.sqlite3 file : I have kept it so there is some data to start with even as you do it for the first time



Test for high concurrency/reliability/prevent overbooking case:
test_concurrent_booking_race_condition


What did I do? Created an atomic transaction with lock on row. I wanted to created a distributed lock with redis but unfortunately did not get enough time to set up redis here.


















---- AI generated detailed version -----

# Event Scheduling & Reservation System

A robust Django REST Framework-based system for managing events and reservations with proper concurrency handling and comprehensive user management.

## 🚀 Features

### Core Functionality
- **User Management**: Separate Organizer and Customer roles with authentication
- **Event Management**: Create, update, delete events with capacity management
- **Reservation System**: Book, cancel, and manage event reservations
- **Concurrency Protection**: Prevents overbooking with database-level locking
- **Comprehensive Logging**: All user actions tracked via HistoryPoint model

### Technical Features
- **RESTful API**: Complete CRUD operations with proper HTTP methods
- **Token Authentication**: Secure API access with DRF tokens
- **Docker Support**: Containerized development and deployment
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Comprehensive Testing**: 900+ lines of tests including concurrency tests

## 🏗️ Architecture Overview

### User Roles
- **Organizers**: Can create and manage events, view bookings for their events
- **Customers**: Can browse events, make reservations, and manage their bookings

### Core Models
- **Event**: Central entity with capacity management and time constraints
- **Booking**: Reservation system with status tracking and validation
- **User Profiles**: Extended user models for Organizer and Customer roles
- **HistoryPoint**: Generic logging system for all user actions

## 📊 Model Schema

### Event Model
```
Event
├── title (CharField) - Event title
├── description (TextField) - Event description  
├── start_time (DateTimeField) - Event start time
├── end_time (DateTimeField) - Event end time
├── capacity (PositiveIntegerField) - Maximum attendees
├── creator (ForeignKey → Organizer) - Event creator
├── created_at (DateTimeField) - Creation timestamp
├── updated_at (DateTimeField) - Last update timestamp
└── Properties:
    ├── available_slots - Calculated available capacity
    ├── is_full - Boolean if event is at capacity
    ├── is_past - Boolean if event has ended
    └── is_ongoing - Boolean if event is currently running
```

### Booking Model
```
Booking
├── attendee (ForeignKey → Customer) - Booking customer
├── event (ForeignKey → Event) - Booked event
├── booking_date (DateTimeField) - Booking timestamp
├── status (CharField) - 'active' or 'cancelled'
├── Constraints:
│   └── unique_together: (attendee, event) - Prevents duplicates
└── Methods:
    └── cancel() - Cancels booking with validation
```

### User Models
```
User (Django Auth)
├── username, email, password (standard Django fields)
├── organizer_profile (OneToOne → Organizer)
└── customer_profile (OneToOne → Customer)

Organizer
├── user (OneToOne → User)
├── organization_name (CharField)
└── business_address (TextField)

Customer  
├── user (OneToOne → User)
└── (minimal profile for future extension)

HistoryPoint (Generic Logging)
├── user (ForeignKey → User)
├── action (CharField) - create/update/delete/cancel/etc.
├── content_type (GenericForeignKey) - Any model
├── object_id (PositiveIntegerField)
├── details (JSONField) - Additional action details
└── created_at (DateTimeField)
```

## 🔌 API Endpoints

### Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/userapi/organizer/register/` | Register new organizer | No |
| POST | `/userapi/customer/register/` | Register new customer | No |
| POST | `/userapi/login/` | User login | No |
| POST | `/userapi/logout/` | User logout | Yes |
| GET | `/userapi/profile/` | Get user profile | Yes |
| GET | `/userapi/history/` | Get user action history | Yes |

### Event Endpoints
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/eventapi/event/` | List all events | Yes | All |
| POST | `/eventapi/event/` | Create new event | Yes | Organizer |
| GET | `/eventapi/event/{id}/` | Get event details | Yes | All |
| PATCH | `/eventapi/event/{id}/` | Update event | Yes | Organizer (own events) |
| DELETE | `/eventapi/event/{id}/` | Delete event | Yes | Organizer (own events) |
| GET | `/eventapi/event/my_events/` | List organizer's events | Yes | Organizer |
| GET | `/eventapi/event/upcoming/` | List upcoming events | Yes | All |
| GET | `/eventapi/event/past/` | List past events | Yes | All |

### Booking Endpoints
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/bookingapi/booking/` | List user's bookings | Yes | All |
| POST | `/bookingapi/booking/` | Create booking | Yes | Customer |
| GET | `/bookingapi/booking/{id}/` | Get booking details | Yes | Attendee/Organizer |
| PATCH | `/bookingapi/booking/{id}/` | Update booking | Yes | Customer (own bookings) |
| DELETE | `/bookingapi/booking/{id}/` | Delete booking | Yes | Customer (own bookings) |
| POST | `/bookingapi/booking/{id}/cancel/` | Cancel booking | Yes | Customer (own bookings) |

### API Documentation
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/apis/chema/`

## 🛡️ Concurrency Handling Strategy

### Problem Statement
The critical requirement is preventing overbooking when multiple users simultaneously try to book the last available slot in an event.

### Solution Implementation

#### 1. Database-Level Locking
```python
@transaction.atomic
def create(self, validated_data):
    event = event.__class__.objects.select_for_update().get(id=event.id)
    if event.is_full:
        raise serializers.ValidationError(...)
```

**How it works:**
- `@transaction.atomic` ensures the entire booking operation is atomic
- `select_for_update()` locks the event row in the database
- Other concurrent requests wait for the lock to be released
- After locking, we re-check capacity to prevent race conditions

#### 2. Capacity Validation
```python
@property
def available_slots(self):
    active_bookings_count = self.bookings.filter(status='active').count()
    return max(0, self.capacity - active_bookings_count)
```

**Benefits:**
- Real-time capacity calculation
- Considers only active bookings (cancelled bookings free up slots)
- Atomic operation prevents inconsistent state

#### 3. Business Logic Validation
- **Duplicate Prevention**: `unique_together = [('attendee', 'event')]`
- **Time Validation**: Prevents booking past/ongoing events
- **Status Management**: Proper booking lifecycle (active ↔ cancelled)

### Testing Concurrency
The system includes comprehensive concurrency tests:
```python
def test_concurrent_booking_race_condition(self):
    # Simulates 5 users booking simultaneously for event with capacity 2
    # Ensures exactly 2 successful bookings and 3 rejections
```

### Production Considerations
- **SQLite Limitations**: Tests note SQLite locking limitations for development
- **PostgreSQL Recommended**: Production should use PostgreSQL for better concurrency
- **Performance**: Locking adds minimal overhead for booking operations

## 🚀 Quick Start

### Prerequisites
- Docker (version 20.10+)
- Docker Compose (version 2.0+)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Assignment

# Copy environment file
cp env.example .env
# Edit .env file with your settings
```

### 2. Build and Run
```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser (optional)
docker-compose exec web python manage.py createsuperuser
```

### 3. Access the Application
- **Django Admin**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **API Root**: http://localhost:8000/

## 🧪 Testing

### Run All Tests
```bash
docker-compose exec web python manage.py test
```

### Run Specific App Tests
```bash
# Test events
docker-compose exec web python manage.py test events

# Test bookings (includes concurrency tests)
docker-compose exec web python manage.py test bookings

# Test user management
docker-compose exec web python manage.py test user
```

### Test Coverage
```bash
docker-compose exec web python -m pytest --cov=.
```

### Concurrency Testing
The booking tests include race condition scenarios:
- Multiple simultaneous booking attempts
- Capacity validation under load
- Cancellation and reactivation edge cases

## 🔧 Development

### Project Structure
```
event_scheduling_system/
├── events/           # Event management
│   ├── models.py     # Event model and properties
│   ├── views.py      # Event CRUD operations
│   ├── serializers.py # Event data validation
│   └── tests.py      # Event tests
├── bookings/         # Reservation system
│   ├── models.py     # Booking model with concurrency
│   ├── views.py      # Booking operations
│   ├── serializers.py # Booking validation with locking
│   └── tests.py      # Comprehensive booking tests
├── user/             # User management
│   ├── models.py     # User profiles and history
│   ├── views.py      # Auth and profile operations
│   └── tests.py      # User tests
└── event_scheduling_system/  # Django settings
    ├── settings.py   # Application configuration
    └── urls.py       # URL routing
```

### Key Design Decisions

#### 1. Separate User Roles
- **Organizers**: Event creators with management capabilities
- **Customers**: Event attendees with booking capabilities
- **Clear separation**: Prevents role confusion and security issues

#### 2. Generic History Logging
- **HistoryPoint model**: Tracks all user actions generically
- **JSON details**: Flexible storage for action-specific data
- **Audit trail**: Complete system activity logging

#### 3. Status-Based Booking Management
- **Active/Cancelled states**: Simple but effective booking lifecycle
- **Reactivation support**: Cancelled bookings can be reactivated
- **Capacity management**: Automatic slot calculation

#### 4. Comprehensive Validation
- **Model-level validation**: Django model constraints
- **Serializer validation**: Business logic validation
- **View-level permissions**: Role-based access control

## 🐳 Docker Commands

### Development
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test
```

### Database Operations
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Reset database (WARNING: Deletes all data)
docker-compose exec web python manage.py flush
```

## 🔒 Security Features

### Authentication
- **Token-based authentication**: Secure API access
- **Role-based permissions**: Organizer vs Customer access control
- **Session management**: Proper logout and token deletion

### Data Protection
- **Input validation**: Comprehensive serializer validation
- **SQL injection prevention**: Django ORM protection
- **XSS protection**: Django's built-in security features

### Business Logic Security
- **Ownership validation**: Users can only modify their own data
- **Capacity enforcement**: Prevents overbooking at database level
- **Time validation**: Prevents booking invalid time periods

## 📈 Performance Considerations

### Database Optimization
- **Indexes**: Proper database indexing on frequently queried fields
- **Select related**: Optimized queries to reduce database hits
- **Pagination**: API responses are paginated for large datasets

### Concurrency Performance
- **Minimal locking**: Only locks during critical booking operations
- **Fast validation**: Efficient capacity calculation
- **Atomic operations**: Prevents database inconsistencies

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000
# Or use different port in docker-compose.yml
```

#### 2. Database Issues
```bash
# Reset database
docker-compose down
docker volume prune
docker-compose up --build
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Debugging
```bash
# Access container shell
docker-compose exec web bash

# Check Django settings
docker-compose exec web python manage.py check

# View application logs
docker-compose logs -f web
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Docker and Django logs
3. Ensure all prerequisites are met
4. Verify environment variables are set correctly

---

**Built with Django REST Framework, Docker, and comprehensive concurrency handling.**
