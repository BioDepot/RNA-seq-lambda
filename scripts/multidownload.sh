#!/bin/bash
SEQS_DIR=$1
nThreads=$2
lockDir=/tmp/locks.$$
mkdir -p $lockDir

runJob(){
 lasti=$((${#dirs[@]} - 1))
 for i in $(seq 0 ${lasti}); do
  if (mkdir $lockDir/lock$i 2> /dev/null ); then
   dir=${dirs[$i]}
   echo thread $1 working on $dir
   echo aws s3 cp s3://egria/Seqs/$dir $SEQS_DIR/$dir
   aws s3 cp s3://egria/Seqs/$dir $SEQS_DIR/$dir
   
  fi
 done
 exit
}
dirs=( $(aws s3 ls s3://myBucket/Seqs/ | awk '{print $4}'))

for i in $(seq 2 $nThreads); do
	  runJob $i &
done
runJob 1 &
wait
rm -rf $lockDir
