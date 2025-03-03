"""
Domain logic for releases.

This enables simulating a release for the purposes of predicting
panel state after a deployment.

This logic is decoupled from persistence whose responsibility lies in
the releases.models module.
"""

import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime

from jinja2.sandbox import ImmutableSandboxedEnvironment


@dataclass
class PanelSnapshot:
    panel_id: int
    name: str
    version: "Version"
    signed_off: "Version | None"
    status: str
    types: set[str]
    comment: str | None

    def types_json(self) -> str:
        return json.dumps(sorted(self.types), indent=0)

    def increment_minor_version(self) -> "PanelSnapshot":
        return dataclasses.replace(self, version=self.version.increment_minor())

    def promote(self, comment: str | None) -> "PanelSnapshot":
        if self.comment and comment:
            comment = f"{comment}\n\n{self.comment}"
        else:
            comment = self.comment or comment

        return dataclasses.replace(
            self, version=self.version.increment_major(), comment=comment
        )

    def sign_off(self) -> "PanelSnapshot":
        return dataclasses.replace(
            self, signed_off=self.version
        ).increment_minor_version()

    def add_types(self, types: set[str]) -> "PanelSnapshot":
        return dataclasses.replace(self, types=self.types | types)


@dataclass
class Version:
    minor: int
    major: int

    def increment_minor(self) -> "Version":
        return dataclasses.replace(self, minor=self.minor + 1)

    def increment_major(self) -> "Version":
        return dataclasses.replace(self, major=self.major + 1, minor=0)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass
class Release:
    promotion_comment: str | None


@dataclass
class ReleasePanel:
    release: Release
    panel: PanelSnapshot
    promote: bool


@dataclass
class ReleasePanelDeployment:
    created_at: datetime
    release_panel: ReleasePanel
    signed_off: Version


@dataclass
class ReleasePanelDeploymentHistory:
    before: ReleasePanel
    after: ReleasePanel


@dataclass
class DeployReleasePanel:
    """
    Encapsulates the command for deploying a release panel
    """

    created_at: datetime
    release_panel: ReleasePanel

    @property
    def commands(self) -> list["Command"]:
        commands = []
        if self.release_panel.promote:
            template_environment = ImmutableSandboxedEnvironment()
            comment_template = template_environment.from_string(
                self.release_panel.release.promotion_comment or ""
            )

            comment = comment_template.render(
                {
                    "now": DateTime(
                        yyyy_mm_dd_hh_mm=self.created_at.strftime("%Y-%m-%d %H:%M")
                    ),
                    "version": self.release_panel.panel.version.increment_major(),
                }
            )
            commands.append(Promote(comment))
        return commands + [SignOff()]

    def __call__(self) -> ReleasePanelDeployment:
        snapshot = self.release_panel.panel
        signed_off = None
        for command in self.commands:
            snapshot = handle(snapshot, command)
            if isinstance(command, SignOff):
                signed_off = snapshot.signed_off
        assert signed_off is not None
        return ReleasePanelDeployment(
            created_at=self.created_at,
            release_panel=dataclasses.replace(self.release_panel, panel=snapshot),
            signed_off=signed_off,
        )


@dataclass
class DateTime:
    yyyy_mm_dd_hh_mm: str


@dataclass
class Promote:
    comment: str | None


@dataclass
class SignOff:
    pass


Command = Promote | SignOff


def handle(snapshot: PanelSnapshot, command: Command) -> PanelSnapshot:
    """
    Handle the application of a Command to a PanelSnapshot which will mutate
    its state.
    """
    match command:
        case Promote(comment=comment):
            return snapshot.promote(comment)
        case SignOff():
            return snapshot.sign_off()
