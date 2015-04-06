#!/usr/bin/env python

import datetime
from flask import url_for
from kvasir import db
from hashlib import md5

from flask.ext.security import UserMixin, RoleMixin

class User(db.Document, UserMixin):
    nickname = db.StringField(max_length=255, required=True)
    email = db.EmailField(required=True, unique=True)
    slug = db.StringField()
    
    about_me = db.StringField()
    office = db.StringField()
    phone = db.StringField()
    
    last_seen = db.DateTimeField(default=datetime.datetime.now, required=True)
    
    tasks = db.ListField(db.ReferenceField('Task'))
    projects = db.ListField(db.ReferenceField('Project'))
    
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField('Role'), default=[])
    
    meta = {
        'indexes': ['nickname', 'email']
    }
    
    def get_absolute_url(self):
        return url_for('user', kwargs={"slug": self.slug})

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
    
    def is_user_or_admin(self):
        for role in self.roles:
            if role.name == 'User' or role.name == 'Admin':
                return True
            
        return False
    
    def is_admin(self):
        for role in self.roles:
            if role.name == 'Admin':
                return True
            
        return False

    def __repr__(self):
        return '<User %r>' % (self.nickname)
    
    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)

class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

class GenericVariant(db.Document):
    genes = db.ListField(db.ReferenceField('Gene'))
    strand = db.StringField(max_length=10)
    type = db.StringField(max_length=10)
    
    meta = {'allow_inheritance': True}

class Variant(GenericVariant):
    chromosome = db.StringField(required=True)
    position = db.StringField(required=True)
    build = db.StringField(required=True)
    ref_allele = db.StringField(required=True)
    alt_allele = db.StringField(required=True)
    
    annotation_sets = db.ListField(db.EmbeddedDocumentField('VariantAnnotationSet'))
    publications = db.ListField(db.ReferenceField('Publication'))
    
    samples = db.ListField(db.ReferenceField('Sample'))

class VariantAnnotationSet(db.DynamicEmbeddedDocument):
    annotation_source = db.StringField(required=True)
    annotator = db.StringField(required=True)
    

class Publication(db.Document):
    title = db.StringField(required=True)
    abstract = db.StringField(required=True)

    pubmed_id = db.StringField()
    doi = db.StringField()
    pdf = db.FileField()


class Project(db.Document):
    project_name = db.StringField(max_length=100, required=True, unique=True)
    slug = db.StringField(max_length=255, required=True, unique=True)
    type = db.StringField(max_length=50, required=True)
    project_desc = db.StringField()
    path = db.StringField()
    assembly_dir = db.StringField()
    last_updated = db.DateTimeField(default=datetime.datetime.now, required=True)
    
    meta = {
        'indexes': ['-last_updated', 'slug'],
        'ordering': ['-last_updated']
    }
    
    def get_absolute_url(self):
        return url_for('project', kwargs={"slug": self.slug})
    
    tasks = db.ListField(db.ReferenceField('Task'))
    files = db.ListField(db.ReferenceField('File'))
    samples = db.ListField(db.ReferenceField('Sample'))
    gemini_databases = db.ListField(db.ReferenceField('GDatabase'))
    
    analyses = db.ListField(db.EmbeddedDocumentField('Analysis'))
    notes = db.ListField(db.EmbeddedDocumentField('Note'))

class GDatabase(db.Document):
    file = db.StringField(required=True)
    slug = db.StringField()
    short_name = db.StringField(max_length=50)
    projects = db.ListField(db.ReferenceField('Project'))

    variants_of_interest = db.ListField(db.ReferenceField('Variant'))
    results = db.ListField(db.ReferenceField('GResult'))

class GResult(db.Document):
    header = db.StringField()
    js_header = db.ListField(db.StringField())
    json = db.FileField()
    query = db.StringField()
    query_slug = db.StringField()

    created_on = db.DateTimeField()
    created_by = db.ReferenceField('User')
    last_accessed = db.DateTimeField()

class Note(db.EmbeddedDocument):
    user = db.ReferenceField('User')
    body = db.StringField(required=True)
    posted = db.DateTimeField(default=datetime.datetime.now, required=True)
    
    meta = {
        'ordering': ['-posted']
    }

class Task(db.Document):
    assigned_user = db.ReferenceField('User')
    assigned_by_user = db.ReferenceField('User')
    project = db.ReferenceField('Project')
    
    date_assigned = db.DateTimeField(default=datetime.datetime.now, required=True)
    date_due = db.DateTimeField()
    description = db.StringField(required=True)
    priority = db.StringField(max_length=10)
    completed = db.BooleanField()

class HumanPhenotype(db.Document):
    hpo_id = db.StringField()
    hpo_term = db.StringField()
    disease_ids = db.ListField(db.StringField())

