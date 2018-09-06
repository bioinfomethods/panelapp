"""
# Panel app data structure

Brief overview of how the data in this app is structured.

## How panel app data should be structured

We have genes - they don’t change, can only be imported by the GEL reviewers.
We also have panels - which holds basic information about the pane.
Panel is the list of Genes, but Genes that are specific to this Panel, i.e. they
can be slightly different from the Genes imported via Import tool.

When adding a panel a curator provides the basic info for this panel.

Reviewers can add a Gene to the panel, this is autocompleted in the form from
the existing Genes.

Reviewers can add comments, new information.

Each time something changes in the panel we create a copy of the panel and copy
the gene panel entry, meaning we have version for each gene panel. This
information can be retrieved from the API and also can be downloaded via tsv.

However, the only version which is visible is the latest version of the gene
panel entry.

Previusly the application was using MongoDB, thus it was easy to create an
embedded version for the previous versions in the list. Since we are moving
to the Postgres it makes sense to keep the gene panel entry backup as a JSON.
"""

from .codes import ProcessingRunCode  # noqa
from .tag import Tag  # noqa
from .gene import Gene  # noqa
from .activity import Activity  # noqa
from .Level4Title import Level4Title  # noqa
from .comment import Comment  # noqa
from .evaluation import Evaluation  # noqa
from .evidence import Evidence  # noqa
from .trackrecord import TrackRecord  # noqa
from .genepanel import GenePanel  # noqa
from .genepanelsnapshot import GenePanelSnapshot  # noqa
from .genepanelentrysnapshot import GenePanelEntrySnapshot  # noqa
from .import_tools import UploadedGeneList  # noqa
from .import_tools import UploadedPanelList  # noqa
from .import_tools import UploadedReviewsList  # noqa
from .strs import STR  # noqa
from .region import Region  # noqa
from .panel_types import PanelType  # noqa
