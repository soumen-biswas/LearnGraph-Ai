import os
os.environ['DEBUG']='True'
os.environ['_TEST_CONFIGURATION']='1'
os.environ.setdefault('SECRET_KEY','test-only-'+('x'*64))
os.environ.setdefault('DATABASE_URL','sqlite:///:memory:')
from .settings import *
CACHES={'default': {'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
ALLOWED_HOSTS=['testserver','localhost','127.0.0.1']
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
PUBLIC_BASE_URL='https://learn.example.com'
