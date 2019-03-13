#!/bin/bash

rm Aligns/* -rf
rm Counts/* -rf
rm Seqs_local/* -rf
rm Outputs/* -rf
aws s3 rm s3://myBucket/Outputs/ --recursive
aws s3 rm s3://myBucket/Aligns/ --recursive
