#!/bin/bash

# Script that loads three volumes automatically in the PkViewer

# Usage:
# ./pk_RIT <patient_number> <scan> <type>
# eg ./pk_RIT 5 PRE Ktrans

SCAN=$2
PATIENT0=`printf "%0*d" 3 $1`
MAP=$3

DIRECTORY1="/netshares/mvlprojects6/Registration_Data/RIT_Data2_ben/Nifti/RIT$PATIENT0/$SCAN"
DIRECTORY2="/data/Biomedia_extra/Results/4_rit_entire_run/RIT$PATIENT0$SCAN"
echo $DIRECTORY1
echo $DIRECTORY2

#load itk-snap images
python PkView2.py --image $DIRECTORY1/dceMRI.nii --roi $DIRECTORY1/ROImind2.nii --overlay $DIRECTORY2/$MAP.nii &
