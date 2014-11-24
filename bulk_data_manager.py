#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import csv
import sys

from flask.ext.script import Manager
from flask.ext.security.utils import encrypt_password

from kvasir import app, db, models, user_datastore
from config import *
from collections import defaultdict
from bson.objectid import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
source_dir = os.path.dirname(os.path.realpath(__file__))

db_manager = Manager(app)

@db_manager.option('-f', '--file', dest='file')
def populate_markers(file):
    "Initial population of markers with no association or allele data. TSV Format with header"

    #Need to add parsing of orientation, and type
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            id = row['ID'].strip()

            #If SNP already exists in the database it will essentially be skipped
            try:
                m = models.Marker.objects.get(dbsnp_id = id)
            except:
                m = models.Marker(dbsnp_id = id)

            m.save()

            if row['Genes']:
                genes = row['Genes'].split(",")
                for gene in genes:
                    gene = gene.strip()
                    if gene.startswith("ENSG"):
                        try:
                            g = models.Gene.objects.get(ensembl_id=gene)
                        except:
                            sys.stderr.write("ERROR: Gene %s not found\n" % gene)
                        else:
                            m.genes.append(g)
                            g.markers.append(m)
                            g.save()
                    else:
                        sys.stdout.write("Searching by HGNC ID: *%s*\n" % gene)
                        results = models.Gene.objects(hgnc_ids__contains=gene)
                        sys.stdout.write("Iterating through possible results:\n")

                        for result in results:
                            sys.stdout.write("HGNC ID(s) for %s:\n" % result.ensembl_id)
                            hgnc_ids = result.hgnc_ids
                            for id in hgnc_ids:
                                sys.stdout.write("%s\n" % id)
                                if id == gene:
                                    sys.stdout.write("Matched HGNC, inserting\n")
                                    m.genes.append(result)
                                    result.markers.append(m)
                                    result.save()

            #if row['Strand']:
            #    m.strand = row['Strand']

            if row['Type']:
                m.type = row['Type']

            m.save()

    sys.stdout.write("Finished loading markers\n")

@db_manager.option('-f', '--file', dest='file')
@db_manager.option('-u', '--user', dest='email', help='Email associated with your user account')
@db_manager.option('-p', '--project', dest='project', help='Project Name')
def populate_associations(file, email, project):
    "Initial population of associations from TSV file with Header row"

    try:
        p = models.Project.objects.get(project_name = project)
    except:
        sys.stderr.write("Project name %s not found. Exiting...\n" % project)
        sys.exit()

    try:
        u = models.User.objects.get(email = email)
    except:
        sys.stderr.write("User with email: %s not found. Exiting...\n" % email)
        sys.exit()

    #Using csv.reader even though this file may potentially just be a list
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            id = row['ID'].strip()

            #If SNP already exists in the database it will essentially be skipped
            try:
                m = models.Marker.objects.get(dbsnp_id = id)
            except:
                sys.stderr.write("Error: Unknown marker %s, creating...\n" % id)
                strand = "Unknown"
                if row['Strand']:
                    strand = row['Strand']

                type = "Unknown"
                if row['Type']:
                    type = row['Type']

                m = models.Marker(dbsnp_id = id, strand = strand, type = type)
                m.save()
            else:
                if not m.strand:
                    if row['Strand']:
                        m.strand = row['Strand']

                if not m.type:
                    if row['Type']:
                        m.type = row['Type']

            active = False
            if row['Active'].upper() == "TRUE":
                active = True

            oid = ObjectId()
            s_oid = str(oid)

            a = models.Association(id = s_oid, allele_of_interest = row['Favoured Allele'], trait = row['Phenotype'],
                                   impact = row['Impact'], confidence = row['Confidence'], project = p,
                                   last_modified_by = u, active = active)

            m.associations.append(a)
            m.save()

    sys.stdout.write("Finished adding associations\n")

