from fastapi import FastAPI, HTTPException, UploadFile, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from mongoengine import *
from bson.objectid import ObjectId
import pandas as pd
import os
import jwt
import time


connect(host='mongodb://admin:%40ccessDenied321@192.168.1.42:27017/riyazdb?authSource=admin')

app = FastAPI()



# emp login and signup and jwt token------------------------------------------------------------

JWT_SECRET = "please_please_update_me_pleasekhgkj39586yh34uth58gh9uewrhg8j"
JWT_ALGORITHM = "HS256"


def token_response(token: str):
    return {
        "access_token": token
    }


def sign_jwt(user_id: str):
    payload = {
        "user_id": user_id,
        "expires": time.time() + 200
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)


def decode_jwt(token: str):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str):
        isTokenValid: bool = False

        try:
            payload = decode_jwt(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True

        return isTokenValid
    



class EmpSchema(BaseModel):
    fullname: str
    email: EmailStr
    password: str


class EmpLoginSchema(BaseModel):
    email: EmailStr
    password: str


class Emp(Document):
    fullname = StringField(required=True)
    email = EmailField(required=True)
    password = StringField(required=True)


@app.post("/emp/signup", tags=["emp"])
async def create_emp(emp: EmpSchema):
    try:
        emp = Emp(**dict(emp))
        emp.save()
        return sign_jwt(emp.email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def check_emp(data: EmpLoginSchema):
    emp = Emp.objects(email=data.email).first()
    if emp:
        return emp.password == data.password
    return False


@app.post("/emp/login", tags=["emp"])
async def emp_login(emp: EmpLoginSchema):
    try:
        if check_emp(emp):
            return sign_jwt(emp.email)
        return {
            "error": "Wrong login details!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))








# user crud operations------------------------------------------------------------


class User(Document):
    srno = IntField(required=True)
    first_name = StringField(required=True, max_length=200)
    last_name = StringField(required=True, max_length=200)
    gender = StringField(required=True, max_length=200)
    country = StringField(required=True, max_length=200)
    age = IntField(required=True)
    code = IntField(required=True)

class UserModel(BaseModel):
    srno: int
    first_name: str
    last_name: str
    gender: str
    country: str
    age: int
    code: int


def user_to_dict(user):
    return {
        "id": str(user.id),
        "srno": user.srno,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "gender": user.gender,
        "country": user.country,
        "age": user.age,
        "code": user.code,
    }

@app.get("/")
async def list_all_users():
    try:
        users = User.objects()
        return [user_to_dict(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

        
@app.post("/users/")
async def create_user(user: UserModel):
    try:
        # Check if a user with the same srno already exists
        if User.objects(srno=user.srno):
            raise HTTPException(status_code=400, detail="User already exists")
        new_user = User(**dict(user))
        new_user.save()
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.put("/users/{user_id}")
async def update_user(user_id: str, updated_user: UserModel):
    try:
        # Check if a user with the same srno already exists
        if User.objects(srno=updated_user.srno):
            raise HTTPException(status_code=400, detail="User already exists")
        id = ObjectId(user_id)
        user = User.objects.get(id=id)
        user.update(**dict(updated_user))
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")


@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    try:
        id = ObjectId(user_id)
        user = User.objects.get(id=id)
        user.delete()
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")



# improt data from excel
@app.post("/users/upload_excel/")
async def upload_users_from_excel(file: UploadFile):
    try:
        # Read the Excel file
        df = pd.read_excel(file.file)

        # List to hold new users
        new_users = []

        # Iterate over the rows and create User documents
        for _, row in df.iterrows():
            user_data = {
                "srno": row["srno"],
                "first_name": row["First Name"],
                "last_name": row["Last Name"],
                "gender": row["Gender"],
                "country": row["Country"],
                "age": row["Age"],
                "code": row["code"]
            }
            # Check if a user with the same srno already exists
            if not User.objects(srno=user_data["srno"]):
                new_users.append(User(**user_data))

        # Bulk insert new users
        if new_users:
            User.objects.insert(new_users)

        return {"message": "Users uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# Get all users with pagination
@app.get("/users/")
async def get_users(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1)):
    try:
        skip = (page - 1) * per_page
        users = User.objects.skip(skip).limit(per_page)
        return [user_to_dict(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# Get all users with filter
@app.get("/users/filter/")
async def get_users(srno: int = None, first_name: str = None, last_name: str = None, gender: str = None, country: str = None, age: int = None, code: int = None):
    try:
        query = {}
        if srno:
            query["srno"] = srno
        if first_name:
            query["first_name"] = first_name
        if last_name:
            query["last_name"] = last_name
        if gender:
            query["gender"] = gender
        if country:
            query["country"] = country
        if age:
            query["age"] = age
        if code:
            query["code"] = code
        users = User.objects(**query)
        return [user_to_dict(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")



# export data to excel
@app.get("/users/export_excel/", dependencies=[Depends(JWTBearer())], tags=["posts"])
async def export_users_to_excel():
    try:
        users = User.objects()
        data = {
            "srno": [],
            "first_name": [],
            "last_name": [],
            "gender": [],
            "country": [],
            "age": [],
            "code": []
        }
        
        for user in users:
            data["srno"].append(user.srno)
            data["first_name"].append(user.first_name)
            data["last_name"].append(user.last_name)
            data["gender"].append(user.gender)
            data["country"].append(user.country)
            data["age"].append(user.age)
            data["code"].append(user.code)
        df = pd.DataFrame(data)
        print(df)
        file_path = os.path.join(os.path.dirname(__file__), "users_export.xlsx")
        df.to_excel(file_path, index=False)
        return {"message": "Users exported successfully", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error {e}")
    





