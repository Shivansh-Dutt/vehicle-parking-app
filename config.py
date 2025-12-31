import os

class Config:
    SECRET_KEY = "super-secret-key"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///parking.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
