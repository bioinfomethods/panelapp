import factory
from django.core import files
from PIL import Image

from panelapp.models import (
    File,
    HomeText,
    Image,
)


class HomeTextFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HomeText

    section: int
    title: str
    href: str
    text: str


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = File

    file: files.File
    title: str


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    image: Image
    alt: str
    title: str
