from enum import Enum

# Valid entity name - gene symbols, region or STR names
# Used in URLs, file upload checks, and other validations
# TODO: Switch to HGNC ids for gene symbols
VALID_ENTITY_FORMAT = r"[\w\-\.\$\~\@\#\ ]+"


class GeneDataType(Enum):
    CLASS = 0
    LONG = 1
    SHORT = 2
    COLOR = 3


class GeneStatus(Enum):
    NOLIST = 0
    RED = 1
    AMBER = 2
    GREEN = 3


# Valid MOI values, used for Evaluations moi field and MOI Checks script
MODE_OF_INHERITANCE_VALID_CHOICES = (
    (
        "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
        "MONOALLELIC, autosomal or pseudoautosomal, NOT imprinted",
    ),  # noqa
    (
        "MONOALLELIC, autosomal or pseudoautosomal, maternally imprinted (paternal allele expressed)",
        "MONOALLELIC, autosomal or pseudoautosomal, maternally imprinted (paternal allele expressed)",
    ),  # noqa
    (
        "MONOALLELIC, autosomal or pseudoautosomal, paternally imprinted (maternal allele expressed)",
        "MONOALLELIC, autosomal or pseudoautosomal, paternally imprinted (maternal allele expressed)",
    ),  # noqa
    (
        "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
        "MONOALLELIC, autosomal or pseudoautosomal, imprinted status unknown",
    ),  # noqa
    (
        "BIALLELIC, autosomal or pseudoautosomal",
        "BIALLELIC, autosomal or pseudoautosomal",
    ),
    (
        "BOTH monoallelic and biallelic, autosomal or pseudoautosomal",
        "BOTH monoallelic and biallelic, autosomal or pseudoautosomal",
    ),  # noqa
    (
        "BOTH monoallelic and biallelic (but BIALLELIC mutations cause a more SEVERE disease form), autosomal or pseudoautosomal",
        "BOTH monoallelic and biallelic (but BIALLELIC mutations cause a more SEVERE disease form), autosomal or pseudoautosomal",
    ),  # noqa
    (
        "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
        "X-LINKED: hemizygous mutation in males, biallelic mutations in females",
    ),  # noqa
    (
        "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
        "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
    ),  # noqa
    ("MITOCHONDRIAL", "MITOCHONDRIAL"),
    ("Unknown", "Unknown"),
    ("Other", "Other - please specifiy in evaluation comments"),
)
