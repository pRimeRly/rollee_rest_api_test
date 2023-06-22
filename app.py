import os
import uuid
from flask import Flask, request, jsonify, abort
from passlib.hash import pbkdf2_sha256
import requests

from db import db
from models import UserModel

# Initialize the flask instance
app = Flask(__name__)

# Configure the database URI
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")

# Initialize the database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

query_file_path = "queries/authenticate_query.graphql"


def load_query(query_path):
    """returns graphql query"""
    with open(query_path, "r") as query_file:
        query = query_file.read()

        return query


@app.route("/auth", methods=['POST'])
def login():
    # Get the username and password from the request data
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return (
            jsonify(
                {"error": "Username and password is required"}
            ),
            400
        )

    comet_api_endpoint = "https://api.comet.co/api/graphql"

    # Request headers for the API call
    headers = {
        "Accept": "application/json",
        "Accept-language": "en-US,en;q=0.9",
        "cache": "no-cache",
        "Content-type": "application/json",
        "authority": "app.comet.co"
    }

    payload = {
        "operationName": "authenticate",
        "variables": {
            "email": username,
            "password": password,
            "signupToken": None
        },
        "query": load_query(query_file_path)
    }

    response = requests.post(comet_api_endpoint, headers=headers, json=payload)
    response.raise_for_status()
    response_json = response.json()
    user = UserModel.query.filter(UserModel.username == username).first()
    if user and pbkdf2_sha256.verify(password, user.password):
        return {"token": user.token}

    # Generate a new token for the user
    token = uuid.uuid4().hex

    # Create a new user record in the database
    user = UserModel(
        username=username,
        password=pbkdf2_sha256.hash(password),
        user_data=response_json,
        token=token
    )
    db.session.add(user)
    db.session.commit()
    return {"token": user.token}


@app.route("/pull", methods=["POST"])
def retrieve_data():
    # Get the access token from the request headers
    access_token = request.headers.get("token")

    if not access_token:
        return abort(401, description="Access token is required")

    user = UserModel.query.filter(UserModel.token == access_token).first()
    if user:
        # Retrieve user data from the response JSON
        response_data = user.user_data.get("data").get("authenticate")
        experience_list = response_data.get("freelance").get("experiences")
        experiences = []
        skills = []

        # Extract experiences and skills from the response
        for experience in experience_list:
            company_name = experience.get("companyName")
            description = experience.get("description")

            experiences.append({"companyName": company_name, "description": description})

        for experience in experience_list:
            skills_list = experience.get("skills")
            for skill in skills_list:
                skill_name = skill.get("name")
                if skill_name:
                    skills.append(skill_name)

        # Prepare the user data to be returned
        user_data = {
            "User-Profile": {
                "fullName": response_data.get("fullName"),
                "profilePictureUrl": response_data.get("profilePictureUrl"),
                "email": response_data.get("email"),
                "phoneNumber": response_data.get("phoneNumber")
            },
            "Experiences": experiences,
            "Skills": skills,
        }
        return user_data
    abort(401, description="Authorization required")
