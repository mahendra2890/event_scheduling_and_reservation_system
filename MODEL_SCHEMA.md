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

Please note that it is advisable to delete the db.sqlite3 file : I have kept it so there is some data to start with even as you do it for the first time



Test for high concurrency/reliability/prevent overbooking case:
test_concurrent_booking_race_condition


What did I do? Created an atomic transaction with lock on row. I wanted to created a distributed lock with redis but unfortunately did not get enough time to set up redis here.


















---- AI generated detailed version -----




# Database Model Schema

## 📊 Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│      User       │         │    Organizer    │         │     Customer    │
│  (Django Auth)  │         │                 │         │                 │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id              │         │ id              │         │ id              │
│ username        │◄────────┤ user            │         │ user            │◄────────┐
│ email           │  1:1    │ organization_name│        │ created_at      │  1:1    │
│ password        │         │ business_address│        │ updated_at      │         │
│ first_name      │         │ created_at      │         └─────────────────┘         │
│ last_name       │         │ updated_at      │                                      │
│ is_active       │         └─────────────────┘                                      │
│ date_joined     │                                  ┌─────────────────┐             │
└─────────────────┘                                  │     Booking     │             │
                                                     ├─────────────────┤             │
                                                     │ id              │             │
                                                     │ attendee        │─────────────┘
                                                     │ event           │
                                                     │ booking_date    │
                                                     │ status          │
                                                     └─────────────────┘
                                                              │
                                                              │ N:1
                                                              ▼
                                                     ┌─────────────────┐
                                                     │      Event      │
                                                     ├─────────────────┤
                                                     │ id              │
                                                     │ title           │
                                                     │ description     │
                                                     │ start_time      │
                                                     │ end_time        │
                                                     │ capacity        │
                                                     │ creator         │◄────────┐
                                                     │ created_at      │  1:N    │
                                                     │ updated_at      │         │
                                                     └─────────────────┘         │
                                                                                 │
                                                     ┌─────────────────┐         │
                                                     │  HistoryPoint   │         │
                                                     ├─────────────────┤         │
                                                     │ id              │         │
                                                     │ user            │─────────┘
                                                     │ action          │
                                                     │ content_type    │
                                                     │ object_id       │
                                                     │ details         │
                                                     │ created_at      │
                                                     └─────────────────┘
```

## 🔗 Model Relationships

### 1. User Management
```
User (Django Auth)
├── organizer_profile (OneToOne) → Organizer
└── customer_profile (OneToOne) → Customer

Organizer
├── user (OneToOne) → User
└── created_events (OneToMany) → Event

Customer
├── user (OneToOne) → User
└── bookings (OneToMany) → Booking
```

### 2. Event System
```
Event
├── creator (ForeignKey) → Organizer
├── bookings (OneToMany) → Booking
└── Properties:
    ├── available_slots (calculated)
    ├── is_full (calculated)
    ├── is_past (calculated)
    └── is_ongoing (calculated)
```

### 3. Booking System
```
Booking
├── attendee (ForeignKey) → Customer
├── event (ForeignKey) → Event
├── Constraints:
│   └── unique_together: (attendee, event)
└── Methods:
    └── cancel() → Booking
```

### 4. History Tracking
```
HistoryPoint (Generic)
├── user (ForeignKey) → User
├── content_object (GenericForeignKey) → Any Model
└── Class Methods:
    └── log_action(user, action, obj, details) → HistoryPoint
