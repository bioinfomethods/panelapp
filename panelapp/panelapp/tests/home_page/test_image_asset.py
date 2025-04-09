import tempfile

import pytest
import responses
from django.core.files.base import ContentFile
from django.test import override_settings
from returns.result import Success

from panelapp.models import Image
from panelapp.tests.factories import ImageFactory
from panelapp.utils.home_page import (
    Created,
    ImageAsset,
    ImageDomainEvent,
    Missing,
)


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_success():
    asset = ImageAsset(name="test.jpg", state=Missing())
    model = ImageFactory.build(image=ContentFile(b"hello", name="images/test.jpg"))
    responses.get(
        "http://test.local/media/images/test.jpg",
        body=b"hello",
    )

    actual_events = asset.upload("http://test.local/media/images/test.jpg")

    [actual_model] = list(Image.objects.all())

    assert actual_model.image.name == model.image.name

    with actual_model.image.open() as f:
        actual_content = f.read()
    with model.image.open() as f:
        expected_content = f.read()
    assert actual_content == expected_content

    assert actual_events == Success(
        [ImageDomainEvent(pk=1, event=Created(name="test.jpg"))]
    )


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_failure_exception(mocker):
    asset = ImageAsset(name="test.jpg", state=Missing())
    responses.get(
        "http://test.local/media/images/test.jpg",
        body=b"hello",
    )
    mocked_image = mocker.patch("panelapp.utils.home_page.Image")
    mocked_image.return_value.save.side_effect = ValueError

    with pytest.raises(ValueError):
        asset.upload("http://test.local/media/images/test.jpg")

    models = list(Image.objects.all())

    assert models == []


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_failure_http():
    asset = ImageAsset(name="test.jpg", state=Missing())
    responses.get("http://test.local/media/images/test.jpg", status=404)

    result = asset.upload("http://test.local/media/images/test.jpg")

    models = list(Image.objects.all())

    assert models == []
    assert (
        str(result.failure())
        == "404 Client Error: Not Found for url: http://test.local/media/images/test.jpg"
    )
