import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from google_auth_oauthlib.flow import Flow

from db.utils.user_utils import user_exists
from utils.auth_utils import AuthenticatedUser
from session.session_layer import create_random_session_string, validate_session
from utils.config_utils import get_settings
from utils.cookie_utils import set_conditional_cookie
from routes.email_routes import fetch_emails_to_db
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Logger setup
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# FastAPI router for Google login
router = APIRouter()

APP_URL = settings.APP_URL

@router.get("/login")
@limiter.limit("10/minute")
async def login(request: Request):
    """Handles Google OAuth2 login and authorization code exchange."""
    code = request.query_params.get("code")
    flow = Flow.from_client_secrets_file(
        settings.CLIENT_SECRETS_FILE,
        settings.GOOGLE_SCOPES,
        redirect_uri=settings.REDIRECT_URI,
    )

    try:
        if not code:
            authorization_url, state = flow.authorization_url(prompt="consent")
            return RedirectResponse(url=authorization_url)
        logger.info("Authorization code received, exchanging for token...")
        try:
            flow.fetch_token(code=code)
        except Exception as e:
            logger.error("Failed to fetch token: %s", e)
            return RedirectResponse(
                url=f"{settings.APP_URL}/errors?message=permissions_error",
                status_code=303
            )   
        try:
            creds = flow.credentials
        except Exception as e:
            logger.error("Failed to fetch credentials: %s", e)
            return RedirectResponse(
                url=f"{settings.APP_URL}/errors?message=credentials_error",
                status_code=303
            )  

        if not creds.valid:
            creds.refresh(Request())
            return RedirectResponse("/login", status_code=303)

        user = AuthenticatedUser(creds)
        session_id = request.session["session_id"] = create_random_session_string()

        # Set session details
        try:
            token_expiry = creds.expiry.isoformat()
        except Exception as e:
            logger.error("Failed to parse token expiry: %s", e)
            token_expiry = (
                datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            ).isoformat()

        request.session["token_expiry"] = token_expiry
        request.session["user_id"] = user.user_id
        request.session["creds"] = creds.to_json() 
        request.session["access_token"] = creds.token

        # NOTE: change redirection once dashboard is completed
        exists, last_fetched_date = user_exists(user)
        if exists:
            logger.info("User already exists in the database.")
            response = RedirectResponse(
                url=f"{settings.APP_URL}/processing", status_code=303
            )
            settings.background_tasks.add_task(fetch_emails_to_db, user, request, last_fetched_date, user_id=user.user_id)
            response.background = settings.background_tasks
            logger.info("Background task started for user_id: %s", user.user_id)
        else:
            request.session["is_new_user"] = True
            response = RedirectResponse(
                url=f"{settings.APP_URL}/dashboard", status_code=303
            )
            print("User does not exist")

        response = set_conditional_cookie(
            key="Authorization", value=session_id, response=response
        )

        return response
    except Exception as e:
        logger.error("Login error: %s", e)
        return HTMLResponse(content="An error occurred, sorry!", status_code=500)


@router.get("/logout")
async def logout(request: Request, response: RedirectResponse):
    logger.info("Logging out")
    request.session.clear()
    response.delete_cookie(key="__Secure-Authorization")
    response.delete_cookie(key="Authorization")
    return RedirectResponse(f"{APP_URL}", status_code=303)


@router.get("/me")
async def getUser(request: Request, user_id: str = Depends(validate_session)):
    if not user_id:
        raise HTTPException(
            status_code=401, detail="No user id found in session"
        )    
    return {"user_id": user_id}