import factory

from panels.tests.factories import (
    GenePanelSnapshotFactory,
    HistoricalSnapshotFactory,
)
from releases.models import (
    Release,
    ReleaseDeployment,
    ReleasePanel,
    ReleasePanelDeployment,
)


class ReleaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Release

    name = factory.Faker("word")


class ReleasePanelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleasePanel

    release = factory.SubFactory(ReleaseFactory)
    panel = factory.SubFactory(GenePanelSnapshotFactory)
    promote = False


class ReleaseDeploymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseDeployment

    release = factory.SubFactory(ReleaseFactory)


class ReleasePanelDeploymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleasePanelDeployment

    release_panel = factory.SubFactory(ReleasePanelFactory)
    before = factory.SubFactory(HistoricalSnapshotFactory)
    signed_off_before = factory.SubFactory(HistoricalSnapshotFactory)
    after = factory.SubFactory(HistoricalSnapshotFactory)
    signed_off_after = factory.SubFactory(HistoricalSnapshotFactory)
