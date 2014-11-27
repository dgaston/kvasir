import json
import datetime
import sys

from gemini import GeminiQuery
from gemini.GeminiQuery import RowFormat
from pyexcelerate import Workbook

from config import *
from kvasir import models
from kvasir import celery

from celery import current_task

from bson.objectid import ObjectId
from collections import Counter

basedir = os.path.abspath(os.path.dirname(__file__))

def print_excel_report(query, database, header, gq, filename):
    wb = Workbook()
    
    #Print Cover material
    ws = wb.new_sheet("Cover")
    ws.set_cell_value(1, 1, "Date Generated:")
    ws.set_cell_value(1, 2, datetime.datetime.now())
    ws.set_cell_value(2, 1, "GEMINI Query:")
    ws.set_cell_value(2, 2, query)
    ws.set_cell_value(3, 1, "GEMINI Database:")
    ws.set_cell_value(3, 2, database)
    
    ws2 = wb.new_sheet("Variants", data=header)
    row = 2
    for row in gq:
        cell = 1
        
        row = row + 1
    
    wb.save(filename)
    

def build_gemini_query_web(form):
    base_query = set_GEMINI_QUERY_BASE(form.query.data)
    table = set_GEMINI_QUERY_TABLE(form.query.data)
    impact = set_GEMINI_Impact_Filter(form.impacts.data)
    genotypes_filter = set_GEMINI_Genotypes_Filter(form.affected_filter.data, form.unaffected_filter.data, form.unknown_filter.data, form.affected_number.data, form.unaffected_number.data, form.unknown_number.data, form.mode.data)
    allele_freqs_filter = set_GEMINI_AF_Filter(form.evs_eur.data, form.evs_afr.data, form.evs_all.data,
                                               form.kg_eur.data, form.kg_afr.data, form.kg_amr.data,
                                               form.kg_asn.data, form.kg_all.data)
    where_clause = BASE_GEMINI_QUERY_WHERE_CLAUSE

    if form.gene_filter.data != 'none':
        where_clause = set_GEMINI_Genes_Filter(form.gene_filter.data, form.filter_method.data, BASE_GEMINI_QUERY_WHERE_CLAUSE)

    if form.intervals.data:
        where_clause = set_GEMINI_intervals_filter(where_clause, form.intervals.data)

    where_clause += " ORDER BY chrom, start"

    query = "%s, %s %s WHERE %s AND %s" % (base_query, DEFAULT_GEMINI_GENOTYPE_COLUMNS, table, where_clause, impact)

    if allele_freqs_filter:
        query = "%s AND %s" % (query, allele_freqs_filter)
    
    return (query, genotypes_filter)

def set_GEMINI_Genes_Filter(name, method, where):
    list = models.GeneList.objects.get(name=name)
    genes = list.genes
    ids = []
    for gene in genes:
        if method == 'exclude':
            ids.append("""g.ensembl_gene_id != '%s'""" % gene.ensembl_id)
        elif method == 'include':
            ids.append("""g.ensembl_gene_id == '%s'""" % gene.ensembl_id)
        else:
            sys.stderr.write("Unknown filter method option %s. Exiting\n" % method)
            sys.exit()

    if method == 'exclude':
        gene_ids_string = " AND ".join(ids)
    elif method == 'include':
        gene_ids_string = " OR ".join(ids)
    else:
        sys.stderr.write("Unknown filter method option %s. Exiting\n" % method)
        sys.exit()

    string = "%s AND (%s)" % (where, gene_ids_string)

    return string

def set_GEMINI_intervals_filter(where, interval_list):
    intervals = interval_list.splitlines()
    for interval in intervals:
        temp = interval.split(':')
        chrom = temp[0]
        coords = temp[1].split('-')
        start = coords[0]
        end = coords[1]

        where += " AND chrom = " + "'" + chrom + "'" + \
            " AND ((start BETWEEN " + start + " AND " + end + ")" +\
            " OR (end BETWEEN " + start + " AND " + end + "))"

    return where


def set_GEMINI_QUERY_BASE(type):
    if type == 'all':
        base = DEFAULT_GEMINI_QUERY_BASE
    elif type == 'clinical':
        base = CLINICAL_GEMINI_QUERY_BASE
    elif type == 'variant':
        base = VARIANT_GEMINI_QUERY_BASE
    else:
        base = DEFAULT_GEMINI_QUERY_BASE
    
    return base

def set_GEMINI_QUERY_TABLE(type):
    if type == 'all':
        base = DEFAULT_GEMINI_TABLE_QUERY
    elif type == 'clinical':
        base = DEFAULT_GEMINI_TABLE_QUERY
    elif type == 'variant':
        base = VARIANT_GEMINI_TABLE_QUERY
    else:
        base = DEFAULT_GEMINI_TABLE_QUERY
    
    return base

