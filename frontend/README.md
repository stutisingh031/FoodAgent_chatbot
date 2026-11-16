# Freshly customer support chat

A responsive React chat UI for the FastAPI support backend in this repository.

## Run it

1. Start the backend from the repository root with `uvicorn app.main:app --reload`, or from this folder with `./run-backend.ps1` (PowerShell).
2. In `frontend/`, run `npm install` and then `npm run dev`.
3. Open the local URL Vite prints. By default, frontend API calls use Vite's same-origin `/api` proxy to `127.0.0.1:8000`, avoiding browser CORS issues. Set `VITE_API_URL` only when your backend runs elsewhere.

The backend needs its database and Gemini API key configured for AI replies. For seeded local accounts, run `python seed.py` from the repository root; the seed script defines the demo email addresses and password.

## Backend integration

The UI uses `GET /chat/options`, `POST /chat`, `GET /chat/{session_id}/history`, `GET /orders/recent`, `POST /auth/login`, `POST /auth/register`, and `POST /support/tickets`. It keeps the conversation session in local storage and restores chat history on sign-in. The current `/chat` implementation always returns `handoff_required: false`; if a later backend version returns a handoff and ticket ID, the UI displays the ticket status. A customer can also explicitly request human follow-up, which creates a `general_support` ticket with high priority.

Creating a ticket records a request for the support team. The backend does not currently connect customers to a live human agent or expose ticket updates in the chat, and the interface explains that to the customer.
