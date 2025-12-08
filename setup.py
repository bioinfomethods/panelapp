"""TODO: module doc..."""

import os
from setuptools import setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_path, "./VERSION"), "r") as version_file:
    version = str(version_file.readline()).strip()


setup(
    name="panelapp",
    version=version,
    author="Antonio Rueda-Martin,Oleg Gerasimenko",
    author_email="antonio.rueda-martin@genomicsengland.co.uk,oleg.gerasimenko@genomicsengland.co.uk",
    url="https://github.com/genomicsengland/PanelApp2",
    description="PanelApp",
    license="Internal GEL use only",  # example license
    classifiers=[
        "Environment :: Other Environment",
        "Intended Audience :: Other Audience",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering",
    ],
    packages=["panelapp"],
    include_package_data=True,
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["django-debug-toolbar==4.4.6", "ipython==8.31.0", "Werkzeug==3.1.3"],
        "tests": [
            "pytest==8.3.4",
            "pytest-django==4.9.0",
            "faker==33.3.1",
            "factory_boy==3.3.0",
            "pytest-cov==6.0.0",
            "flake8==7.1.1",
        ],
    },
    install_requires=[
        # Core Django
        "django==4.2.21",
        "djangorestframework==3.16.0",
        "django-filter==22.1",
        # Django Extensions
        "django-extensions==3.2.3",
        "django-cors-headers==4.7.0",
        "django-model-utils==4.5.1",
        "django-object-actions==4.3.0",
        "django-markdownx==4.0.9",
        "django-autocomplete-light==3.12.1",
        "django-storages==1.14.6",
        "django-bootstrap3==25.3",
        "django-mathfilters==1.0.0",
        "django-admin-list-filter-dropdown==1.0.3",
        "django-markdown-deux==1.0.6",
        "django-qurl-templatetag==0.0.14",
        "django-click==2.4.1",
        "django-array-field-select-multiple==0.3.2",
        "djangoajax==3.3",
        # API/Docs
        "drf-yasg==1.21.10",
        "djangorestframework-jsonapi==6.1.0",
        "drf-nested-routers==0.93.5",
        "swagger-spec-validator==3.0.4",
        "flex==6.14.1",
        # Database
        "psycopg2-binary==2.9.10",
        "dj-database-url==2.3.0",
        # Task Queue (already upgraded)
        "celery==5.5.2",
        "kombu==5.5.3",
        # AWS
        "boto3==1.38.13",
        # Web Server
        "gunicorn==23.0.0",
        # Other
        "Markdown==3.8",
        "PyYAML==6.0.2",
        "requests==2.32.3",
        "pytz==2024.2",
        "python-jose[cryptography]==3.4.0",
        "jsonschema==4.23.0",
        "pycurl==7.45.6",
        "simple-json-log-formatter==0.5.5",
        "zstandard==0.25.0",
    ],
)
