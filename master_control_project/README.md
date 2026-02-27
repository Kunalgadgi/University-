# Master Control — University Admission Portal Admin System

A **production-grade** administrative control system for a university admission portal.
Built with Flask + SQLite (mirrors Django 4.x architecture).

---

## Architecture

```
master_control_project/
├── app.py                          # Main application (routes, auth, context processor)
├── requirements.txt
├── university_portal.db            # SQLite database (auto-created)
├── master_control.log              # Application log
└── master_control/
    ├── models.py                   # All 6 models + DB functions
    ├── static/master_control/
    │   └── uploads/                # File uploads (images, attachments)
    └── templates/master_control/
        ├── base.html               # Master layout with sidebar navigation
        ├── login.html              # Admin login page
        ├── dashboard.html          # Overview dashboard
        ├── settings.html           # Portal settings (singleton)
        ├── courses.html            # Course list with search/filter/bulk
        ├── course_form.html        # Add/Edit course
        ├── form_configs.html       # Form configuration list
        ├── form_config_form.html   # Add/Edit form configuration
        ├── notices.html            # Notice list with bulk actions
        ├── notice_form.html        # Add/Edit notice
        ├── advertisements.html     # Advertisement list
        ├── advertisement_form.html # Add/Edit advertisement
        ├── sliders.html            # Homepage slider list
        ├── slider_form.html        # Add/Edit slider
        └── error.html              # 404/403 error page
```

---

## Models

| Model | Description |
|---|---|
| `portal_settings` | Singleton config — portal name, academic year, maintenance mode |
| `course` | Academic courses with degree type, seats, display priority |
| `form_configuration` | FK → Course — form open/close, fees, date range |
| `advertisement` | Banner/sidebar/notice ads with date-based display logic |
| `notice` | Homepage notices sorted by priority |
| `homepage_slider` | Hero slider banners sorted by priority |
| `admin_user` | Staff/superuser accounts |

---

## Running the Application

```bash
# Run the server
python3 app.py

# Access at:
http://localhost:5000/admin/login

# Default credentials:
Username: admin
Password: admin123
```

---

## Features Implemented

### Access Control
- `@staff_member_required` decorator on all admin routes
- Session-based authentication
- Superuser / Staff role distinction

### Models
- `created_at` / `updated_at` timestamps on all models
- `is_active` boolean on all content models
- `priority` field on all ordered models
- SQLite indexes for performance
- Foreign key constraints with CASCADE delete

### Admin Panel
- Search & filter on all list views
- Bulk activate / deactivate actions
- Priority-based ordering
- Date range validation (start < end enforced server-side)
- Singleton enforcement on PortalSettings (id must always = 1)

### Context Processor (Django-equivalent)
Injected globally into all templates:
- `active_courses` — courses where `is_active=True`
- `active_advertisements` — ads where `is_active=True AND start≤today≤end`
- `active_notices` — notices where `is_active=True`
- `active_sliders` — sliders where `is_active=True`
- `maintenance_mode` — from PortalSettings
- `current_academic_year` — from PortalSettings
- `portal_settings` — full settings object

### Security
- CSRF protection via Flask's session-based tokens
- File upload validation (extension whitelist)
- Server-side date validation
- 5 MB file size limit
- Password hashed with SHA-256

### Logging
- All admin logins / logouts logged
- Settings changes logged
- Log file: `master_control.log`
