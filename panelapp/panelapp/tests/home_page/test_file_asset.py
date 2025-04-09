import tempfile

import pytest
import responses
from django.core.files.base import ContentFile
from django.test import override_settings
from returns.result import Success

from panelapp.models import File
from panelapp.tests.factories import FileFactory
from panelapp.utils.home_page import (
    Created,
    FileAsset,
    FileDomainEvent,
    Missing,
)


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_success():
    asset = FileAsset(name="test.pdf", state=Missing())
    model = FileFactory.build(file=ContentFile(b"hello", name="files/test.pdf"))
    responses.get(
        "http://test.local/media/files/test.pdf",
        body=b"hello",
    )

    actual_events = asset.upload("http://test.local/media/files/test.pdf")

    [actual_model] = list(File.objects.all())

    assert actual_model.file.name == model.file.name

    with actual_model.file.open() as f:
        actual_content = f.read()
    with model.file.open() as f:
        expected_content = f.read()
    assert actual_content == expected_content

    assert actual_events == Success(
        [FileDomainEvent(pk=1, event=Created(name="test.pdf"))]
    )


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_failure_exception(mocker):
    asset = FileAsset(name="test.pdf", state=Missing())
    responses.get(
        "http://test.local/media/files/test.pdf",
        body=b"hello",
    )
    mocked_file = mocker.patch("panelapp.utils.home_page.File")
    mocked_file.return_value.save.side_effect = ValueError

    with pytest.raises(ValueError):
        asset.upload("http://test.local/media/files/test.pdf")

    models = list(File.objects.all())

    assert models == []


@responses.activate
@override_settings(MEDIA_ROOT=tempfile.TemporaryDirectory(prefix="mediatest").name)
@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_upload_failure_http():
    asset = FileAsset(name="test.pdf", state=Missing())
    responses.get("http://test.local/media/files/test.pdf", status=404)

    result = asset.upload("http://test.local/media/files/test.pdf")

    models = list(File.objects.all())

    assert models == []
    assert (
        str(result.failure())
        == "404 Client Error: Not Found for url: http://test.local/media/files/test.pdf"
    )
