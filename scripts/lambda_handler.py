#lhhung 013119 - refactored and extended Dimitar Kumar's original script

from subprocess import call
import sys
import glob
import stat
import os
import boto3
import botocore
import time
import datetime
import json

# A utility function to run a bash command from python
def runCmd(cmd):
    sys.stderr.write("#{}\n".format(cmd))
    call([cmd], shell=True)

#utilities to remove directories and files except those in the whitelist
def removeDirectoriesExcept(rootDirectory,whiteList):
    for directory in os.popen('find {} -type d -mindepth 1 -maxdepth 1 '.format(rootDirectory)).read().split('\n')[0:-1]:
        if directory not in whiteList:
            sys.stderr.write("removing {}\n".format(directory))
            runCmd("rm {} -rf".format(directory))
            
def removeFilesExcept(rootDirectory,whiteList):
    for myFile in os.popen('find {} -type f '.format(rootDirectory)).read().split('\n')[0:-1]:
        if myFile not in whiteList:
            sys.stderr.write("removing {}\n".format(myFile))
            try:
                os.remove(myFile)
            except Exception as e:
                sys.stderr.write('unable to remove {}\n'.format(myFile))
                

def downloadFiles(sourceFile,destFile,bucketName,overwrite=True,verbose=True):
    sourceFile=sourceFile.replace("/home/ubuntu/LINCS/","")
    s3 = boto3.resource('s3')
    if overwrite or not os.path.exists(destFile):
        try:
            if verbose:
                sys.stderr.write("Downloading {} to {}\n".format(sourceFile,destFile))
                s3.Bucket(bucketName).download_file(sourceFile, destFile)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                sys.stderr.write("The object does not exist\n")
            else:
                raise
            
# Performs BWA for the given splitFile, filterCmd, and outputFile
def runBwa(splitFile,outputFile,filterCmd):
    cmdStr="/tmp/bwa aln -l 24 -t 2 /tmp/Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa /tmp/{} | /tmp/bwa samse -n 20 /tmp/Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa - /tmp/{} | {} > {} ".format(splitFile,splitFile,filterCmd,outputFile)
    sys.stderr.write("running cmd:\n{}\n".format(cmdStr))
    runCmd(cmdStr)

def uploadResultsTest(sourceFile,destFile,bucketName):
    sys.stderr.write("cp {} {}\n".format(sourceFile,destFile))
# Uploads the result to the appropriate S3 Aligns/splitFile folder
def uploadResults(sourceFile,destFile,bucketName):
    s3 = boto3.resource('s3')
    destFile=destFile.replace("/home/ubuntu/LINCS/Aligns","Outputs")
    return s3.meta.client.upload_file(sourceFile, bucketName,destFile)

# Lambda's entry point.
def lambda_handler(event, context):
    
    #### List of parameters to customize ####
    
    #bwa doesn't actually need the sequence information - just the name to figure out where the indices are
    #these files are empty to save space - probably should add the chrM.fa file 
    
    fakeFiles=['/tmp/Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa']
    
    #sourceFiles and directories used in other places
    alignDir='/tmp/Aligns'
    refDir='/tmp/Human_RefSeq'
    barcodeFile="/tmp/barcodes_trugrade_96_set4.dat" #in References/BroadUMI directory
    erccFile="/tmp/ERCC92.fa"
    symToRefFile="/tmp/refGene.hg19.sym2ref.dat"
    

    sourceFiles= ["umimerge_filter", "bwa", "Human_RefSeq/chrM.fa", "barcodes_trugrade_96_set4.dat","ERCC92.fa" ,"refGene.hg19.sym2ref.dat", "Human_RefSeq/refGene.hg19.txt", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.amb", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.ann", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.bwt", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.fai", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.pac", "Human_RefSeq/refMrna_ERCC_polyAstrip.hg19.fa.sa"]
    
    #change bucketName as necessary - could pass it through event in json payload
    bucketName = "myBucket"    
    
    #### End parameters list ####

    #get splitFile from json payload - may want to load s3 bucket from here also instead of hardcoding
    fullPathSplitFile = event["splitFile"]
    splitFile=os.path.basename(fullPathSplitFile)
    
    sys.stderr.write("Running handler for splitFile [{}] at time {}\n"
        .format(
            splitFile,
            datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        )
    )

    sys.stderr.write("Json dump:\n{}\n".format(json.dumps(event, indent=4, sort_keys=True)))
    
    #cleanup files - keep RefSeq and binaries if already there
    whiteListFiles=[]
    for sourceFile in sourceFiles:
        destFile='/tmp/'+sourceFile
        whiteListFiles.append(destFile)
    whiteListFiles=whiteListFiles + fakeFiles
    
    removeDirectoriesExcept('/tmp',['/tmp/Human_RefSeq'])
    removeFilesExcept('/tmp',whiteListFiles)

    #create directories
    for directory in [alignDir,refDir]:
        runCmd('mkdir -p {}'.format(directory))
    
    #make empty fakeFiles
    for fakeFile in fakeFiles:
        if not os.path.exists(fakeFile):
            runCmd('touch {}'.format(fakeFile))
    
    #download source files
    for sourceFile in sourceFiles:
        destFile='/tmp/'+sourceFile
        downloadFiles(sourceFile,destFile,bucketName,overwrite=False,verbose=True)

    #download splitFile 
    downloadFiles(fullPathSplitFile,'/tmp/' + splitFile, bucketName,overwrite=True,verbose=True)

    
    #make sure that executables have correct permissions
    for executable in ('/tmp/bwa','/tmp/umimerge_filter'):
        runCmd('chmod +x {}'.format(executable))
   
    #run bwa 
    outputFile='{}/{}.saf'.format(alignDir,os.path.splitext(splitFile)[0])
    filterCmd="/tmp/umimerge_filter -s {} -b {} -e {}".format(symToRefFile,barcodeFile,erccFile)
    #filterCmd="grep -v '^\@'"
    sys.stderr.write("Starting bwa at {}".format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
    runBwa(splitFile,outputFile,filterCmd)

    #upload results
    uploadFile=os.path.dirname(fullPathSplitFile)+'/'+os.path.basename(outputFile)
    sys.stderr.write("Starting bwa at {}".format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))
    uploadResults(outputFile,uploadFile,bucketName)
    #uploadResultsTest(outputFile,uploadFile,bucketName)
    #write done time
    sys.stderr.write("Finished at {}".format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')))

