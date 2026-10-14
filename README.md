# حفظ النعمة | Hifz Al-Na'ma

A responsive Arabic-first prototype for the surplus-food management project. The package includes a browser-based dashboard prototype and a FastAPI backend starter.

## What's included
- Responsive Arabic RTL dashboard for desktop and mobile.
- Surplus-food cards, search, category filters, and sorting.
- Demo reservation interactions.
- Add-surplus form with validation and dynamic listing updates.
- FastAPI starter endpoints for health checks, food listings, and reservations.

## Run the frontend
Open `frontend/index.html` in a browser. The current frontend uses demo data in the browser; it does not yet persist to the API/database.

For a local web server, from the project folder run:

```bash
python -m http.server 5500 --directory frontend
```

Then open `http://localhost:5500`.

## Run the backend API
Python 3.10+ recommended.

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API documentation: `http://127.0.0.1:8000/docs`
Health check: `http://127.0.0.1:8000/api/health`

## Current prototype limitations
- Demo cards and reservations in the frontend are not connected to the backend and reset on refresh.
- Backend data is held in memory and resets when the server restarts; MySQL integration is not implemented yet.
- Authentication, role permissions, file uploads, AI-based food recognition, Google Maps routing, push notifications, and production deployment require configuration and implementation.
- Never store passwords as plain text. Add secure authentication, input validation, authorization, audit logs, and food-safety policies before real-world use.

## Suggested next milestones
1. Connect frontend forms and reservation buttons to the API.
2. Add MySQL models/migrations and transactional reservation locking.
3. Add user roles (restaurant, charity, individual, admin) and secure authentication.
4. Integrate image storage and food-image recognition.
5. Integrate maps/geocoding and distance-based discovery.
6. Add notifications, admin analytics, tests, and deployment.
