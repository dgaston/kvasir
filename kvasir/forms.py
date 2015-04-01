from flask_wtf import Form

from wtforms import TextField, TextAreaField, FileField, FieldList, FormField, SelectField, DecimalField, DateField, SelectMultipleField
from wtforms import widgets

from flask_security.forms import RegisterForm

from wtforms.validators import DataRequired, Length

from kvasir.models import User, Project, GeneList

def fetch_projects():
    projects = Project.objects()
    choices = []
    
    for project in projects:
        choice = (project.slug, project.project_name)
        choices.append(choice)
    
    return choices

def fetch_users():
    users = User.objects()
    choices = []
    
    for user in users:
        choice = (user.email, user.nickname)
        choices.append(choice)
    
    return choices

def fetch_gene_lists():
    lists = GeneList.objects()
    choices = []

    choices.append(('none', 'None'))

    for list in lists:
        choice = (list.name, list.name)
        choices.append(choice)
    
    return choices

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ExtendedRegisterForm(RegisterForm):
    nickname = TextField('Nickname', validators = [DataRequired()])

class GQueryForm(Form):
    intervals = TextAreaField('intervals')
    
    gene_lists = fetch_gene_lists()

    gene_filter = SelectField(u'gene filter', choices=gene_lists)
    filter_method = SelectField(u'filter type', choices=[('exclude', 'Exclude from Results'), ('include', 'Include Results Only Appearing in List')])
    
    query = SelectField(u'select', choices=[('all', 'All fields in the variant and gene_detailed tables'),
        ('clinical', 'Clinical: Only core variant/gene info and clinical databases (ClinVar, OMIM)'),
        ('variant', 'All fields in the variant table only')])


    affected_filter = SelectField(u'affected filter', choices=[('none', 'None'),
        ('ref', 'Homozygous Reference'),
        ('refu', 'Homozyous Reference or Unknown Genotype'),
        ('variant', 'Heterozygous/Homozygous Variant or Unknown'),
        ('het', 'Heterozygous Variant'),
        ('hetu', 'Heterozygous Variant or Unknown'),
        ('hom', 'Homozygous Variant'),
        ('nhoma', 'Not Homozygous Alternative'),
        ('homu', 'Homozygous Variant or Unknown')])
    
    unaffected_filter = SelectField(u'unaffected filter', choices=[('none', 'None'),
        ('ref', 'Homozygous Reference'),
        ('refu', 'Homozyous Reference or Unknown Genotype'),
        ('variant', 'Heterozygous/Homozygous Variant or Unknown'),
        ('het', 'Heterozygous Variant'),
        ('hetu', 'Heterozygous Variant or Unknown'),
        ('nhoma', 'Not Homozygous Alternative'),
        ('hom', 'Homozygous Variant'),
        ('homu', 'Homozygous Variant or Unknown')])
    
    unknown_filter = SelectField(u'unknown filter', choices=[('none', 'None'),
        ('ref', 'Homozygous Reference'),
        ('refu', 'Homozyous Reference or Unknown Genotype'),
        ('variant', 'Heterozygous/Homozygous Variant or Unknown'),
        ('het', 'Heterozygous Variant'),
        ('hetu', 'Heterozygous Variant or Unknown'),
        ('hom', 'Homozygous Variant'),
        ('nhoma', 'Not Homozygous Alternative'),
        ('homu', 'Homozygous Variant or Unknown')])

    affected_number = SelectField(u'affected number', choices = [('all', 'All') , ('any', 'Any'), ('none', 'None')])
    unaffected_number = SelectField(u'unaffected number', choices = [('all', 'All') , ('any', 'Any'), ('none', 'None')])
    unknown_number = SelectField(u'unknown number', choices = [('all', 'All') , ('any', 'Any'), ('none', 'None')])
    
    impacts = SelectField(u'Variant impacts', choices=[('all', 'All'), ('med+high', 'Medium and High'), ('high', 'High')])
    mode = SelectField(u'Mode', choices=[('none', 'None/Normal'), ('denovo', 'de novo'), ('compound', 'Compound Heterozygotes'), ('sex-linked', 'Sex Linked')])
    
    evs_eur = DecimalField(label='evs_eur', default=-1, places=None, rounding=None)
    evs_afr = DecimalField(label='evs_afr', default=-1, places=None, rounding=None)
    evs_all = DecimalField(label='evs_all', default=-1, places=None, rounding=None)
    
    kg_eur = DecimalField(label='1kg_eur', default=-1, places=None, rounding=None)
    kg_afr = DecimalField(label='1kg_afr', default=-1, places=None, rounding=None)
    kg_amr = DecimalField(label='1kg_amr', default=-1, places=None, rounding=None)
    kg_asn = DecimalField(label='1kg_asn', default=-1, places=None, rounding=None)
    kg_all = DecimalField(label='1kg_all', default=-1, places=None, rounding=None)

    exac_eur = DecimalField(label='exac_eur', default=-1, places=None, rounding=None)
    exac_fin = DecimalField(label='exac_fin', default=-1, places=None, rounding=None)
    exac_afr = DecimalField(label='exac_afr', default=-1, places=None, rounding=None)
    exac_amr = DecimalField(label='exac_amr', default=-1, places=None, rounding=None)
    exac_eas = DecimalField(label='exac_eas', default=-1, places=None, rounding=None)
    exac_sas = DecimalField(label='exac_sas', default=-1, places=None, rounding=None)
    exac_all = DecimalField(label='exac_all', default=-1, places=None, rounding=None)
    exac_oth = DecimalField(label='exac_oth', default=-1, places=None, rounding=None)

