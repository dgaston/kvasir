import os, sys
from collections import defaultdict
from config import TMP_FOLDER

basedir = os.path.abspath(os.path.dirname(__file__))
QUERY_JSON_RESULTS = os.path.join(TMP_FOLDER, 'JSON_Results/')

DEFAULT_GEMINI_QUERY_BASE = "select v.*, g.*"

CLINICAL_GEMINI_QUERY_BASE = "select v.chrom, v.start, v.end, v.vcf_id, v.type, \
                            v.sub_type, v.ref, v.alt, v.filter, v.qual, v.gene, v.biotype, \
                            v.impact, v.impact_so, v.impact_severity, v.codon_change, v.transcript, v.aa_change, \
                            v,aa_length, v.in_cpg_island, \
                            v.exon, v.in_omim, v.clinvar_sig, v.clinvar_disease_name, v.clinvar_dbsource, \
                            v.clinvar_dbsource_id, v.clinvar_origin, v.clinvar_dsdb, v.clinvar_dsdbid, \
                            v.clinvar_disease_acc, v.clinvar_in_locus_spec_db, v.clinvar_on_diag_assay, \
                            v.depth, v.num_alleles, v.allele_count, \
                            v.rs_ids, v.aaf_esp_ea, v.aaf_esp_aa, v.aaf_esp_all, \
                            v.aaf_1kg_eur, v.aaf_1kg_amr, v.aaf_1kg_asn, v.aaf_1kg_afr, v.aaf_1kg_all, \
                            v.is_conserved, v.is_somatic"

VARIANT_GEMINI_QUERY_BASE = "select v.*"

DEFAULT_GEMINI_TABLE_QUERY = "from variants v, gene_detailed g"
VARIANT_GEMINI_TABLE_QUERY = "from variants v"

DEFAULT_GEMINI_GENOTYPES = "(gts).(*), (gt_depths).(*)"

BASE_GEMINI_QUERY_WHERE_CLAUSE = "v.chrom = g.chrom AND v.gene = g.gene AND v.transcript = g.transcript"