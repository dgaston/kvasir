#!/usr/bin/env python

# -*- coding: utf-8 -*-
import sys, argparse
import subprocess as sub
import pipeline as pipe

from WorkflowConfig import parseProjectConfig
from multiprocessing import Pool
from collections import defaultdict


def run_bwa(configuration):
    '''Run BWA MEM with multiple threads on one or more samples'''

    #print type(configuration)
    sys.stdout.write("Preparing to run BWA on the following samples:\n")
    for sample in configuration['samples']:
        sys.stdout.write("%s\n" % sample['name'])

    # Run BWA in multi-threaded mode on each sample specified
    for sample in configuration['samples']:
        try:
            sample['bam']
        except KeyError:
            sys.stdout.write("Running BWA for sample %s\n" % sample['name'])
            output = "%s.sorted" % sample['name']
            logfile = "%s.bwa.log" % sample['name']
            command = ("""bwa mem -t %s -R "@RG\tID:%s\tSM:%s\tPL:illumina" -M -v 2 %s %s %s | """
                       """samtools view -b -S -u - | samtools sort -@ %s - %s""" \
                       % (configuration['num_cores'], sample['rg_id'], sample['rg_sm'], configuration['reference_genome'],
                          sample['fastq1'], sample['fastq2'], configuration['num_cores'], output))

            code = pipe.runAndLogCommand(command, logfile)
            pipe.checkReturnCode(code)

            sys.stdout.write("Finished BWA for sample: %s\n" % sample['name'])

    sys.stdout.write("Finished BWA\n")


def run_MarKDuplicates(configuration):
    '''Run Picard MarkDuplicates'''

    pool = Pool(processes=int(configuration['num_cores']))

    sys.stdout.write("Running MarkDuplicates\n")

    instructions = []
    for sample in configuration['samples']:
        logfile = "%s.markduplicates.log" % sample['name']

        try:
            input = sample['bam']
        except KeyError:
            input = "%s.sorted.bam" % sample['name']

        output = "%s.dedup.sorted.bam" % sample['name']
        metrics = "%s.dedup.metrics" % sample['name']

        command = (
            "java -Xmx4g -jar %s/MarkDuplicates.jar CREATE_INDEX=true INPUT=%s OUTPUT=%s METRICS_FILE=%s VALIDATION_STRINGENCY=LENIENT" %
            (configuration['picard_bin_dir'], input, output, metrics))
        instructions.append((command, logfile))
        sys.stdout.write("Finished running MarkDuplicates for sample %s\n" % sample['name'])

    sys.stdout.write("Setting up worker pool for multiple processes\n")
    result = pool.map_async(pipe.runMulti, instructions)
    codes = result.get()
    pool.close()
    pool.join()

    pipe.checkReturnCodes(codes)

    sys.stdout.write("Finished Running MarkDuplicates\n")


def run_RealignIndels(configuration):
    '''Create Indel realignment targets and run realignment step'''

    pool = Pool(processes=int(configuration['num_cores']))
    instructions = []

    sys.stdout.write("Realigning Indels\n")
    for sample in configuration['samples']:
        sys.stdout.write("Running TargetCreator for sample %s\n" % sample['name'])

        input = "%s.dedup.sorted.bam" % sample['name']
        targets = "%s.targets.intervals" % sample['name']
        output = "%s.realigned.sorted.bam" % sample['name']

        logfile = "%s.targetcreator.log" % sample['name']
        logfile2 = "%s.realignment.log" % sample['name']

        command = ("java -Xmx4g -jar %s -T RealignerTargetCreator -nt %s -R %s -known %s -known %s -I %s -o %s"
                   % (
            configuration['gatk_bin'], configuration['num_cores'], configuration['reference_genome'], configuration['indel1'], configuration['indel2'], input,
            targets))

        command2 = (
            "java -Xmx4g -jar %s -T IndelRealigner -I %s -o %s -known %s -known %s -targetIntervals %s -R %s --read_filter NotPrimaryAlignment" %
            (configuration['gatk_bin'], input, output, configuration['indel1'], configuration['indel2'], targets, configuration['reference_genome']))

        instructions.append((command2, logfile2))

        code = pipe.runAndLogCommand(command, logfile)
        pipe.checkReturnCode(code)

        sys.stdout.write("Finished Identifying Targets for %s\n" % sample['name'])

    sys.stdout.write("Finished Identifying Realignment Targets\n")
    sys.stdout.write("Realigning targets\n")

    result = pool.map_async(pipe.runMulti, instructions)
    codes = result.get()
    pool.close()
    pool.join()

    pipe.checkReturnCodes(codes)

    sys.stdout.write("Finished Realigning Targets\n")


