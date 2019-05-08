==============
BASIL Tutorial
==============

Introduction
============

In this section you will find a number of tutorials on the analysis of ASL data using the BASIL tools. If you are trying to use BASIL on your own data then a good place to begin is to find an example here that is as close to the data you have as a guide on how to proceed.

Single-delay ASL
================

Dataset 1: pcASL
----------------

This tutorial runs through the use of the BASIL command line tools on single-delay ASL data, the example data uses pcASL labelling and can be found here (~35 MB):

- `data_singledelay.zip <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BASIL/Tutorial?action=AttachFile&do=view&target=data_singledelay.zip>`_ 


Please note that the data is only provided for training purposes and should not be used for research without permission.

**Exercise 1.1: Tag-control subtraction**

The first (and simplest) thing to do with the data is tag-control subtraction to get a perfusion weighted image. This can be achieved with asl_file::

    asl_file --data=data --ntis=1 --iaf=tc --diff --out=diffdata --mean=diffdata_mean

Note that we have told asl_file that the data contains only a single delay ``--ntis=1``, that we have tag and control pairs ``--iaf=tc`` - standing for input ASL format). We have asked asl_file to perform tag control differencing ``--diff`` and then output to a file called diffdata, we have also asked for a second output in mean the mean has been taken across all the repeats in the data ``--mean=diffdata_mean``. If you examine the ``diffdata_mean`` image you should see something that looks like an image of perfusion. In fact if we were happy with relative perfusion values we could stop here.

**Exercise 1.2: Kinetic model inversion**

If we want to quantify perfusion in absolute units (ml/100g/min) then the next step is to invert the kinetic model - the model describes how the rate of delivery of labeled blood (and thus perfusion) is related to the measured signal. This can be achieved using ``oxford_asl`` (that makes a call to the ``basil`` command line tool to do the actual model inversion). To do this we now need to know some information about the data, namely:

- Labeling was performed using pcASL (thus we need the --casl option).
- Labelling was performed for 1.4 seconds (--bolus 1.4).
- The post-labeling delay was 1.5 seconds.

The post-labelling delay corresponds to an 'inversion time' of 2.9 seconds, i.e. 1.4 + 1.5. Thus we set ``--tis 2.9`` - this is the list of TIs, where we only have one in this case). Here we have data with only a single delay (and BASIL includes various features for multi-delay data) - ``oxford_asl`` sets a number of other options that are appropriate for single delay data ``--artoff --fixbolus``. Note that before FSL 5.0.6 you would need to add the ``--singleti`` option::

    oxford_asl -i diffdata -o ex1_2 --tis 2.9 --bolus 1.4 --casl

In the ``ex1_2/native_space`` directory you will find the results: a perfusion image that will look very similar to the one derived in the first exercise, but the magnitude scale will be different. However, this is still only in relative units, we have yet to complete the final step needed to get perfusion in absolute units.

You may also notice an arrival image, this gives the arterial (bolus) arrival time (in seconds) in every voxel. Since this cannot be estimated from single delay data the image will be uniform and default to 0.7 seconds (or whatever value you choose with the ``--bat`` option).

**Exercise 1.3: Calibration**

To finally get perfusion in absolute units we also need to calculate the equilibrium magnetization of arterial blood and include that in the calculations. Now we need to know some more information about our data.

- Background suppression was ON.

This should have improved our perfusion contrast by removing as much static tissue signal as possible. However, we with this cannot use the control images to estimate equilibrium magnetization values. Instead there is a separate dataset, called ``calib``, which is a series of control images with BGS OFF. We also have ``calib_body`` data in which control images were acquired with the same parameters but using the body coil. We will assume that the latter has a relatively flat sensitivity and use this to correct for sensitivity variation in the coil we used for the main acquisition. At this stage we also supply a structural image - this will be used to segment out the ventricles which will form the basis of our magnetization estimation, plus the perfusion image will also be transformed into the same resolution as the structural image via registration::

    bet data_singleti/struct struct_brain
    oxford_asl -i diffdata -o ex1_3 --tis 2.9 --bolus 1.4 --casl -c calib --cref calib_body -s struct_brain

