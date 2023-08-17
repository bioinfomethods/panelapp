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
        "Programming Language :: Python :: 3.5",
        "Topic :: Scientific/Engineering",
    ],
    packages=["panelapp"],
    include_package_data=True,
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": [
            "django-debug-toolbar==3.1",
            "ipython==7.18.1",
            "Werkzeug==1.0.1",
            "pdbpp==0.10.2",
            "black==22.3.0",
        ],
        "tests": [
            "pytest==6.2.5",
            "pytest-cases==3.6.10",
            "pytest-django==4.5.2",
            "pytest-cov==3.0.0",
            "pytest-sugar==0.9.4",
            "pytest-mock==3.10.0",
            "flake8==3.5.0",
            "faker==13.3.2",
            "factory_boy==3.2.1",
            "responses==0.10.12",
            "pytest-pythonpath==0.7.4",
        ],
    },
    install_requires=[
        "Markdown==3.4.3",
        "PyYAML==6.0.1",
        "boto3==1.26.60",
        "celery==5.2.7",
        "click==8.1.3",
        "dj-database-url==1.2.0",
        "django-admin-list-filter-dropdown==1.0.3",
        "django-array-field-select==0.2.0",  # remove it? there are some migration deps
        "django-autocomplete-light==3.9.4",
        "django-bootstrap3==22.2",
        "django-click==2.3.0",  # TODO get rid of it, doesn't provide too much value
        "django-cors-headers==3.13.0",
        "django-extensions==2.2.9",
        "django-filter==22.1",
        "django-markdown-deux==1.0.6",
        "django-markdownx==4.0.2",
        "django-mathfilters==1.0.0",
        "django-model-utils==4.3.1",
        "django-object-actions==4.1.0",
        "django-qurl-templatetag==0.0.14",
        "django-storages==1.13.2",
        "django==3.2.20",
        "djangoajax==3.3",
        "djangorestframework-jsonapi==6.0.0",
        "djangorestframework==3.14.0",
        "drf-nested-routers==0.93.4",
        "drf-yasg==1.21.4",
        "flex==6.14.1",
        "gunicorn==20.1.0",
        "jsonschema<4.0",
        "psycopg2-binary==2.8.6",
        "pycurl==7.45.2",
        "python-jose==3.3.0",
        "python-json-logger==2.0.4",
        "pytz==2022.7.1",
        "requests==2.31.0",
        "swagger-spec-validator==3.0.3",
    ],
)