def set_GEMINI_Genotypes_Filter(affected, unaffected, unknown, affected_number, unaffected_number, unknown_number, mode):
    
    genotype_filters = []

    if affected == 'variant':
        genotype_filters.append("(gt_types).(phenotype==2).(!=HOM_REF).(%s)" % affected_number)
    elif affected == 'het':
        genotype_filters.append("(gt_types).(phenotype==2).(==HET).(%s)" % affected_number)
    elif affected == 'hetu':
        genotype_filters.append("(gt_types).(phenotype==2).(!=HOM_REF).(%s) and (gt_types).(phenotype==2).(!=HOM_ALT).(%s)" % (affected_number, affected_number))
    elif affected == 'hom':
        genotype_filters.append("(gt_types).(phenotype==2).(==HOM_ALT).(%s)" % affected_number)
    elif affected == 'homu':
        genotype_filters.append("(gt_types).(phenotype==2).(!=HOM_REF).(%s) and (gt_types).(phenotype==2).(!=HET).(%s)" % (affected_number, affected_number))
    elif affected == 'ref':
        genotype_filters.append("(gt_types).(phenotype==2).(==HOM_REF).(%s)" % affected_number)
    elif affected == 'refu':
        genotype_filters.append("(gt_types).(phenotype==2).(==HOM_REF).(%s)" % affected_number)
    elif affected == 'nhoma':
        genotype_filters.append("(gt_types).(phenotype==2).(!=HOM_ALT).(%s)" % affected_number)
    else:
        pass


    #Still need to put any/all/none on the multi-type selects

    if unaffected == 'variant':
        genotype_filters.append("(gt_types).(phenotype==1).(!=HOM_REF).(%s)" % unaffected_number)
    elif unaffected == 'het':
        genotype_filters.append("(gt_types).(phenotype==1).(==HET).(%s)" % unaffected_number)
    elif unaffected == 'hetu':
        genotype_filters.append("(gt_types).(phenotype==1).(!=HOM_REF).(all) and (gt_types).(phenotype==1).(!=HOM_ALT).(all)")
    elif unaffected == 'hom':
        genotype_filters.append("(gt_types).(phenotype==1).(==HOM_ALT).(%s)" % unaffected_number)
    elif unaffected == 'homu':
        genotype_filters.append("(gt_types).(phenotype==1).(!=HOM_REF).(all) and (gt_types).(phenotype==1).(!=HET).(all)")
    elif unaffected == 'ref':
        genotype_filters.append("(gt_types).(phenotype==1).(==HOM_REF).(%s)" % unaffected_number)
    elif unaffected == 'refu':
        genotype_filters.append("(gt_types).(phenotype==1).(==HOM_REF).(%s)" % unaffected_number)
    elif unaffected == 'nhoma':
        genotype_filters.append("(gt_types).(phenotype==1).(!=HOM_ALT).(%s)" % unaffected_number)
    else:
        pass
    
    if unknown == 'variant':
        genotype_filters.append("(gt_types).(phenotype==-9).(!=HOM_REF).(%s)" % unknown_number)
    elif unknown == 'het':
        genotype_filters.append("(gt_types).(phenotype==-9).(==HET).(%s)" % unknown_number)
    elif unknown == 'hetu':
        genotype_filters.append("(gt_types).(phenotype==-9).(!=HOM_REF).(all) and (gt_types).(phenotype==-9).(!=HOM_ALT).(all)")
    elif unknown == 'hom':
        genotype_filters.append("(gt_types).(phenotype==-9).(==HOM_ALT).(%s)" % unknown_number)
    elif unknown == 'homu':
        genotype_filters.append("(gt_types).(phenotype==-9).(!=HOM_REF).(all) and (gt_types).(phenotype==-9).(!=HET).(all)")
    elif unknown == 'ref':
        genotype_filters.append("(gt_types).(phenotype==-9).(==HOM_REF).(%s)" % unknown_number)
    elif unknown == 'refu':
        genotype_filters.append("(gt_types).(phenotype==-9).(==HOM_REF).(%s)" % unknown_number)
    elif unknown == 'nhoma':
        genotype_filters.append("(gt_types).(phenotype==-9).(!=HOM_ALT).(%s)" % unknown_number)
    else:
        pass
    
    genotypes_filter_string = " AND ".join(genotype_filters)
    
    return genotypes_filter_string