def run_Recalibrator(configuration):
    '''Recalibrate and print bases'''

    sys.stdout.write("Recalibrating bases for all samples\n")

    instructions1 = []
    instructions2 = []
    instructions3 = []
    instructions4 = []

    for sample in configuration['samples']:
        sys.stdout.write("Generating commands for multiprocessing steps %s\n" % sample['name'])

        logfile1 = "%s.baserecalibrator.log" % sample['name']
        logfile2 = "%s.baserecalibrator_second_pass.log" % sample['name']
        logfile3 = "%s.printreads.log" % sample['name']
        logfile4 = "%s.printplots.log" % sample['name']

        realigned = "%s.realigned.sorted.bam" % sample['name']
        recal_config = "%s.recal" % sample['name']
        post_recal= "%s.post.recal" % sample['name']
        plots = "%s.recalibration_plots.pdf" % sample['name']
        output = "%s.recalibrated.sorted.bam" % sample['name']

        #Calculate covariates
        #command1 = ("java -Xmx4g -jar %s -T BaseRecalibrator -I %s -o %s -R %s --knownSites %s"
        #            % (configuration['gatk_bin'], realigned, recal_config, configuration['reference_genome'], configuration['dbsnp']))

        #Second pass after bqsr
        #command2 = ("java -Xmx4g -jar %s -T BaseRecalibrator -I %s -o %s -R %s --knownSites %s -BQSR %s"
        #            % (configuration['gatk_bin'], realigned, post_recal, configuration['reference_genome'], configuration['dbsnp'], recal_config))

        #Print recalibrated BAM
        command3 = ("java -Xmx4g -jar %s -T PrintReads -I %s -o %s -R %s -BQSR %s"
                    % (configuration['gatk_bin'], realigned, output, configuration['reference_genome'], recal_config))

        #Analysis of Covariates and Plot Printing
        #command4 = ("java -Xmx4g -jar %s -T AnalyzeCovariates -before %s -after %s -plots %s"
        #            % (configuration['gatk_bin'],recal_config, post_recal, plots))

        #instructions1.append((command1, logfile1))
        #instructions2.append((command2, logfile2))
        instructions3.append((command3, logfile3))
        #instructions4.append((command4, logfile4))

    # sys.stdout.write("Running multiprocessing of BaseRecalibrator\n")
    # pool = Pool(processes=int(configuration['num_cores']))
    # result1 = pool.map_async(pipe.runMulti, instructions1)
    # codes = result1.get()
    # pool.close()
    # pool.join()
    #
    # pipe.checkReturnCodes(codes)
    #
    # sys.stdout.write("Running multiprocessing of Post Calibration BaseRecalibrator\n")
    # pool2 = Pool(processes=int(configuration['num_cores']))
    # result2 = pool.map_async(pipe.runMulti, instructions2)
    # codes = result2.get()
    # pool2.close()
    # pool2.join()
    #
    # pipe.checkReturnCodes(codes)

    sys.stdout.write("Running multiprocessing of PrintReads\n")
    pool3 = Pool(processes=int(configuration['num_cores']))
    result3 = pool3.map_async(pipe.runMulti, instructions3)
    codes = result3.get()
    pool3.close()
    pool3.join()

    pipe.checkReturnCodes(codes)

    # sys.stdout.write("Running Analysis and Plotting of Covariates\n")
    # pool4 = Pool(processes=int(configuration['num_cores']))
    # result4 = pool4.map_async(pipe.runMulti, instructions4)
    # codes = result4.get()
    # pool4.close()
    # pool4.join()
    #
    # pipe.checkReturnCodes(codes)

    sys.stdout.write("Finished recalibrating bases\n")


