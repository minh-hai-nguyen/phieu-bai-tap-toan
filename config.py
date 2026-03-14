"""Configuration for the Math Education Web App."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Database paths
WEBAPP_DB = os.path.join(BASE_DIR, "webapp.db")
# Try local copy first (for Render), then project-level
_yccd_local = os.path.join(BASE_DIR, "yccd.db")
_yccd_project = os.path.join(PROJECT_DIR, "yccd-DESKTOP-BC98DI1.db")
YCCD_DB = _yccd_local if os.path.exists(_yccd_local) else _yccd_project

# JWT
SECRET_KEY = os.environ.get("SECRET_KEY", "math-edu-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Static files
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Image extraction
IMAGES_DIR = os.path.join(STATIC_DIR, "img", "exercises")

# Grade config
GRADES = [1, 2, 3, 4, 5]
WEEKS_PER_GRADE = 35
SPECIAL_UNITS = {36: "midterm", 37: "final"}
