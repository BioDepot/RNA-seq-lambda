#!/bin/bash
ALIGNS_DIR=$1
SEQS_DIR=$2
S3Path=$3
#Threads before split is done
NTHREADS1=$4
#Threads after split is done
NTHREADS2=$5


while [ 1 ]; do
 nseq=`ls $SEQS_DIR | wc -l`
 ndone=`ls ${ALIGNS_DIR}/*.done | wc -l`
 if [ "${nseq}" == "${ndone}" ]; then
     ./uploadSplitFiles.sh  $ALIGNS_DIR $S3Path $NTHREADS2
    ./
    date
    exit
 fi
 ./uploadSplitFiles.sh  $ALIGNS_DIR $S3Path $NTHREADS1
 sleep 1
done
