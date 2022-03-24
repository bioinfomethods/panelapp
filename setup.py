"""TODO: module doc..."""

import os

from setuptools import (
    find_packages,
    setup,
)

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
        ],
        "tests": [
            "pytest==7.1.0",
            "pytest-cases==3.6.10",
            "pytest-django==4.5.2",
            "pytest-cov==3.0.0",
            "pytest-sugar==0.9.4",
            "flake8==3.5.0",
            "faker==13.3.2",
            "factory_boy==3.2.1",
            "responses==0.10.12",
        ],
    },
    install_requires=[
        "django==2.2.16",
        "PyYAML==5.3.1",
        "psycopg2-binary==2.8.6",
        "dj-database-url==0.5.0",
        "django-model-utils==3.2.0",
        "djangoajax==3.2",
        "djangorestframework==3.11.1",
        "django-extensions==2.2.9",
        "django-cors-headers==2.5.3",
        "django-autocomplete-light==3.5.1",
        "django-markdown-deux==1.0.5",
        "django-bootstrap3==10.0.1",
        "django-markdownx==2.0.28",
        "Markdown==3.3.4",
        "django-object-actions==0.10.0",
        "django-mathfilters==0.4.0",
        "celery==4.4.7",
        "requests==2.24.0",
        "django-admin-list-filter-dropdown==1.0.3",
        "pytz==2020.1",
        "gunicorn==19.9.0",
        "django-array-field-select==0.2.0",  # remove it? there are some migration deps
        "drf-yasg==1.17.1",
        "flex==6.14.0",
        "swagger-spec-validator==2.7.3",
        "djangorestframework-jsonapi==2.8.0",
        "drf-nested-routers==0.91",
        "django-qurl-templatetag==0.0.14",
        "django-click==2.2.0",  # TODO get rid of it, doesn't provide too much value
        "django-filter==2.3.0",
        "django-storages==1.10.1",
        "boto3==1.15.2",
        "pycurl==7.43.0.6",
        "python-jose==3.2.0",
        "click==7.1.2",
        "python-json-logger==0.1.11",
    ],
)