class EditForm(Form):
    nickname = TextField('nickname', validators = [DataRequired()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.objects(nickname = self.nickname.data)
        if user:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True

class AssociationForm(Form):
    aoi = TextField(u'aoi', validators = [DataRequired()])
    fg = TextField(u'fg')
    trait = TextField(u'trait', validators = [DataRequired()])
    desc = TextField(u'desc')
    
    project_choices = fetch_projects()
    
    project = SelectField(u'projects', choices = project_choices)
    active = SelectField(u'active', choices = [('True', 'True'), ('False', 'False')])
    
    impact = DecimalField(u'impact', validators = [DataRequired()], places=None, rounding=None)
    confidence = DecimalField(u'conf', validators = [DataRequired()], places=None, rounding=None)

class EditAssociationForm(AssociationForm):
    reason = TextField(u'desc')

class AlleleForm(Form):
    ref_allele = TextField(u'ref_allele', validators = [DataRequired()])
    alt_allele = TextField(u'alt_allele', validators = [DataRequired()])
    source = TextField(u'source', validators = [DataRequired()])
    orientation = SelectField(u'orientation', choices=[('plus', 'plus'),
        ('negative', 'negative')])
    
    kg_eur = DecimalField(label='1kg_eur', places=None, rounding=None)
    kg_afr = DecimalField(label='1kg_afr', places=None, rounding=None)
    kg_amr = DecimalField(label='1kg_amr', places=None, rounding=None)
    kg_asn = DecimalField(label='1kg_asn', places=None, rounding=None)
    kg_all = DecimalField(label='1kg_all', places=None, rounding=None)

class FrequencyForm(Form):
    population = TextField(u'population', validators = [DataRequired()])
    frequency = DecimalField(label='frequency', places=None, rounding=None)

class PublicationForm(Form):
    title = TextField(u'title', validators = [DataRequired()])
    abstract = TextField(u'abstract', validators = [DataRequired()])
    pubmed_id = TextField(u'pubmed_id')
    doi = TextField(u'doi')

class MarkerForm(Form):
    dbsnp_id = TextField('dbsnp_id', validators = [DataRequired()])
    
    alleles = FieldList(FormField(AlleleForm), min_entries=1)
    associations = FieldList(FormField(AssociationForm), min_entries=1)
    
    def validate(self):
        if not Form.validate(self):
            return False
        
        return True

class AddSampleForm(Form):
    sample_id = TextField('id', validators = [DataRequired()])
    status = TextField('status')
    ngs = TextField('ngs')
    genotyping = TextField('genotyping')
    variants = TextField('variants')
    maternal_id = TextField('maternal')
    paternal_id = TextField('paternal')
    phenotypes = TextField('phenotypes')

    def validate(self):
        if not Form.validate(self):
            return False
        
        return True

class NoteForm(Form):
    note = TextAreaField('note')

class SummaryForm(Form):
    text = TextAreaField('text', validators = [DataRequired()])

class GenotypeSummaryForm(SummaryForm):
    genotype = TextField('genotype', validators= [DataRequired()])

class AssociationSummaryForm(SummaryForm):
    title = TextField('title', validators = [DataRequired()])
    type = TextField('type', validators = [DataRequired()])

class GeneSummaryForm(SummaryForm):
    type = TextField('type', validators = [DataRequired()])

class FileForm(Form):
    fileName = FileField('file')

class FileNoteForm(Form):
    file_note = TextAreaField('file_note')

class TaskForm(Form):    
    project_choices = fetch_projects()
    user_choices = fetch_users()
    
    project = SelectField(u'projects', choices = project_choices)
    assigned = SelectField(u'assigned', choices = user_choices)
    priority = SelectField(u'priority', choices = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])
    due = DateField(format='%Y-%m-%d')
    
    description = TextField(validators = [DataRequired()])
    
class SearchForm(Form):
    search = TextField('search', validators = [DataRequired()])