```

## 📋 Field Details

### Event Model
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `title` | CharField(200) | Event title | Required |
| `description` | TextField | Event description | Optional |
| `start_time` | DateTimeField | Event start time | Required, > now |
| `end_time` | DateTimeField | Event end time | Required, > start_time |
| `capacity` | PositiveIntegerField | Maximum attendees | Required, > 0 |
| `creator` | ForeignKey(Organizer) | Event creator | Required |
| `created_at` | DateTimeField | Creation timestamp | Auto |
| `updated_at` | DateTimeField | Last update timestamp | Auto |

### Booking Model
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `attendee` | ForeignKey(Customer) | Booking customer | Required |
| `event` | ForeignKey(Event) | Booked event | Required |
| `booking_date` | DateTimeField | Booking timestamp | Auto |
| `status` | CharField(16) | Booking status | 'active' or 'cancelled' |

### Organizer Model
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | OneToOneField(User) | Associated user | Required |
| `organization_name` | CharField(100) | Organization name | Required |
| `business_address` | TextField | Business address | Required |
| `created_at` | DateTimeField | Creation timestamp | Auto |
| `updated_at` | DateTimeField | Last update timestamp | Auto |

### Customer Model
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | OneToOneField(User) | Associated user | Required |
| `created_at` | DateTimeField | Creation timestamp | Auto |
| `updated_at` | DateTimeField | Last update timestamp | Auto |

### HistoryPoint Model
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `user` | ForeignKey(User) | User who performed action | Required |
| `action` | CharField(20) | Action performed | create/update/delete/etc. |
| `content_type` | ForeignKey(ContentType) | Model type | Required |
| `object_id` | PositiveIntegerField | Object ID | Required |
| `details` | JSONField | Action details | Optional |
| `created_at` | DateTimeField | Action timestamp | Auto |

## 🔒 Constraints and Indexes

### Unique Constraints
```python
# Booking Model
unique_together = [('attendee', 'event')]  # Prevents duplicate bookings
```

### Database Indexes
```python
# Booking Model
indexes = [
    models.Index(fields=['attendee']),     # Fast attendee lookups
    models.Index(fields=['event']),        # Fast event lookups
    models.Index(fields=['status']),       # Fast status filtering
]

# HistoryPoint Model
indexes = [
    models.Index(fields=['user', 'action']),           # User action history
    models.Index(fields=['content_type', 'object_id']), # Object history
    models.Index(fields=['created_at']),               # Time-based queries
]
```

### Model Validation
```python
# Event Model
def clean(self):
    if self.end_time <= self.start_time:
        raise ValidationError('End time must be after start time.')
    if self.capacity < 1:
        raise ValidationError('Capacity must be at least 1.')

# Booking Model
def cancel(self):
    if self.status != 'active':
        raise ValueError('Only active bookings can be cancelled.')
    if self.event.is_ongoing or self.event.is_past:
        raise ValueError('Cannot cancel booking for events that have started.')
```

## 🔄 Data Flow

### Booking Creation Flow
```
1. Customer submits booking request
2. System validates:
   - Event exists and is not full
   - Event is not past/ongoing
   - Customer doesn't have existing booking
3. System locks event row (select_for_update)
4. System re-validates capacity after lock
5. System creates booking record
6. System logs action in HistoryPoint
7. System releases lock
```

### Event Capacity Calculation
```
available_slots = event.capacity - event.bookings.filter(status='active').count()
is_full = available_slots <= 0
```

### History Tracking Flow
```
1. User performs action (create/update/delete/cancel)
2. System calls HistoryPoint.log_action()
3. System creates HistoryPoint record with:
   - User who performed action
   - Action type
   - Target object (generic foreign key)
   - Additional details (JSON)
   - Timestamp
```

## 📊 Query Examples

### Get Event with Available Slots
```python
# Get all events with available capacity
events = Event.objects.annotate(
    active_bookings=Count('bookings', filter=Q(bookings__status='active'))
).filter(
    active_bookings__lt=F('capacity')
)
```

### Get User's Booking History
```python
# Get all bookings for a customer
customer_bookings = Booking.objects.filter(
    attendee__user=user
).select_related('event', 'attendee__user')
```

### Get Organizer's Event Bookings
```python
# Get all bookings for organizer's events
organizer_bookings = Booking.objects.filter(
    event__creator__user=user
).select_related('event', 'attendee__user', 'event__creator')
```

### Get User Action History
```python
# Get user's recent actions
user_history = HistoryPoint.objects.filter(
    user=user
).select_related('content_type').order_by('-created_at')
```

## 🎯 Key Design Principles

### 1. Separation of Concerns
- **User Management**: Separate Organizer and Customer roles
- **Event Management**: Centralized event logic with capacity management
- **Booking System**: Reservation logic with concurrency protection
- **History Tracking**: Generic logging for all actions

### 2. Data Integrity
- **Foreign Key Constraints**: Ensure referential integrity
- **Unique Constraints**: Prevent duplicate bookings
- **Validation**: Business logic validation at model level
- **Transactions**: Atomic operations for critical changes

### 3. Performance Optimization
- **Database Indexes**: Optimize common query patterns
- **Select Related**: Reduce database queries
- **Property Methods**: Efficient calculated fields
- **Generic Foreign Keys**: Flexible history tracking

### 4. Scalability
- **Normalized Design**: Efficient data storage
- **Indexed Queries**: Fast data retrieval
- **Generic Logging**: Extensible history system
- **Concurrency Protection**: Database-level locking

---

**This schema provides a robust foundation for the Event Scheduling System with proper relationships, constraints, and performance optimizations.**
