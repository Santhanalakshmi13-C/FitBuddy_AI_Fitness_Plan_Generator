# FitBuddy — AI Fitness Plan Generator

FitBuddy is a FastAPI web application based on the supplied project document. It offers:
- A responsive Jinja2 frontend for collecting a user's name, user ID, age, weight, goal and intensity.
- A 7-day workout plan and a nutrition/recovery tip.
- Feedback-based plan revision, preserving original and revised versions.
- SQLite persistence through SQLAlchemy.
- A password-protected coach dashboard at `/view-all-users`.
- JSON endpoints and interactive FastAPI docs at `/docs`.
- Demo fallback responses if Gemini is not configured or temporarily unavailable.

## Requirements
- Python 3.11 or newer recommended
- VS Code
- Internet access and a Gemini API key for live AI responses (optional for demo mode)

## Setup in VS Code (Windows)
1. Extract the project ZIP and open the `fitbuddy_project` folder in VS Code (`File → Open Folder`).
2. Open **Terminal → New Terminal**.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
4. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt in VS Code and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
5. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. Copy `.env.example` to `.env`. In VS Code, right-click `.env.example` → Copy, paste, and rename the copy to `.env`.
7. For real Gemini output, add your Google AI Studio key to `GOOGLE_API_KEY=` in `.env`. Keep this key private and never commit `.env`. If you leave it blank, FitBuddy still runs in demo mode.
8. Change `ADMIN_PASSWORD` in `.env` before opening the coach dashboard.
9. Start the server from the project root:
   ```powershell
   python -m uvicorn app.main:app --reload
   ```
10. Open `http://127.0.0.1:8000`.

## Setup in VS Code (Ubuntu/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY and a private ADMIN_PASSWORD if using Gemini/admin.
python -m uvicorn app.main:app --reload
```
If `venv` creation fails on Ubuntu, install the venv package: `sudo apt install python3-venv`.

## Test the app
- Homepage: `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/health` — expected `{"status":"ok","service":"FitBuddy"}`
- API documentation: `http://127.0.0.1:8000/docs`
- Coach dashboard: `http://127.0.0.1:8000/view-all-users` — browser prompts for HTTP Basic credentials. Use `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`.
- Generate a plan using the web form. Try user ID `student_01`, age `20`, weight `60`, goal `general_wellness`, intensity `low`.
- Submit feedback on the result page and confirm the revised plan appears.
- Stop the server with `Ctrl+C`.

### API smoke test
In `/docs`, expand `POST /api/generate-workout`, click **Try it out**, and use:
```json
{
  "username": "Test User",
  "user_id": "test_user_01",
  "age": 20,
  "weight": 60,
  "goal": "general_wellness",
  "intensity": "low"
}
```
The response includes `plan_id`, `workout_plan`, `nutrition_tip`, and `demo_mode`. Use the returned plan ID in `POST /api/submit-feedback` as the query parameter `plan_id`; request body:
```json
{
  "user_id": "test_user_01",
  "feedback": "Please include more gentle mobility and another recovery day."
}
```
Admin endpoints require HTTP Basic authentication.

## API routes
| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Homepage |
| POST | `/generate-workout` | HTML form generation |
| POST | `/submit-feedback` | HTML feedback update |
| GET | `/view-all-users` | Protected coach dashboard |
| GET | `/health` | Health check |
| POST | `/api/generate-workout` | JSON plan generation |
| POST | `/api/submit-feedback?plan_id=1` | JSON feedback update |
| GET | `/api/users` | Protected JSON admin listing |

## Gemini configuration
This project uses the current `google-genai` Python SDK rather than the older `google-generativeai` package shown in some older examples. Model availability depends on the Google AI project/key. If your account does not have access to the default models, set `GEMINI_WORKOUT_MODEL` and `GEMINI_TIP_MODEL` in `.env` to model IDs available to your key. When Gemini calls fail, the app logs no secret key and returns a clearly labeled fallback response.

## Safety and privacy
FitBuddy generates general wellness suggestions, not medical care. It does not diagnose, prescribe diets, or promise outcomes. The dashboard is protected with HTTP Basic authentication, but this starter project is intended for local development; do not expose it publicly without HTTPS, stronger identity/access controls, rate limiting, and a privacy review. User-entered age and weight are stored locally in `fitbuddy.db`. Delete that file to reset the local database while the server is stopped.
