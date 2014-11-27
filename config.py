import os

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True

SECRET_KEY = u'Gh\x00)\xad\x7fQx\xedvx\xfetS-\x9a\xd7\x17$\x08_5\x17F' #Change this value on deployment!!!!!
SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
SECURITY_PASSWORD_SALT = SECRET_KEY

SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = True
SECURITY_CHANGEABLE = True

THREADS_PER_PAGE = 2

# Mail server settings
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True

#Change these on a production server
MAIL_USERNAME = "admin@mail.com"
MAIL_PASSWORD = "test_pass"
SECURITY_EMAIL_SENDER = 'admin@mail.com'

# Administrator list
ADMINS = []

# Directories
PROJECTS_DIR = ""
UPLOAD_FOLDER = os.path.join(basedir, 'kvasir/uploads/')
STATIC_FOLDER = os.path.join(basedir, 'kvasir/static/')
TMP_RESULTS_FOLDER = os.path.join(basedir, 'kvasir/tmp/')
TMP_FOLDER = os.path.join(basedir, 'tmp/')

#File Upload Settings
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf', 'xls', 'xlsx', 'doc', 'docx'])

# Database Settings
MAX_SEARCH_RESULTS = 500

# General Settings for Application
# Are these actually needed anymore with flask-security running?
ROLE_GUEST = 0
ROLE_USER = 1
ROLE_ADMIN = 2
STATUS_ACTIVE = 1
STATUS_INACTIVE = 0

DEFAULT_GEMINI_QUERY_BASE = "select v.*, g.*"

CLINICAL_GEMINI_QUERY_BASE = "select v.chrom, v.start, v.end, v.vcf_id, v.type, v.sub_type, v.ref, v.alt, v.filter, v.gene, v.biotype, v.impact, v.impact_so, v.impact_severity, v.codon_change, v.transcript, v.aa_change, v.exon, v.in_omim, v.clinvar_sig, v.clinvar_disease_name, v.clinvar_dbsource, v.clinvar_dbsource_id, v.clinvar_origin, v.clinvar_dsdb, v.clinvar_dsdbid, v.clinvar_disease_acc, v.clinvar_in_locus_spec_db, v.clinvar_on_diag_assay, v.rs_ids, v.aaf_esp_ea, v.aaf_esp_aa, v.aaf_esp_all, v.aaf_1kg_eur, v.aaf_1kg_amr, v.aaf_1kg_asn, v.aaf_1kg_afr, v.aaf_1kg_all, v.is_conserved, v.is_somatic, g.ensembl_gene_id"

VARIANT_GEMINI_QUERY_BASE = "select v.*"

DEFAULT_GEMINI_TABLE_QUERY = "from variants v, gene_detailed g"
VARIANT_GEMINI_TABLE_QUERY = "from variants v"

DEFAULT_GEMINI_GENOTYPE_COLUMNS = "(gts).(*), (gt_depths).(*)"

BASE_GEMINI_QUERY_WHERE_CLAUSE = "v.chrom = g.chrom AND v.gene = g.gene AND v.transcript = g.transcript"