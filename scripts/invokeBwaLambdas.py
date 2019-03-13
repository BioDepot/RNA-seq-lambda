#!/usr/bin/python3
#lhhung 013119 - cleaned up code from Dimitar Kumar
#lhhung 031019 - added timing code
import os
import sys
import json
import glob
import boto3
import datetime,time
from timeit import default_timer as timer

def checkS3Output(splitFiles,startTimes,finishTimes,outputName,s3Files):
    doneFlag=1    
    for splitFile in splitFiles:
        if splitFile not in finishTimes: 
            if outputName[splitFile] in s3Files:
                finishTimes[splitFile]=timer()
            else:
                doneFlag=0
    return doneFlag
         
def waitOnLambdas(splitFiles,startTimes,finishTimes,timeout=600):
    waitStartTime=timer()
    outputName={}
    for splitFile in splitFiles:
        outputName[splitFile]=os.path.splitext(os.path.basename(splitFile))[0]
    while (1):
        s3Files=[]
        s3Lines=os.popen("aws s3 ls s3://myBucket/Outputs/ --recursive | awk {'print $4'}").read().split( )
        for s3Line in s3Lines:
            s3Files.append(os.path.splitext(os.path.basename(s3Line))[0])
        if checkS3Output(splitFiles,startTimes,finishTimes,outputName,s3Files) or timer()-waitStartTime > timeout:
            return
        time.sleep(1)

def getSplitFilenames(directory,suffix):
    sys.stderr.write("{}/*.{}\n".format(directory,suffix))
    return glob.glob("{}/*.{}".format(directory,suffix))

def startLambdas(splitFiles,awsAccessKeyId,awsSecretAccessKey,region,functionName,startTimes):
    lambdaClient = boto3.client('lambda',aws_access_key_id=awsAccessKeyId,aws_secret_access_key=awsSecretAccessKey,region_name=region)
    for splitFile in splitFiles:
        startTimes[splitFile]=timer()
        sys.stderr.write('working on {}\n'.format(splitFile))
        lambdaClient.invoke(FunctionName=functionName,InvocationType="Event",Payload=json.dumps({"splitFile": splitFile}))
        
def main():
    # Change these parameters
    functionName = "your_function_name"
    awsAccessKeyId = "ABCDEFGHIJKLMNOPQRST"
    awsSecretAccessKey = "SomeAwsSecretAccessKeyShouldGoHere123456"
    region = "us-east-1"
    
    #where your reads reside
#    directory='/home/ubuntu/LINCS/Aligns/*'
    directory='/home/ubuntu/LINCS/Aligns/*'
#    suffix='fq.gz'
    suffix='fq'
    splitFiles=getSplitFilenames(directory,suffix)
    startTimes={}
    finishTimes={}
    start = timer()
    startLambdas(splitFiles,awsAccessKeyId,awsSecretAccessKey,region,functionName,startTimes)
    sys.stderr.write('Time elapsed for launch is {}\n'.format(timer()-start))
    waitOnLambdas(splitFiles,startTimes,finishTimes)
    sys.stderr.write('Time elapsed for lambdas is {}\n'.format(timer()-start))
    for splitFile in splitFiles:
        print ('{} {} {} {}'.format(startTimes[splitFile],finishTimes[splitFile],finishTimes[splitFile]-startTimes[splitFile],splitFile))
    
if __name__ == "__main__": 
    main()
