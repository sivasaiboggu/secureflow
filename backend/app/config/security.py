from app.config.settings import settings

# Security configurations definitions
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Password strength criteria configurations
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_REQUIRE_NUMBERS = True