@db_manager.option('-f', '--file', dest='file')
def populate_alleles(file):
    "Initial population of alleles from TSV file with Header row"

    #Using csv.reader even though this file may potentially just be a list
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            id = row['ID'].strip()

            #If SNP already exists in the database it will essentially be skipped
            try:
                m = models.Marker.objects.get(dbsnp_id = id)
            except:
                m = models.Marker(dbsnp_id = id)
                m.save()

            oid = ObjectId()
            s_oid = str(oid)

            a = models.Allele(id = s_oid, ref_allele = row['Reference'], alt_allele = row['Alternative'],
                              source = row['Source'], orientation = row['Orientation'])

            if row['Frequencies']:
                frequencies = row['Frequencies'].split(",")
                for frequency in frequencies:
                    temp = frequency.split(":")
                    population = temp[0].strip()
                    frequency = float(temp[1].strip())

                    f = models.Frequency(population = population, frequency = frequency)
                    a.frequencies.append(f)

            m.alleles.append(a)
            m.save()

    sys.stdout.write("Finished adding allele data\n")

@db_manager.option('-f', '--file', dest='file')
def populate_goslim_terms(file):
    "Populate the ensembl -> GO_term associations"

    entries = defaultdict(list)
    sys.stdout.write("Parsing GOSlim term entries\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['GOSlim GOA Accession(s)']:
                entry = dict()
                entry['accession'] = row['GOSlim GOA Accession(s)']
                entry['description'] = row['GOSlim GOA Description']

                entries[row['Ensembl Gene ID']].append(entry)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding GOSlim terms to gene models in database\n")
    for gene in genes:
        gene_entries = entries[gene.ensembl_id]
        for entry in gene_entries:
            g = models.GOSlim(go_id=entry['accession'], go_desc=entry['description'])
            gene.goslim_terms.append(g)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-f', '--file', dest='file', help='Input adjacency list')
def populate_pathways(file):
    "Populate the interactions database from a tab-delimited, four column, adjacency list"

    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            ids = row['ensembl_ids'].split(',')
            for id in ids:
                p = models.Pathway(gene_id=id, pathway=row['pathway'].decode('utf-8'), source=row['source'])
                p.save()

@db_manager.option('-f', '--file', dest='file', help='HPO Genes to Phenotypes File')
@db_manager.option('-e', '--entrez', dest='convert_file', help='BioMart Ensembl ID to Entrez ID Conversion Table')
def populate_phenotypes(file, convert_file):
    "Populate the gene to phenotypes association database from input file"

    conversion = dict()
    gene_phenotypes = defaultdict(list)

    sys.stdout.write("Constructing Entrez ID to Ensembl ID dictionary\n")
    with open(convert_file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['EntrezGene ID']:
                if row['Ensembl Gene ID'].startswith('LRG_'):
                    continue

                conversion[row['EntrezGene ID']] = row['Ensembl Gene ID']

    sys.stdout.write("Parsing Phenotype file and creating dictionary of phenotypes\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            try:
                ensembl_id = conversion[row['entrez-gene-id']]
            except:
                sys.stderr.write("WARNING: Could not find an Ensembl ID for Entrez ID: %s\n" % row['entrez-gene-id'])
                continue

            phenotype = dict()
            phenotype['term'] = row['HPO-Term-Name']
            phenotype['id'] = row['HPO-Term-ID']

            gene_phenotypes[ensembl_id].append(phenotype)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding Phenotypes to gene models in database\n")
    for gene in genes:
        phenotypes = gene_phenotypes[gene.ensembl_id]
        for phenotype in phenotypes:
            p = models.Phenotype(term=phenotype['term'], id=phenotype['id'])
            gene.phenotypes.append(p)

        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-i', '--interactions', dest='file', help='BioGRID Interactions File by Organism')
@db_manager.option('-e', '--entrez', dest='convert_file', help='BioMart Ensembl ID to Entrez ID Conversion Table')
def populate_biogrid_interactions(file, convert_file):
    "Populate the gene to BioGRID interactions association database from input file"

    conversion = dict()
    interactions = defaultdict(list)

    sys.stdout.write("Constructing Entrez ID to Ensembl ID dictionary\n")
    with open(convert_file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['EntrezGene ID']:
                if row['Ensembl Gene ID'].startswith('LRG_'):
                    continue

                conversion[row['EntrezGene ID']] = row['Ensembl Gene ID']

    sys.stdout.write("Parsing BioGRID file and creating dictionary of interactions\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            try:
                ensembl_id1 = conversion[row['Entrez Gene Interactor A']]
            except:
                sys.stderr.write("WARNING: Could not find an Ensembl ID for Entrez ID: %s\n" % row['Entrez Gene Interactor A'])
                continue
            try:
                ensembl_id2 = conversion[row['Entrez Gene Interactor B']]
            except:
                sys.stderr.write("WARNING: Could not find an Ensembl ID for Entrez ID: %s\n" % row['Entrez Gene Interactor B'])
                continue

            interaction1 = dict()
            interaction2 = dict()

            try:
                score = float(row['Score'])
            except:
                score = 0.0

            interaction1['interactor_ensembl'] = ensembl_id2
            interaction2['interactor_ensembl'] = ensembl_id1

            interaction1['system'] = row['Experimental System']
            interaction2['system'] = row['Experimental System']

            interaction1['phenotypes'] = row['Phenotypes']
            interaction2['phenotypes'] = row['Phenotypes']

            interaction1['modifications'] = row['Modification']
            interaction2['modifications'] = row['Modification']

            interaction1['qualifications'] = row['Qualifications']
            interaction2['qualifications'] = row['Qualifications']

            interaction1['type'] = row['Experimental System Type']
            interaction2['type'] = row['Experimental System Type']

            interaction1['source'] = row['Source Database']
            interaction2['source'] = row['Source Database']

            interaction1['throughput'] = row['Throughput']
            interaction2['throughput'] = row['Throughput']

            interaction1['score'] = score
            interaction2['score'] = score

            interaction1['pubmed_id'] = row['Pubmed ID']
            interaction2['pubmed_id'] = row['Pubmed ID']

            interaction1['interaction_source_id'] = row['#BioGRID Interaction ID']
            interaction2['interaction_source_id'] = row['#BioGRID Interaction ID']

            interactions[ensembl_id1].append(interaction1)
            interactions[ensembl_id2].append(interaction2)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding interactions to gene models in database\n")
    for gene in genes:
        interactions_list = interactions[gene.ensembl_id]
        for interactor in interactions_list:
            i = models.Interaction(interactor_ensembl_id=interactor['interactor_ensembl'],
                                   system=interactor['system'], phenotype=interactor['phenotypes'],
                                   modifications=interactor['modifications'], qualifications=interactor['qualifications'],
                                   type=interactor['type'], source=interactor['source'],
                                   throughput=interactor['throughput'], score=interactor['score'],
                                   pubmed_id=interactor['pubmed_id'], interaction_source_id=interactor['interaction_source_id'])

            gene.interactions.append(i)

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

        gene.save()

@db_manager.option('-p', '--psgn', dest='file', help='PSGN File')
@db_manager.option('-e', '--entrez', dest='convert_file', help='BioMart Ensembl ID to Entrez ID Conversion Table')
def populate_PSGN(file, convert_file):
    "Populate the Pathophenotypic Similarity Gene Network"

    conversion = dict()
    interactions = defaultdict(list)

    sys.stdout.write("Constructing Entrez ID to Ensembl ID dictionary\n")
    with open(convert_file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['EntrezGene ID']:
                if row['Ensembl Gene ID'].startswith('LRG_'):
                    continue

                conversion[row['EntrezGene ID']] = row['Ensembl Gene ID']

    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            try:
                ensembl_id1 = conversion[row['Entrez GeneID 1']]
            except:
                sys.stderr.write("WARNING: Could not find an Ensembl ID for Entrez ID: %s\n" % row['Entrez GeneID 1'])
                continue
            try:
                ensembl_id2 = conversion[row['Entrez GeneID 2']]
            except:
                sys.stderr.write("WARNING: Could not find an Ensembl ID for Entrez ID: %s\n" % row['Entrez GeneID 2'])
                continue

            interaction1 = dict()
            interaction2 = dict()

            interaction1['interactor_ensembl_id'] = ensembl_id2
            interaction2['interactor_ensembl_id'] = ensembl_id1

            interaction1['similarity'] = float(row['Pathophenotypic similarity'])
            interaction2['similarity'] = float(row['Pathophenotypic similarity'])

            interactions[ensembl_id1].append(interaction1)
            interactions[ensembl_id2].append(interaction2)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding PSGN interactions to gene models in database\n")
    for gene in genes:
        interactions_list = interactions[gene.ensembl_id]
        for interactor in interactions_list:
            p = models.PSGN(interactor_ensembl_id=interactor['interactor_ensembl_id'],
                            similarity=interactor['similarity'])

            gene.psgn_connections.append(p)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-f', '--file', dest='file', help='Input gene-OMIM association file')
def populate_OMIM(file):
    "Populate the gene to OMIM diseases database from input file"

    entries = defaultdict(list)
    sys.stdout.write("Parsing OMIM entries\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['MIM Morbid Accession']:
                entry = dict()
                entry['omim_id'] = row['MIM Morbid Accession']
                entry['description'] = row['MIM Morbid Description']

                entries[row['Ensembl Gene ID']].append(entry)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding OMIM entries to gene models in database\n")
    for gene in genes:
        gene_entries = entries[gene.ensembl_id]
        for entry in gene_entries:
            o = models.OMIM(omim_id=entry['omim_id'], description=entry['description'])
            gene.omim.append(o)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-f', '--file', dest='file', help='Input gene-Orphanet association file')
def populate_orphanet(file):
    "Populate the gene to Orphanet database from input file"

    entries = defaultdict(list)
    sys.stdout.write("Parsing Orphanet entries\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            entry = dict()
            entry['accession'] = row['orphanet_id']
            entry['description'] = row['description']

            entries[row['gene_id']].append(entry)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding Orphanet entries to gene models in database\n")
    for gene in genes:
        gene_entries = entries[gene.ensembl_id]
        for entry in gene_entries:
            o = models.Orphanet(accession=entry['accession'], description=entry['description'])
            gene.orphanet.append(o)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-f', '--file', dest='file', help='BioMart export of Ensembl Genes and Transcript IDs')
def populate_transcripts(file):
    "Populate the Transcripts table with Associated Ensembl IDs"

    entries = defaultdict(list)
    sys.stdout.write("Parsing Transcript entries\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            entry = dict()
            if row['Ensembl Transcript ID']:
                entry['transcript_id'] = row['Ensembl Transcript ID']
                entry['protein_id'] = row['Ensembl Protein ID']
                entry['start'] = row['Transcript Start (bp)']
                entry['end'] = row['Transcript End (bp)']
                entry['biotype'] = row['Transcript Biotype']

                entries[row['Ensembl Gene ID']].append(entry)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding Transcript data to gene models in database\n")
    for gene in genes:
        gene_entries = entries[gene.ensembl_id]
        for entry in gene_entries:
            t = models.Transcript(transcript_id=entry['transcript_id'], protein_id=entry['protein_id'],
                                  start = entry['start'], end = entry['end'],
                                  biotype = entry['biotype'])
            gene.transcripts.append(t)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-f', '--file', dest='file', help='BioMart export of Ensembl Genes and Orthologs')
@db_manager.option('-n', '--name', dest='name', help="One word species name for file")
def add_orthologs(file, name):
    "Populate Orthologs Table"

    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        reader.next()
        for row in reader:
            if row[1]:
                o = models.Ortholog(human_id=row[0], ortho_id=row[1], species_common=name, homology_type=row[2], percent_id = row[3])
                db.session.add(o)
        db.session.commit()

@db_manager.option('-f', '--file', dest='file', help='BioMart export of Ensembl Genes and Paralogs')
def populate_paralogs(file):
    "Populate Paralogs Table"

    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        reader.next()
        for row in reader:
            if len(row) > 1:
                g1 = models.Gene.objects.get(ensembl_id=row[0])
                g2 = models.Gene.objects.get(ensembl_id=row[1])

                g1.paralogs.append(g2)
                g2.paralogs.append(g1)

                g1.save()
                g2.save()

@db_manager.option('-f', '--infile', dest='file', help='Gene base info source file')
@db_manager.option('-o', '--official_hgnc', dest='hgnc', help='Ensembl to HGNC Mappings file')
@db_manager.option('-l', '--lof', dest='lof_file', help='MacArthur et al LOF Annotations')
@db_manager.option('-e', '--entrez', dest='entrez', help='Ensembl to Entrez Mappings')
@db_manager.option('-u', '--uniprot', dest='uniprot', help='Ensembl to Uniprot Mappings')
@db_manager.option('-c', '--ccds', dest='ccds', help='Ensembl to CCDS Mappings')
@db_manager.option('-s', '--ucsc', dest='ucsc', help='Ensembl to UCSC Mappings')
def populate_genes(file, hgnc, lof_file, entrez, uniprot, ucsc, ccds):
    "Populate the genes database from input file"

    sys.stdout.write("Parsing %s\n" % hgnc)
    hgnc_dict = _parseEnsemblExternalMappingFile(hgnc)

    sys.stdout.write("Parsing %s\n" % entrez)
    entrez_dict = _parseEnsemblExternalMappingFile(entrez)

    sys.stdout.write("Parsing %s\n" % uniprot)
    uniprot_dict = _parseEnsemblExternalMappingFile(uniprot)

    sys.stdout.write("Parsing %s\n" % ccds)
    ccds_dict = _parseEnsemblExternalMappingFile(ccds)

    sys.stdout.write("Parsing %s\n" % ucsc)
    ucsc_dict = _parseEnsemblExternalMappingFile(ucsc)

    sys.stdout.write("Parsing %s\n" % lof_file)
    macarthur_dict = _parseMacArthurLOF(lof_file)

    duplicates = defaultdict(int)

    with open(file, 'rU') as csvfile:
        sys.stdout.write("Parsing %s\n" % file)
        count = 0
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row:
                #Skip adding LRG loci and identifiers in the database
                if row['Ensembl Gene ID'].startswith("LRG_"):
                    continue

                if not count % 1000:
                    sys.stdout.write("Processed %s rows\n" % count)

                hgnc_ids = hgnc_dict[row['Ensembl Gene ID']]
                entrez_ids = entrez_dict[row['Ensembl Gene ID']]
                uniprot_ids = uniprot_dict[row['Ensembl Gene ID']]
                ccds_ids = ccds_dict[row['Ensembl Gene ID']]
                ucsc_ids = ucsc_dict[row['Ensembl Gene ID']]

                score = 0.00
                rank = 0
                tolerant = "N/A"

                for hgnc_id in hgnc_ids:
                    if macarthur_dict[hgnc_id]:
                        score = float(macarthur_dict[hgnc_id]['score'])
                        rank = float(macarthur_dict[hgnc_id]['rank'])
                        tolerant = macarthur_dict[hgnc_id]['tolerant']

                if duplicates[row['Ensembl Gene ID']]:
                    sys.stderr.write("Ensembl ID %s has already been added to the database for commit. Skipping...\n\n" % row['Ensembl Gene ID'])
                    duplicates[row['Ensembl Gene ID']] = duplicates[row['Ensembl Gene ID']] + 1
                else:
                    duplicates[row['Ensembl Gene ID']] = 1
                    g = models.Gene(ensembl_id = row['Ensembl Gene ID'], chromosome = row['Chromosome Name'],
                                band = row['Band'], biotype = row['Gene Biotype'], status = row['Status (gene)'],
                                strand = row['Strand'], start = row['Gene Start (bp)'], end = row['Gene End (bp)'],
                                description = row['Description'], slug = row['Ensembl Gene ID'],
                                macarthur_lof_score = score, macarthur_lof_rank = rank, macarthur_lof_tolerant = tolerant)

                    for id in hgnc_ids:
                        g.hgnc_ids.append(id)

                    for id in entrez_ids:
                        g.entrez_ids.append(id)

                    for id in uniprot_ids:
                        g.uniprot_ids.append(id)

                    for id in ccds_ids:
                        g.ccds_ids.append(id)

                    for id in ucsc_ids:
                        g.ucsc_ids.append(id)

                    g.save()
                count = count + 1

        sys.stdout.write("ID\tNumber of Entries\n")
        for id in duplicates:
            if duplicates[id] > 1:
                sys.stdout.write("%s\t%s\n" % (id, duplicates[id]))

@db_manager.option('-f', '--file', dest='file', help='Samples file')
def populate_samples(file):
    "Populate info for multiple samples from a tab-delimited file"

    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            s = models.Sample(id=row['id'], maternal_id=row['mid'], paternal_id=row['pid'], status=row['status'], project=row['project'], exome=row['exome_dir'], genotype_data=row['genotype_dir'], phenotypes=row['phenotypes'])
            s.save()

@db_manager.option('-n', '--name', dest='name', help='Name for gene list')
@db_manager.option('-d', '--desc', dest='desc', help='Description of gene list')
@db_manager.option('-f', '--file', dest='file', help='File of genes from panther')
def populate_gene_list_from_panther(name, desc, file):
    "Populate a Gene List based on genes from a PANTHER format file"

    list = models.GeneList(name=name, description=desc)
    list.save()

    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
            ids = row[0].split('|')
            string = ids[1]
            ensembl = string.replace("Ensembl=", "")

            try:
                gene = models.Gene.objects.get(ensembl_id=ensembl)
            except:
                sys.stderr.write("ERROR: Gene %s could not be found. Skipping\n" % ensembl)
            else:
                list.genes.append(gene)
    list.save()

@db_manager.option('-n', '--name', dest='name', help='Name for gene list')
@db_manager.option('-d', '--desc', dest='desc', help='Description of gene list')
@db_manager.option('-f', '--file', dest='file', help='File of genes')
def populate_gene_list(name, desc, file):
    "Populate a Gene List based on genes from a PANTHER format file"

    list = models.GeneList(name=name, description=desc)
    list.save()

    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        for row in reader:
            id = row[0]

            try:
                gene = models.Gene.objects.get(ensembl_id=id)
            except:
                sys.stderr.write("ERROR: Gene %s could not be found. Skipping\n" % ensembl)
            else:
                list.genes.append(gene)
    list.save()

@db_manager.option('-f', '--file', dest='file', help='GNF Expression Atlas BioMart File')
def populate_expression_atlas(file):
    "Populate GNF Expression Atlast data from Ensembl BioMart file"

    "Populate info for multiple samples from a tab-delimited file"

    entries = defaultdict(list)
    sys.stdout.write("Parsing Gene Expression Atlas entries\n")
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            entry = dict()
            if row['Ensembl Gene ID'] and (row['GNF/Atlas cell type'] or row['GNF/Atlas disease state'] or row['GNF/Atlas organism part']):
                entry['cell_type'] = row['GNF/Atlas cell type']
                entry['disease_state'] = row['GNF/Atlas disease state']
                entry['organism_part'] = row['GNF/Atlas organism part']

                entries[row['Ensembl Gene ID']].append(entry)

    sys.stdout.write("Retrieving gene documents\n")
    genes = models.Gene.objects()
    num_genes = len(genes)
    count = 0
    sys.stdout.write("Adding Gene expression data to gene models in database\n")
    for gene in genes:
        gene_entries = entries[gene.ensembl_id]
        for entry in gene_entries:
            e = models.Expression(cell_type = entry['cell_type'], disease_state = entry['disease_state'],
                                       organism_part = entry['organism_part'])
            gene.expression.append(e)
        gene.save()

        count = count + 1
        if not count % 1000:
            sys.stdout.write("Processed %s / %s genes\n" % (count, num_genes))

@db_manager.option('-u', '--user', dest='email', help="User email address")
def delete_all_markers(email):
    "Delete all markers from the database"

    markers = models.Marker.objects()
    for marker in markers:
        marker.delete()

@db_manager.command
def delete_all_transcripts():
    results = models.Transcript.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_publications():
    results = models.Publication.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_tasks():
    results = models.Task.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_samples():
    results = models.Sample.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_users():
    results = models.User.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_projects():
    results = models.Project.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_files():
    results = models.File.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_analyses():
    results = models.Analysis.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_workflows():
    results = models.Workflow.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_genes():
    results = models.Gene.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_interactions():
    genes = models.Gene.objects()
    for gene in genes:
        gene.interactions = []
        gene.save()

@db_manager.command
def delete_all_psgn():
    genes = models.Gene.objects()
    for gene in genes:
        gene.psgn_connections = []
        gene.save()

@db_manager.command
def delete_all_pathways():
    results = models.Pathway.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_phenotypes():
    results = models.Phenotype.objects()
    for result in results:
        result.delete()

@db_manager.command
def delete_all_OMIM():
    genes = models.Gene.objects()
    for gene in genes:
        gene.omim = []
        gene.save()

@db_manager.command
def delete_all_orphanet():
    genes = models.Gene.objects()
    for gene in genes:
        gene.orphanet = []
        gene.save()

@db_manager.command
def delete_all_GOslim():
    genes = models.Gene.objects()
    for gene in genes:
        gene.goslim = []
        gene.save()

@db_manager.command
def delete_all_orthologs():
    genes = models.Gene.objects()
    for gene in genes:
        gene.orthologs = []
        gene.save()

@db_manager.command
def delete_all_paralogs():
    genes = models.Gene.objects()
    for gene in genes:
        gene.paralogs = []
        gene.save()

@db_manager.option('-p', '--project', dest='project', help='Project ID')
def delete_project(project):
    "Delete a specified project from the database. Does not remove directory or data"

    project = models.Project.objects.get(project_name = project)

    sys.stdout.write("Deleting project: %s (ID: %s)\n" % (project.project_name, project.id))

    project.delete()

def _parseEnsemblExternalMappingFile(file):
    mapping = defaultdict(list)
    with open(file, 'rU') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        reader.next()
        for row in reader:
            if row:
                #Skip LRG loci
                if row[0].startswith("LRG_"):
                    continue

                if row[0] and row[1]:
                    mapping[row[0]].append(row[1])

                #if mapping[row[0]]:
                #    mapping[row[0]].append(row[1])
                #else:
                #    ids = []
                #    ids.append(row[1])
                #    mapping[row[0]] = ids

    return mapping

def _parseMacArthurLOF(file):
    lof_dict = defaultdict(dict)
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            lof_dict[row['gene']]['score'] = row['P(rec)']
            lof_dict[row['gene']]['rank'] = row['rank']
            lof_dict[row['gene']]['tolerant'] = row['class']

    return lof_dict

if __name__ == "__main__":
    db_manager.run()