import os
from dotenv import load_dotenv

load_dotenv()

TOKEN_TG = os.getenv("TG_AI_TOKEN")
TOKEN_HUG = os.getenv("TOKEN_HUG")
MODEL_NAME = os.getenv("MODEL_NAME")
API_URL = os.getenv("API_URL")
YA_TOKEN = os.getenv("YA_AI_TOKEN")
