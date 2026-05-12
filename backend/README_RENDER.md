# README for Render backend deployment

This backend is designed to be deployed on [Render](https://render.com/).

## Deployment Steps

1. Push your code to a public Git repository (e.g., GitHub).
2. Create a new Web Service on Render and connect your repository.
3. Render will automatically detect the `render.yaml` file and set up the service.
4. The backend will be served using FastAPI with Gunicorn and Uvicorn worker.

## Important Files
- `render.yaml`: Render service definition.
- `backend/requirements.txt`: Python dependencies.
- `backend/Procfile`: Start command for Gunicorn/Uvicorn.
- `backend/.renderignore`: Files/folders to exclude from deployment.

## Notes
- Make sure all backend dependencies are listed in `requirements.txt`.
- The backend must expose a FastAPI app as `app` in `app.py`.
- The service will listen on the port specified by the `PORT` environment variable.
