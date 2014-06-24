#!/bin/bash

# Script that loads three volumes automatically in the PkViewer

# Usage:
# ./pk_RIT <patient_number> <scan> <type>
# eg ./pk_RIT 5 PRE Ktrans

SCAN=$2
PATIENT0=`printf "%0*d" 3 $1`
MAP=$3

DIRECTORY1="/netshares/mvlprojects6/Registration_Data/RIT_PK_Andre/RIT_RSNA/PK/RIT_$PATIENT0/$SCAN"
echo $DIRECTORY1


#load itk-snap images
python PkView2.py --image $DIRECTORY1/dceCut.nii --roi $DIRECTORY1/roiCut.nii --overlay $DIRECTORY1/${MAP}Map.nii &
