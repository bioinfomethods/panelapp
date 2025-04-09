import uuid
from typing import cast

import pytest
from django.test import Client
from django.urls import reverse
from testfixtures import Comparison as C
from testfixtures.django import compare

from accounts.models import User
from releases.models import Release
from releases.tests.factories import ReleaseFactory


@pytest.mark.django_db
def test_list(client: Client, curator_user: User):
    release = cast(Release, ReleaseFactory(promotion_comment="Release comment"))

    client.login(username=curator_user.username, password="pass")

    res = client.get(reverse("releases:list"), {"deployment": "pending"})

    assert res.status_code == 200

    assert release.name in res.content.decode("utf-8")


@pytest.mark.django_db
def test_create(client: Client, curator_user: User):
    client.login(username=curator_user.username, password="pass")

    name = str(uuid.uuid4())

    res = client.post(
        reverse("releases:create"),
        {
            "name": name,
            "promotion_comment": "Promotion comment",
        },
    )

    assert res.status_code == 302

    compare(
        list(Release.objects.all()),
        [Release(name=name, promotion_comment="Promotion comment")],
        ignore_fields=["id"],
    )


@pytest.mark.django_db
def test_edit(client: Client, curator_user: User):
    release = cast(
        Release,
        ReleaseFactory(name=str(uuid.uuid4()), promotion_comment="Original comment"),
    )

    client.login(username=curator_user.username, password="pass")

    new_name = str(uuid.uuid4())

    res = client.post(
        reverse("releases:edit", args=(release.pk,)),
        {
            "name": new_name,
            "promotion_comment": "New comment",
        },
    )

    assert res.status_code == 302

    compare(
        list(Release.objects.all()),
        [Release(pk=release.pk, name=new_name, promotion_comment="New comment")],
    )