def run_UnifiedGenotyper(configuration):
    '''Call Multi-Sample Variants with UnifiedGenotyper'''

    sample_inputs = []

    for sample in configuration['samples']:
        sample = "-I %s.recalibrated.sorted.bam" % sample['name']
        sample_inputs.append(sample)

    sample_bam_string = " ".join(sample_inputs)

    sys.stdout.write("Running UnifiedGenotyper for samples in project %s\n" % configuration['project_name'])
    output = "%s.raw.ug.vcf" % configuration['project_name']
    logfile = "%s.unifiedgenotyper.log" % configuration['project_name']

    command = (
        "java -Xmx4g -jar %s -T UnifiedGenotyper -R %s %s -o %s --dbsnp %s -stand_call_conf 50.0 -stand_emit_conf 10.0 -dcov 200 --genotype_likelihoods_model BOTH --output_mode EMIT_VARIANTS_ONLY -nt %s"
        % (configuration['gatk_bin'], configuration['reference_genome'], sample_bam_string, output, configuration['dbsnp'],
           configuration['num_cores']))

    code = pipe.runAndLogCommand(command, logfile)
    pipe.checkReturnCode(code)

    sys.stdout.write("Finished UnifiedGenotyper\n")

def run_HaplotypeCaller(configuration):
    "Call and Genotype variants using the HaplotypeCaller"

    instructions = []
    gvcfs = []

    for sample in configuration['samples']:
        sample = "%s.recalibrated.sorted.bam" % sample['name']
        output = "%s.raw.hc.snps.indels.g.vcf" % sample['name']
        logfile = "%s.hc.log" % sample['name']

        command = ("java -Xmx4G -jar %s -T HaplotypeCaller -R %s -I %s -o %s --emitRefConfidence GVCF --variant_index_type LINEAR --variant_index_parameter 128000 --dbsnp %s"
                % (configuration['gatk_bin'], configuration['reference_genome'], sample_bam, output, configuration['dbsnp']))

        instructions.append((command, logfile))
        gvcfs.append(output)

    sys.stdout.write("Running HaplotypeCaller for samples in project %s\n" % configuration['project_name'])

    result = pool.map_async(pipe.runMulti, instructions)
    codes = result.get()
    pool.close()
    pool.join()

    pipe.checkReturnCodes(codes)

    sys.stdout.write("Finished Running HaplotypeCaller\n")
    sys.stdout.write("Running Joint Genotyping on Cohort\n")

    command = ("java -Xmx4G -jar %s -T HaplotypeCaller -R %s"
               % (configuration['gatk_bin'], configuration['reference_genome']))

    code = pipe.runAndLogCommand(command, logfile)
    pipe.checkReturnCode(code)

    sys.stdout.write("Finished Joint Genotyping Cohort\n")


def run_AnnotationAndFilters(configuration):
    '''GATK Annotate and Variant Filters'''

    sample_inputs = []

    for sample in configuration['samples']:
        sample = "-I %s.recalibrated.sorted.bam" % sample['name']
        sample_inputs.append(sample)

    sample_bam_string = " ".join(sample_inputs)

    raw_vcf = "%s.raw.ug.vcf" % configuration['project_name']
    annotated_vcf = "%s.annotated.vcf" % configuration['project_name']
    filtered_vcf = "%s.filtered.vcf" % configuration['project_name']

    logfile1 = "%s.variantannotation.log" % configuration['project_name']
    logfile2 = "%s.variantfiltration.log" % configuration['project_name']

    command1 = (
        "java -Xmx4g -jar %s -T VariantAnnotator -R %s %s -o %s --variant %s -L %s --dbsnp %s -nt %s --group StandardAnnotation" %
        (configuration['gatk_bin'], configuration['reference_genome'], sample_bam_string, annotated_vcf, raw_vcf, raw_vcf,
         configuration['dbsnp'], configuration['num_cores']))
    command2 = (
        "java -Xmx4g -jar %s -T VariantFiltration -R %s -o %s --variant %s --filterExpression 'MQ0 > 50' --filterName 'HighMQ0' --filterExpression 'DP < 10' --filterName 'LowDepth' --filterExpression 'QUAL < 10' --filterName 'LowQual' --filterExpression 'MQ < 10' --filterName 'LowMappingQual'" %
        (configuration['gatk_bin'], configuration['reference_genome'], filtered_vcf, annotated_vcf))

    sys.stdout.write("Annotating variants\n")
    code = pipe.runAndLogCommand(command1, logfile1)
    pipe.checkReturnCode(code)

    sys.stdout.write("Applying variant filters\n")
    code = pipe.runAndLogCommand(command2, logfile2)
    pipe.checkReturnCode(code)

    sys.stdout.write("Finished annotating and filtering variants using the GATK\n")


