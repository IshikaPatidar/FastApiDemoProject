from datetime import timedelta, datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request, Response, Form
from pydantic import BaseModel
from ..models import Users
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from ..database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = "longstringsecretkey8723541746913864353"
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

templates = Jinja2Templates(directory="fastapi_demo/templates/")


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not check_password_hash(user.hashed_password, password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            logout(request)
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User Could not Validate")


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post('/token', response_model=Token)
async def login_for_access_token(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False

    token = create_access_token(user.username, user.id, timedelta(minutes=60))

    response.set_cookie(key="access_token", value=token, httponly=True)
    return True


@router.get('/', response_class=HTMLResponse)
async def authenticate_page(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@router.post('/', response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse("login.html", {'request':request, 'msg': msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {'request': request, 'msg': msg})


@router.get('/logout')
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {'request': request, 'msg': msg})
    response.delete_cookie(key='access_token')
    return response


@router.get('/register', response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {'request': request})


@router.post('/register', response_class=HTMLResponse)
async def register_user(request: Request, email: str = Form(...), username: str = Form(...),
                        firstname: str = Form(...), lastname: str = Form(...), password: str =Form(...),
                        password2: str = Form(...), db: Session = Depends(get_db)):
    validation1 = db.query(Users).filter(Users.username == username).first()
    validation2 = db.query(Users).filter(Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = 'Invalid registration request'
        return templates.TemplateResponse("register.html", {"request": request, 'msg': msg})

    user_model = Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname

    hash_password = generate_password_hash(password, method='pbkdf2:sha256')
    user_model.hashed_password = hash_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg= "User successfully created"
    return templates.TemplateResponse('login.html', {'request': request, 'msg': msg})


@router.get('/change-password')
async def password(request: Request):
    return templates.TemplateResponse("change-password.html", {'request': request})


@router.post('/change-password')
async def change_password(request: Request, username: str = Form(...), password: str = Form(...),
                          password2: str = Form(...), db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    print(username)
    user_model = db.query(Users).filter(Users.username == username).first()
    msg = "User not found or Password incorrect"

    if user_model is not None:
        pasw = check_password_hash(user_model.hashed_password, password)
        if username == user_model.username and pasw:
            user_model.hashed_password = generate_password_hash(password2, method='pbkdf2:sha256')
            db.add(user_model)
            db.commit()
            msg = "Password Updated"
    return templates.TemplateResponse('login.html', {'request': request, 'msg':msg})


@router.get('/read', status_code=status.HTTP_200_OK)
async def read_user(db: db_dependency):
    return db.query(Users).all()