In ``ex1_3/native_space`` you should find perfusion which is the same image as in Ex 1.2, but now it will have been joined by ``perfusion_calib``, which is perfusion in ml/100g/min. You should also find ``ex1_3/structural_space`` that has the same results but in a resolution that matches the structural image, the transformation for this process can be found in ``ex1_3/native_space/asl2struct.mat``.

The results of the calibration process will be saved in ``ex1_3/calib``, here you should find M0.txt which is the estimated M0 value needed to get the perfusion image into absolute units as well as ``refmask`` that you should inspect to check that it looks like the CSF in the ventricles has been selected. For this data it should have worked fine, but if you find data for which this has failed you might need to manually mask a region of CSF in the ventricles and supply that to ``oxford_asl`` using the ``--csf option`` (see the next exercise).

Note that ``oxford_asl`` always uses CSF as a reference for calibration. Other regions and alternative methods are possible and can be accessed through ``asl_calib``, which can be used to calculate an M0 value that can then be applied to the perfusion image.

**Exercise 1.4: Improving the registration and other options**

In the previous example registration was carried out between the raw ASL data and structural image, it should have worked but we would probably like to do better. However, this is a tricky process (due to the low resultion of the ASL data) and is particularly prone to failure if you only have data in which tag-control subtraction has already been done. In the previous example ``oxford_asl`` used the calibration image as the basis for registration (if this had not been available it would have used the perfusion image), it is possible to supply another image as the basis for registration: here we will use the mean of the raw data::

    fslmaths data -Tmean data mean
    bet datamean datamean_brain
    fslmaths data -Tmean datamean
    
Like before we will carry out calibration, but to save repeating the identification of the ventricles we will re-use the mask from before.

Finally, this time we will apply a spatial smoothing prior to the perfusion image. This exploits spatial homogeneity in the perfusion image to improve the estimation, but in an adaptive manner. This is similar to spatially smoothing the data before analysis, but it applies it to the estimated perfusion image and not the data, whilst also estimating the correct degree of spatial smoothing from the data::

    oxford_asl -i diffdata -o ex1_4 --tis 2.9 --bolus 1.4 --casl 
               -c calib --cref calib_body -s struct_brain 
               --csf ex1_3/calib/refmask --regfrom datamean_brain 
               --spatial

The structure of the results will be the same as in the previous exercise. Compare the two and see what difference the choice of registration basis has made and the use of the ``--spatial option``, this should be most clear on the native_space data.

Multi-delay ASL
===============

This tutorial runs through the use of ``oxford_asl`` (the command line tool) on a number of different multi-delay ASL datasets. Examples of pASL, pcASL and QUASAR data are included. The data can be found here (~50 MB):

- `basildata.zip <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BASIL/Tutorial?action=AttachFile&do=view&target=basildata.zip>`_ 

Please note that the data is only provided for training purposes and should not be used for research without permission.

DATASET 1: pulsed ASL
---------------------

This dataset is resting-state ASL data collected using a single-shot three-dimensional GRASE readout, TR/TE 3110/23 ms, 3.44x3.44x5mm, 22 slices using a matrix size 64x64, FAIR preparation, background suppression. Alternating control and tag pairs were acquired with 10 TIs (400, 620, 840, 1060, 1280, 1500, 1720, 1940, 2160, 2380 ms), each one repeated 10 times. The data is in the directory ``data_pasl``.

In this case the tag-control subtraction has already been done and the multiple measurements at each TI have been averaged, this has been put in the file ``diffdata.nii.gz``. (In a later exercise we will see how that was done). Have a look at the differenced data using FSLview::

    fslview pasl_data/diffdata &

You might like to flick through the different volumes and see if you can spot the label washing in and then decaying away again. Notice that the label arrives in some regions later than others.

**Exercise 1.1: CBF estimation**

Firstly we are going to do the model-fitting. Try typing this in your terminal::

    oxford_asl