def run_Normalization(configuration):
    filtered_vcf = "%s.filtered.vcf" % configuration['project_name']
    normalized_vcf = "%s.normalized.vcf" % configuration['project_name']
    logfile = "%s.vt_norm.log" % configuration['project_name']

    command = ("zless %s | sed 's/ID=AD.Number=./ID=AD,Number=R/' | vt decompose -s - | vt normalize -r %s - > %s" %
               (filtered_vcf, configuration['reference_genome'], normalized_vcf))

def run_SNPEff(configuration):
    '''Run snpEff Annotations'''

    normalized_vcf = "%s.normalized.vcf" % configuration['project_name']
    snpEff_vcf = "%s.snpEff.%s.vcf" % (configuration['project_name'], configuration['snpeff_reference'])
    logfile = "%s.snpeff.log" % configuration['project_name']

    command = ("java -Xmx4G -jar %s -classic -formatEff -v %s %s > %s" %
               (configuration['snpeff_bin'], configuration['snpeff_reference'], normalized_vcf, snpEff_vcf))

    sys.stdout.write("Running snpEff\n")
    code = pipe.runAndLogCommand(command, logfile)
    pipe.checkReturnCode(code)

    sys.stdout.write("Finished snpEff\n")


def run_GEMINI(configuration):
    '''Run GEMINI'''

    snpEff_vcf = "%s.snpEff.%s.vcf" % (configuration['project_name'], configuration['snpeff_reference'])
    gemini_db = "%s.snpEff.%s.db" % (configuration['project_name'], configuration['snpeff_reference'])
    logfile = "%s.gemini.log" % configuration['project_name']

    command = ("%s load --cores %s -v %s -t snpEff %s" %
               (configuration['gemini_docker'], configuration['num_cores'], snpEff_vcf, gemini_db))

    sys.stdout.write("Running GEMINI\n")
    code = pipe.runAndLogCommand(command, logfile)
    pipe.checkReturnCode(code)

    sys.stdout.write("Finished GEMINI\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config_file', help="Input configuration file [Required]")
    parser.add_argument('-s', '--stage', help="Stage to restart from [Default = 1]", default=1, type=int)

    args = parser.parse_args()

    configuration = (parseProjectConfig(args.config_file))
    #print type(configuration)

    sys.stdout.write("Starting stage: %s\n" % args.stage)

    if args.stage == 1:
        run_bwa(configuration)
        args.stage = args.stage + 1

    if args.stage == 2:
        run_MarKDuplicates(configuration)
        args.stage = args.stage + 1

    if args.stage == 3:
        run_RealignIndels(configuration)
        args.stage = args.stage + 1

    if args.stage == 4:
        run_Recalibrator(configuration)
        args.stage = args.stage + 1

    # if args.stage == 5:
    #     run_UnifiedGenotyper(configuration)
    #     args.stage = args.stage + 1
    #
    # if args.stage == 6:
    #     run_AnnotationAndFilters(configuration)
    #     args.stage = args.stage + 1
    #
    # if args.stage == 7:
    #     run_Normalization(configuration)
    #     args.stage = args.stage + 1
    #
    # if args.stage == 8:
    #     run_SNPEff(configuration)
    #     args.stage = args.stage + 1
    #
    # if args.stage == 9:
    #     run_GEMINI(configuration)
    #     args.stage = args.stage + 1

    sys.stdout.write("Completed pipeline\n")