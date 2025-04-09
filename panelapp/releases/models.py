from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
)
from functools import singledispatch

from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from model_utils.models import (
    TimeFramedModel,
    TimeStampedModel,
)
from returns.result import (
    Failure,
    Result,
    Success,
)

from accounts.models import User
from panels.models import (
    GenePanelSnapshot,
    HistoricalSnapshot,
)
from releases import domain_logic
from releases.utils import parse_sort_field


class Release(TimeStampedModel):
    """Manage and apply batch changes to panels"""

    name = models.CharField(
        max_length=255, unique=True, validators=[MinLengthValidator(1)]
    )
    promotion_comment = models.TextField(null=True)
    panels = models.ManyToManyField(GenePanelSnapshot, through="ReleasePanel")

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("releases:detail", kwargs={"pk": self.pk})


@dataclass
class AlreadyDeployed:
    timestamp: datetime


class ReleaseDeployment(TimeFramedModel):
    """Release deployment state"""

    release = models.OneToOneField(
        Release, on_delete=models.CASCADE, related_name="deployment"
    )

    def deploy(self, user: User, now: datetime) -> Result[None, AlreadyDeployed]:
        if self.end is not None:  # type: ignore
            return Failure(AlreadyDeployed(timestamp=self.end))  # type: ignore

        for release_panel in (
            self.release.releasepanel_set.select_for_update()  # type: ignore
            .prefetch_related(
                "panel",
                "panel__genepanelsnapshot_set",
                "panel__genepanelsnapshot_set__panel",
                "panel__genepanelsnapshot_set__panel__signed_off",
            )
            .all()
        ):
            release_panel.deploy(user, now)

        self.end = timezone.now()

        self.save()

        return Success(None)

    def elapsed(self) -> timedelta | None:
        if self.start is None:
            return None
        if self.end is None:
            return timezone.now() - self.start
        return self.end - self.start

    def timed_out(self) -> bool:
        elapsed = self.elapsed()
        return (
            self.end is None and elapsed is not None and elapsed > timedelta(minutes=30)
        )


class ReleasePanelQuerySet(models.query.QuerySet["ReleasePanel"]):
    def search(
        self,
        *,
        search: str | None,
        statuses: list[str] | None,
        types: list[str] | None,
        order_by: str | None,
    ) -> "ReleasePanelQuerySet":
        qs = self
        if order_by:
            sort_field, sort_direction = parse_sort_field(order_by)
            qs = qs.order_by(
                f"{'-' if sort_direction == 'desc' else ''}panel__panel__{sort_field}"
            )

        if statuses:
            q_status = Q()
            for status in statuses:
                q_status = q_status | Q(panel__panel__status=status)
            qs = qs.filter(q_status)

        if types:
            q_type = Q()
            for type_ in types:
                q_type = q_type | Q(panel__panel__types__slug=type_)
            qs = qs.filter(q_type)

        if search:
            qs = qs.filter(panel__panel__name__icontains=search)

        qs = qs.distinct()

        return qs


class ReleasePanel(models.Model):
    """Changes to be applied to a panel as part of a release"""

    class Meta:
        unique_together = [["panel", "release"]]

    objects = ReleasePanelQuerySet.as_manager()

    panel = models.ForeignKey(GenePanelSnapshot, on_delete=models.CASCADE)
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    promote = models.BooleanField()

    def as_deployed(self) -> domain_logic.PanelSnapshot:
        return domain_logic.DeployReleasePanel(
            created_at=timezone.now(), release_panel=convert(self)
        )().release_panel

    def deploy(self, user: User, now: datetime):
        deploy = domain_logic.DeployReleasePanel(
            created_at=now, release_panel=convert(self)
        )
        deployment = deploy()
        before_version = domain_logic.Version(
            major=self.panel.major_version, minor=self.panel.minor_version
        )
        signed_off_before = self.panel.panel.signed_off
        comment_before = self.panel.version_comment
        for command in deploy.commands:
            persist(command, self, user, now)

        ReleasePanelDeployment.objects.create(
            release_panel=self,
            before_id=HistoricalSnapshot.objects.only("pk")
            .get(
                panel=self.panel.panel,
                major_version=before_version.major,
                minor_version=before_version.minor,
            )
            .pk,
            signed_off_before=signed_off_before,
            comment_before=comment_before,
            after_id=HistoricalSnapshot.objects.only("pk")
            .get(
                panel=self.panel.panel,
                major_version=deployment.signed_off.major,
                minor_version=deployment.signed_off.minor,
            )
            .pk,
            signed_off_after=self.panel.panel.signed_off,
            comment_after=self.panel.version_comment,
        )


class ReleasePanelDeployment(models.Model):
    """ReleasePanel deployment state"""

    release_panel = models.OneToOneField(
        ReleasePanel, on_delete=models.CASCADE, related_name="deployment"
    )
    before = models.OneToOneField(
        HistoricalSnapshot,
        on_delete=models.CASCADE,
        related_name="release_deployment_before",
    )
    signed_off_before = models.OneToOneField(
        HistoricalSnapshot,
        on_delete=models.CASCADE,
        related_name="release_deployment_signed_off_before",
        null=True,
    )
    comment_before = models.TextField(null=True)
    after = models.OneToOneField(
        HistoricalSnapshot,
        on_delete=models.CASCADE,
        related_name="release_deployment_after",
    )
    signed_off_after = models.OneToOneField(
        HistoricalSnapshot,
        on_delete=models.CASCADE,
        related_name="release_deployment_signed_off_after",
        null=True,
    )
    comment_after = models.TextField(null=True)


@singledispatch
def convert(instance):
    raise NotImplementedError


@convert.register
def _(instance: GenePanelSnapshot) -> domain_logic.PanelSnapshot:
    return domain_logic.PanelSnapshot(
        panel_id=instance.panel.pk,
        name=instance.panel.name,
        version=domain_logic.Version(
            minor=instance.minor_version, major=instance.major_version
        ),
        signed_off=(
            domain_logic.Version(
                minor=instance.panel.signed_off.minor_version,
                major=instance.panel.signed_off.major_version,
            )
            if instance.panel.signed_off
            else None
        ),
        status=instance.panel.status,
        types={x.name for x in instance.panel.types.all()},
        comment=instance.version_comment,
    )


@convert.register
def _(instance: Release) -> domain_logic.Release:
    return domain_logic.Release(
        promotion_comment=instance.promotion_comment,
    )


@convert.register
def _(instance: ReleasePanel) -> domain_logic.ReleasePanel:
    return domain_logic.ReleasePanel(
        release=convert(instance.release),
        panel=convert(instance.panel),
        promote=instance.promote,
    )


def persist(
    command: domain_logic.Command,
    release_panel: ReleasePanel,
    user: User,
    now: datetime,
):
    match command:
        case domain_logic.Promote(comment=comment):
            release_panel.panel.promote(user, now, comment)
        case domain_logic.SignOff():
            release_panel.panel.sign_off(user, now)
