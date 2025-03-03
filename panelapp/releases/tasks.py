import logging
from typing import cast

from django.db import (
    DatabaseError,
    transaction,
)
from django.utils import timezone

from accounts.models import User
from panelapp.celery import app
from releases.models import (
    Release,
    ReleaseDeployment,
)

logger = logging.getLogger(__name__)


@app.task
@transaction.atomic
def deploy_release(pk: int, user_pk: int):
    try:
        release = Release.objects.select_for_update(nowait=True).get(pk=pk)
    except DatabaseError:
        logger.info("Release already being updated", exc_info=True)
        return

    deployment = cast(ReleaseDeployment, release.deployment)  # type: ignore

    user = User.objects.get(pk=user_pk)
    deployment.deploy(user, timezone.now()).unwrap()