class Gene(db.Document):
    ensembl_id = db.StringField(required=True)
    slug = db.StringField(required=True)
    
    hgnc = db.StringField
    
    chromosome = db.StringField()
    band = db.StringField()
    description = db.StringField()
    biotype = db.StringField()
    status = db.StringField()
    strand = db.StringField()
    start = db.IntField()
    end = db.IntField()
    
    macarthur_lof_score = db.FloatField()
    macarthur_lof_tolerant = db.StringField()
    macarthur_lof_rank = db.FloatField()
    
    hgnc_ids = db.ListField(db.StringField())
    ccds_ids = db.ListField(db.StringField())
    ucsc_ids = db.ListField(db.StringField())
    uniprot_ids = db.ListField(db.StringField())
    entrez_ids = db.ListField(db.StringField())
    synonyms = db.ListField(db.StringField())
    
    omim = db.ListField(db.EmbeddedDocumentField('OMIM'))
    orphanet = db.ListField(db.EmbeddedDocumentField('Orphanet'))
    transcripts = db.ListField(db.EmbeddedDocumentField('Transcript'))
    goslim_terms = db.ListField(db.EmbeddedDocumentField('GOSlim'))
    interactions = db.ListField(db.EmbeddedDocumentField('Interaction')) 
    psgn_connections = db.ListField(db.EmbeddedDocumentField('PSGN'))
    expression = db.ListField(db.EmbeddedDocumentField('Expression'))
    phenotypes = db.ListField(db.EmbeddedDocumentField('Phenotype'))
    
    paralogs = db.ListField(db.ReferenceField('Gene'))
    variants = db.ListField(db.ReferenceField('Variant'))
    pathways = db.ListField(db.ReferenceField('Pathway'))
    
    user_description = db.StringField()
    summaries = db.ListField(db.EmbeddedDocumentField('GeneSummary'))
    
    meta = {
        'indexes': ['ensembl_id', 'hgnc_ids', 'slug']
    }
    
    def get_absolute_url(self):
        return url_for('gene', kwargs={"slug": self.slug})
    
    #pathways = db.relationship('Pathway', backref = 'gene', lazy = 'dynamic')
    #orphanet = db.relationship('Orphanet', backref = 'gene', lazy = 'dynamic')
    #orthologs = db.relationship('Ortholog', backref = 'gene', lazy = 'dynamic')

class GeneList(db.Document):
    genes = db.ListField(db.ReferenceField('Gene'))
    name = db.StringField(required=True, unique=True)
    description = db.StringField()

class GeneSummary(db.EmbeddedDocument):
    id = db.StringField()
    text = db.StringField()
    last_edited_by = db.ReferenceField('User')
    last_modified = db.DateTimeField(default=datetime.datetime.now)
    type = db.StringField()

class Pathway(db.Document):
    name = db.StringField()
    source = db.StringField()
    external_id = db.StringField()
    members = db.ListField(db.ReferenceField('Gene'))

class OMIM(db.EmbeddedDocument):
    omim_id = db.StringField()
    description = db.StringField()

class Orphanet(db.EmbeddedDocument):
    accession = db.StringField()
    description = db.StringField()

class Phenotype(db.EmbeddedDocument):
    term = db.StringField()
    id = db.StringField()

class Transcript(db.EmbeddedDocument):
    transcript_id = db.StringField()
    protein_id = db.StringField()
    start = db.IntField()
    end = db.IntField()
    biotype = db.StringField()

class Expression(db.EmbeddedDocument):
    cell_type = db.StringField()
    disease_state = db.StringField()
    organism_part = db.StringField()

class Interaction(db.EmbeddedDocument):
    interactor_ensembl_id = db.StringField()
    system = db.StringField()
    phenotype = db.StringField()
    modifications = db.StringField()
    qualifications = db.StringField()
    type = db.StringField()
    source = db.StringField()
    throughput = db.StringField()
    score = db.FloatField
    pubmed_id = db.StringField()
    interaction_source_id = db.StringField()

class GOSlim(db.EmbeddedDocument):
    go_id = db.StringField()
    go_desc = db.StringField()

class PSGN(db.Document):
    interactor_ensembl_id = db.StringField()
    similarity = db.FloatField()

class Sample(db.Document):
    sample_id = db.StringField(required=True, unique=True)
    project_id = db.ReferenceField('Project', required=True)
    species_name = db.StringField()
    species_ncbi_id = db.StringField()

    bam_files = db.ListField(db.StringField())
    vcf_files = db.ListField(db.StringField())
    genotype_files = db.ListField(db.StringField())
    phenotypes = db.ListField(db.StringField())
    
    status = db.StringField()
    maternal_id = db.ReferenceField('Sample')
    paternal_id = db.ReferenceField('Sample')
    
    variants = db.ListField(db.ReferenceField('Variant'))

class File(db.Document):
    name = db.StringField(required=True)
    desc = db.StringField()
    file = db.FileField(required=True)
    #location = db.StringField(required=True)


    uploaded_by = db.ReferenceField('User', required=True)
    projects = db.ListField(db.ReferenceField('Project'))
    
    file_notes = db.ListField(db.EmbeddedDocumentField('FileNote'))

class FileNote(db.EmbeddedDocument):
    body = db.StringField(required=True)
    posted = db.DateTimeField(default=datetime.datetime.now, required=True)
    
    user = db.ReferenceField('User', required=True)


class GenericGenomicRegion(db.Document):
    genome = db.StringField(required=True)
    chromosome = db.StringField(required=True)
    start = db.IntField(required=True)
    end = db.IntField(required=True, unique_with=['chromosome', 'start'])
    
    meta = {
        'allow_inheritance': True,
        'indexes': ['chromosome', 'start', 'end']
        }


class CoverageStatRegion(GenericGenomicRegion):
    sample_coverage = db.ListField(db.EmbeddedDocumentField('SampleCoverage'))
    low_cov_samples = db.ListField(db.ReferenceField('Sample'))
    cov_gap_samples = db.ListField(db.ReferenceField('Sample'))
    no_read_samples = db.ListField(db.ReferenceField('Sample'))
    poor_qual_samples = db.ListField(db.ReferenceField('Sample'))


class SampleCoverage(db.EmbeddedDocument):
    sample = db.ReferenceField('Sample')
    coverage = db.StringField()


class Resource(db.Document):
    resource_type = db.StringField()
    location = db.StringField()
    desc = db.StringField()