def set_GEMINI_AF_Filter(evs_eur, evs_afr, evs_all, kg_eur, kg_afr, kg_amr, kg_asn, kg_all):
    af_filters = []
    
    if evs_eur != -1:
        af_filters.append("(aaf_esp_ea <= %s OR aaf_esp_ea is NULL)" % evs_eur)
    
    if evs_afr != -1:
        af_filters.append("(aaf_esp_aa <= %s OR aaf_esp_aa is NULL)" % evs_afr)
    
    if evs_all != -1:
        af_filters.append("(aaf_esp_all <= %s OR aaf_esp_all is NULL)" % evs_all)
    
    if kg_eur != -1:
        af_filters.append("(aaf_1kg_eur <= %s OR aaf_1kg_eur is NULL)" % kg_eur)
    
    if kg_afr != -1:
        af_filters.append("(aaf_1kg_afr <= %s OR aaf_1kg_afr is NULL)" % kg_afr)
    
    if kg_amr != -1:
        af_filters.append("(aaf_1kg_amr <= %s OR aaf_1kg_amr is NULL)" % kg_amr)
    
    if kg_asn != -1:
        af_filters.append("(aaf_1kg_asn <= %s OR aaf_1kg_asn is NULL)" % kg_asn)
    
    if kg_all != -1:
        af_filters.append("(aaf_1kg_all <= %s OR aaf_1kg_all is NULL)" % kg_all)
    
    af_filter_string = " AND ".join(af_filters)
    
    return af_filter_string

def set_GEMINI_Impact_Filter(filter):
    impact_filter = ""
    
    if filter == 'all':
        impact_filter = """((impact_severity == 'MED') or (impact_severity == 'HIGH') or (impact_severity == 'LOW'))"""
    elif filter == 'med+high':
        impact_filter = """((impact_severity == 'MED') or (impact_severity == 'HIGH'))"""
    elif filter =='high':
        impact_filter = """impact_severity == 'HIGH'"""
    else:
        pass
    
    return impact_filter

def _setupGEMINIQuery(sample_list, query_base, where_clause):
    sys.stdout.write("Retrieving info on provided samples\n")
    samples = sample_list.split(',')
    sample_genotype_ids = []
    for sample in samples:
        id = "gts.%s" % sample
        sample_genotype_ids.append(id)
   
    genotype_query_string = ",".join(sample_genotype_ids)
    query = "%s, %s %s %s" % (query_base, genotype_query_string, DEFAULT_GEMINI_TABLE_QUERY, where_clause)
    
    sys.stdout.write("Working with samples: %s\n" % genotype_query_string)
    
    return (query, samples)


@celery.task
def run_gemini_query(id, query, genotype_filter, json_filename, mode, results_string):
    return_dict = dict()

    json_results_fh = os.path.join(STATIC_FOLDER, json_filename)
    results_file = "/static/%s" % json_filename

    gdb = models.GDatabase.objects.get(id = ObjectId(id))
    gq = GeminiQuery(gdb.file, out_format=JSONRowFormat(None))
    gq.run(query, genotype_filter)

    header = gq.header
    js_header = []
    for key in header:
        string = key.replace('.', '\\\\.')
        js_header.append(string)

    #The json result file is a unique name generated from the database name, query, and genotype_filter
    #If the json results file already exists we save some time by skipping generating the file.
    #We only re-executed the query to get the header object.
    count1 = 0
    if not os.path.isfile(json_results_fh):
        genes_filter = []
        if mode == 'compound':
            gene_variants = Counter()
            for row in gq:
                count1 += 1
                gene_variants[row['ensembl_gene_id']] += 1
            for gene in gene_variants:
                if gene_variants[gene] >= 2:
                    genes_filter.append(gene)

        gq = GeminiQuery(gdb.file, out_format=JSONRowFormat(None))
        gq.run(query, genotype_filter)
        with open(json_results_fh, "wb") as file:
            count = 0
            total = 0
            file.write("""{\n"data": [\n""")
            for row in gq:
                total += 1
                flag = 0
                if mode == 'none':
                    flag = 1
                elif mode == 'compound':
                    if row['ensembl_gene_id'] in genes_filter:
                        flag = 1
                else:
                    flag = 1

                if flag:
                    if count == 0:
                        file.write("%s" % row)
                    else:
                        file.write(",\n%s" % row)
                    count += 1
            file.write("""\n]\n}\n""")
            #Debugging, creates bad formatted JSON
            #file.write("Output %s of %s results and count1 of %s\n" % (count, total, count1))

    return (header, js_header, results_file, gdb.file, query, genotype_filter, results_string)

@celery.task
def test_celery ():
    return ("string 1", "string 2")

class JSONRowFormat(RowFormat):

    name = "json"

    def __init__(self, args):
        pass

    def format(self, row):
        """Emit a JSON representation of a given row
        """
        return json.dumps(row.row)

    def format_query(self, query):
        return query

    def predicate(self, row):
        return True

    def header(self, fields):
        """ return a header for the row """
        return fields