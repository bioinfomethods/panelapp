from django.db import models
from model_utils import Choices
from model_utils.models import TimeStampedModel

from accounts.models import User


class TrackRecord(TimeStampedModel):
    """Keeps track of what's changed in a gene for a specific panel"""

    ISSUE_TYPES = Choices(
        ("Created", "Created"),
        ("NewSource", "Added New Source"),
        ("RemovedSource", "Removed Source"),
        ("ChangedGeneName", "Changed Gene Name"),
        ("SetPhenotypes", "Set Phenotypes"),
        ("SetModelofInheritance", "Set Mode of Inheritance"),
        ("ClearSources", "Clear Sources"),
        ("SetModeofPathogenicity", "Set mode of pathogenicity"),
        ("GeneClassifiedbyGenomicsEnglandCurator", "Gene classified by Genomics England curator"),
        ("EntityClassifiedbyGenomicsEnglandCurator", "Entity classified by Genomics England curator"),
        ("SetModeofInheritance", "Set mode of inheritance"),
        ("SetPenetrance", "Set penetrance"),
        ("SetPublications", "Set publications"),
        ("ApprovedGene", "Approved Gene"),
        ("ApprovedEntity", "Approved Entity"),
        ("GelStatusUpdate", "Gel Status Update"),
        ("UploadGeneInformation", "Upload gene information"),
        ("RemovedTag", "Removed Tag"),
        ("AddedTag", "Added Tag"),
        ("ChangedName", "Changed Name"),
        ("ChangedSTRName", "Changed STR Name"),
        ("ChangedChromosome", "Changed Chromosome"),
        ("ChangedPosition37", "Changed GRCh37"),
        ("ChangedPosition38", "Changed GRCh38"),
        ("ChangedNormalRepeats", "Changed Normal Number of Repeats"),
        ("ChangedPathogenicRepeats", "Changed Pathogenic Number of Repeats"),
        ("RemovedGene", "Removed Gene from the STR"),
        ("ChangedRepeatedSequence", "Changed Repeated Sequence"),
        ('ChangedEffectTypes', 'Changed Effect Types'),
        ('ChangedVariantType', 'Changed Variant Types'),
        ('ChangedHaploinsufficiencyScore', 'Changed Haploinsufficiency Score'),
        ('ChangedTriplosensitivityScore', 'Changed Triplosensitivity Score'),
        ('ChangedRequiredOverlapPercentage', 'Changed Required Overlap Percentage'),
    )

    class Meta:
        ordering = ('-created',)

    issue_type = models.CharField(choices=ISSUE_TYPES, max_length=512)  # can this be standartized?
    issue_description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    curator_status = models.IntegerField(default=0)  # Boolean maybe?
    gel_status = models.IntegerField(default=0)

    def dict_tr(self):
        return {
            "date": self.created,
            "gel_status": self.gel_status,
            "curator_status": self.curator_status,
            "issue_type": self.issue_type,
            "issue_description": self.issue_description,
            "user": self.user
        }