If you call ``oxford_asl`` without any options you get the usage information. There is a lot of functionality (and we do not want to use all of it now), the three main things it can do are: model-fitting, registration and calibration. We need to do model-fitting to get CBF from the multi-TI data, so we will need:

- The tag-control differenced ASL data - we have this already.
- The TIs that were used to acquire the data - 0.4,0.62,0.84,1.06,1.28,1.5,1.72,1.94,2.16,2.38.
- The duration of the ASL bolus - the acquisition was FAIR, so the bolus duration is determined by the labelling coil (body). In fact the bolus duration for this data is around 1.1 s, so we will use that value, but allow the model fitting to refine that estimate (this is automatically done by ``oxford_asl`` unless we tell it otherwise).
- A starting guess for the bolus arrival time - we will take the default of 0.7 s, we dont need to be very precise as the model-fitting should work this out for us.
- Values of T1 and T1b for the field strength we used - data was aquired at 3T so use T1 of 1.3 s and T1b of 1.6 s.

We have all the information we need so all we have to do is run this command (check you understand what each bit does)::

    oxford_asl -i data_pasl/diffdata --tis 0.4,0.62,0.84,1.06,1.28,1.5,1.72,1.94,2.16,2.38 
               -o ex1_1 --bolus 1.1 --bat 0.7 --t1 1.3 --t1b 1.66 --artoff --spatial

Notice that we have turned off the estimation of the macrovascular component ``--artoff``, we will come back to this. We are using the 'spatial' mode, which is recommened as it exploits the natural spatial smoothness of the estimated CBF image.

In the results directory, ``ex1_1``, you will find a native_space directory that contains all the estimated images at the same resolution as the original data. You should find in there (and look at using FSLview):

- ``perfusion.nii.gz`` The estimated CBF image in the same (arbitrary) units as the original data.
- ``arrival.nii.gz`` The estimated bolus arrival time image (in seconds).

Since we would like the estimated CBF in physiological units (ml/100g/min) we also need:

- Calibration data - we have ``aslcalib.nii.gz`` which was acquired using the same readout but no inversion and no background suppression.
- A reference 'tissue' - in this case we are going to use CSF as our reference (yes it isn't actually a 'tissue').

``oxford_asl`` will, if given a structural image, try to automatically segment out the ventricles and use these as a CSF reference for calibration. We want a slightly quicker result, so there is a previously defined CSF mask, csfmask.nii.gz, to use. In this case there was a difference in the gain of a factor of 10 used when acquiring the calibration data (no background suppression) and the main ASL data (with background suppression).

Run the command again but with the extra calibration information supplied::

    oxford_asl -i data_pasl/diffdata --tis 0.4,0.62,0.84,1.06,1.28,1.5,1.72,1.94,2.16,2.38 
               -o ex1_1 --bolus 1.1 --bat 0.7 --t1 1.3 --t1b 1.66 --artoff --spatial 
               -c pasl_data/aslcalib --csf pasl_data/csfmask --cgain 10

You should now find in the results directory an extra image: ``perfusion_calib.nii.gz``, which is the estimated CBF image in ml/100g/min having used the separate calibration information. You should also find a ``calib`` subdirectory that includes the results of the calibration process, the main one being ``M0.txt`` that contains the estimated equilibrium magnetization of arterial blood (in scanner units). This M0 value was used to scale the perfusion image to get it into physiological units.

**Exercise 1.2: CBF estimation with a macro vascular component**

In the previous exercise we only fit a tissue based kinetic curve to the data. However, the data was not aquired with flow supression so there should be a substantial contirbution from ASL label still within larger vessels. What we should do, therefore, is to add a macro vascular component to account for this::

    oxford_asl -i data_pasl/diffdata -c aslcalib --csf csfmask 
               --tis 0.4,0.62,0.84,1.06,1.28,1.5,1.72,1.94,2.16,2.38 
               -o ex1_2 --bolus 1.1 --bat 0.7 --t1 1.3 --t1b 1.66 --spatial

Notice that we have run exactly the same command as the previous exercise, we have just removed ``--artoff``. By default ``oxford_asl`` always fits the macro vascualr component, even with flow suppression some arterial label can still be present.

In the results directory, ``ex1_2``, you will find the perfusion and arrival results again, along with an image called ``aCBV.nii.gz``, this is the estimated arterial cerebral blood volume image from the macro vascular component. Compare the images from this exercise with the previous one. Notice that the CBF is lower and arrival time is later where the magntiude of the aCBV image is large - around regions where large vessels would be expected.

DATASET 2: pseudo continuous ASL
--------------------------------

This dataset is resting-state pcASL data collected using an EPI readout, TR/TE 3750/14 ms, 3.75x3.75x7.5mm, 24 slices using a matrix size 64x64. Alternating control and tag pairs were acquired after 1.4 s of labelling at 5 different post labelling delays (200, 400, 600, 800, 1000 ms), each one repeated 12 times. The data is in the directory ``pcasl_data``

We are going to need to know what the inversion times were for each measurement. For pASL this was the time between labelling and readout. For cASL we need the time from the start of labelling to readout, so our TI = labelling duration + post labelling delay. Thus the TIs are: 1.6, 1.8, 2.0, 2.2, 2.4 s.

**Exercise 2.1: Tag-control subtraction**

The first thing we need to do is take the raw ASL data and do tag-control subtraction to remove the static tissue contribution. We are also going to take the average of the multiple measurements at each TI to make the model-fitting faster (in practice would could skip this as ``oxford_asl`` could do this for us). We could split the data into separate volumes and do subtraction and averaging of these images before re-assembling it all together, but that would be tedious! Instead we have a command that knows how to deal with ASL data, what we want to do is::

    asl_file --data=data_pcasl/asl_raw_data --ntis=5 --ibf=rpt --iaf=tc --diff --mean=pcasl_diffdata

The command tells asl_file:

- Where to find the data.
- How many TIs there are in the file.
- That the data contains repeated measurements (where we have cycled through all the TIs each time).
- That the data is in tag-control pairs.
- That we want to do pairwise subtraction.
- That it should take the mean of each TI and save that as the output file in the current directory: ``pcasl_diffdata``.

Have a look at the data ``pcasl_diffdata`` in FSLview as we did for the pASL data. This set will look a bit different as we only have 5 TIs and these are all placed so that they will be near the peak of the kinetic curve. So we dont see the nice clear wash in of the label as we did before.

**Exercise 2.2: CBF estimation**

We will do CBF estimation in a very similar way to the pASL data. However, this time we will:

- Use a cASL model with the ``--casl`` option.
- Set the bolus duration to 1.4 s - the length of labeling. Since the cASL label is well defined we wont try to estimate its duration, so we add the ``--fixbolus`` option.
- Supply a structural image, which means that ``oxford_asl`` will try to register the ASL data to the structural image and give the CBF results in the same space at the structural. By default ``oxford_asl`` will try to register the estimated CBF image to the structural, this can be problematic as there may not be excellent contrast for this. The raw ASL data is a much better basis for registration so we will instruct ``oxford_asl`` to use this with the ``--regfrom`` commmand.
- Not supply a CSF mask. We will let ``oxford_asl`` automatically identify the CSF using the structural image.

Firstly we do a little pre-processing of the supporting images - mainly brain extraction::

    bet data_pcasl/struc struc_brain
    fslmaths data_pcasl/asl_raw_data -Tmean asl_raw
    bet asl_raw asl_raw_brain

The full command we need is (again see if you can identify what each term does)::

    oxford_asl -i pcasl_diffdata -c data_pcasl/calibration_head 
               --tis 1.6,1.8,2.0,2.2,2.4 -o ex2_2 
               --bolus 1.4 --bat 0.7 --t1 1.3 --t1b 1.66 
               --artoff --fixbolus --spatial --casl -s struc_brain 
               --regfrom asl_raw_brain

In the results directory, ``ex2_2``, you will find a native_space set of results, but also the same results at the resolution of the structural image ``struct_space``. As with the pASL results there are perfusion and bolus arrival time images. Since we only have 5 tightly spaced TIs we wont expect our arrival time images to be as good. You will also notice from the arrival time image that the mask generated by ``oxford_asl`` wasn't perfect - it includes all the brain, but some non brain too. We could have made our own mask and supplied it to ``oxford_asl`` with the ``-m`` option if we had wanted to. It is also worth looking at ``ex2_2/calib/refmask.nii.gz`` as this is the mask that was used to indentify the CSF in the calibration image, you should check that it looks like voxels within the ventricles have been indentified.

When we analysed the pASL data we also added a macro vascular component into the model. However, we wont do that here since all the TIs we have come quite late and we are likely to have missed most of the early arriving arterial based label.

DATASET 3: QUASAR
-----------------

The QUASAR variant of ASL makes use of a combination of flow suppressed and non suppressed multi-TI data to allow for a better separation of the tissue and macro vascular signals. This aids model-based analysis and also permits 'model-free' analysis similar to that used in DSC-MRI. QUASAR data also has all the information within it to do the calibration step. Because the QUASAR sequence is well defined we dont have to worry about all the options in ``oxford_asl``, in fact there is a special version specifcally desgined for QUASAR data called ``quasil``. Again just trying the command brings up the usage - there are not many options this time!

**Exercise 3.1: Model-based analysis**

Firstly we are going to do a model-based analysis, just like we did in exercise 2, but tailored for QUASAR data. The command we want is::

    quasil -i data_quasar/data -o ex3_1

In the results directory, ``ex3_1``, you should find perfusion and aCBV images to examine.

**Exercise 3.2: Model-free analysis**

Now we are going to compare the model-based results with numerical deconvolution (this is the method proposed in Petersen's original paper). quasil will also do this using the ``--mfree`` option::

    quasil -i data_quasar/data -o ex3_2 --mfree

Like the model-based analysis both perfusion and aCBV images are produced. Compare the model-based and model-free results, you should find that the model-free perfusion values are generally lower than the model-based results, primiarly due to the underestimation of the numerical deconvolution.

DATASET 4: Turbo-QUASAR
-------------------------

Turbo-QUASAR achieves full brain coverage and improves the SNR of QUASAR by using multiple labelling pulses to create a longer effective bolus duration while retaining the other characteristics of QUASAR. Due to the frequent labelling pulses, MT effects can be an issue affecting both calibration and CBF quantification. The analysis pipeline ``toast`` includes options to either correct the MT effects or use a separately acquired calibration data, in addition to quantifying the main hemodynamic parameters such as perfusion, arterial transit time, and arterial blood volume.


**Exercise 4.1: Calibration by correcting for MT effects**

The command to quantify the hemodynamic parameters by correcting for MT effects in calibration::

    cd data_turbo_quasar

    toast -i data -o ex4_1 --infert1 --corrcal

The option --infert1 indicates that MT effects are corrected. The optional step --corrcal indicates that the partial volume effects on the edge of the brain are corrected.

**Exercise 4.2: Calibration by using a separately acquired**

Calibration can also be performed using a user-provided M0 image from a separate scan in the same session. The TR of the calibration image needs to be specified. A structural image needs to be provided in order to register the calibration image to the ASL image. The command is::

    toast -i data -o ex4_2  --calib M0 --tr 4.4 --struct structural --corrcal

**Exercise 4.3 Quantify arterial blood volume**

Turbo-QUASAR can also quantify arterial blood volume (ABV or aCBV) from the data using the --inferart option. We could use either of the calibration methods. The command is::

    toast -i data -o ex4_3_1 --infert1 --corrcal --inferart

or::

    toast -i data -o ex4_3_2 --calib M0 --tr 4.4 --struct structural --corrcal --inferart





Acknowledgments
===============

Thanks are due to Tom Okell, Brad MacIntosh, Dan Gallichan, Michael Kelly, Esben Petersen, Xavier Golay, Lena Václavů, and Aart Nederveen for the provision of the ASL data used in these exercises.