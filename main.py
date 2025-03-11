from fastapi import FastAPI, HTTPException, UploadFile, Query
from pydantic import BaseModel
from mongoengine import *
from bson.objectid import ObjectId
import pandas as pd
import datetime
from typing import List


connect(host='mongodb://admin:%40ccessDenied321@192.168.1.42:27017/riyazdb?authSource=admin')

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


app = FastAPI()

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