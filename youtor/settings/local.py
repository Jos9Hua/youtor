from .base import *


DEBUG = True

STATIC_DIR = os.path.join(BASE_DIR,'staticfiles')
ALLOWED_HOSTS = ['localhost', '127.0.0.1'] # or ['*']


STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_TEST_PUBLIC_KEY", "pk_test_UK5fm7dMAqlhGpOba90Fh9pT00YDurSpsi")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_TEST_SECRET_KEY", "sk_test_RNiWlFH7DLma6qTBjQLyXjzI00MPcFA34s")

SITE_ID=3
