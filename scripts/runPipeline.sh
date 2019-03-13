#!/bin/bash
echo "seqs s3 to ec2 start" >> lambdaLogs/time.txt
date >>lambdaLogs/time.txt
./multidownload.sh /home/ubuntu/LINCS/Seqs_local 12 &> lambdaLogs/download_log 
echo "seqs s3 to ec2 finish" >> lambdaLogs/time.txt
date >>lambdaLogs/time.txt

echo "start split" >> lambdaLogs/time.txt
date >>lambdaLogs/time.txt
./runSplit.sh &> lambdaLogs/splitLog &

echo "upload split gz ec2 to s3 begin" >>lambdaLogs/time.txt
date >>lambdaLogs/time.txt
./runUploadSplitFiles.sh /home/ubuntu/LINCS/Aligns /home/ubuntu/LINCS/Seqs_local s3://myBucket/Aligns/ 7 8 >& lambdaLogs/uploadLog  
echo "upload split gz ec2 to s3 finish" >>lambdaLogs/time.txt
date >>lambdaLogs/time.txt

echo "invoke lambda begin" >>lambdaLogs/time.txt
date >>lambdaLogs/time.txt
python3 invokeBwaLambdas.py &> lambdaLogs/lambdaLog
echo "finish lambda\n">>lambdaLogs/time.txt
date >>lambdaLogs/time.txt

echo "download saf s3 to ec2 begin\n">>lambdaLogs/time.txt
date>>lambdaLogs/time.txt
aws s3 cp s3://myBucket/Outputs Outputs --recursive &> downloadSafLog
echo "download saf s3 to ec2 finish">>lambdaLogs/time.txt
date >>lambdaLogs/time.txt

echo "merge sam files begin">>lambdaLogs/time.txt
date >>lambdaLogs/time.txt
sudo ./umimerge_parallel -p 0 -f -i RNAseq_20150409 -s References/Broad_UMI/Human_RefSeq/refGene.hg19.sym2ref.dat -e References/Broad_UMI/ERCC92.fa -b References/Broad_UMI/barcodes_trugrade_96_set4.dat -a Outputs -o Counts -t 16 &> lambdaLogs/mergeLog
echo "merge sam files finish">>lambdaLogs/time.txt
date >>lambdaLogs/time.txt
