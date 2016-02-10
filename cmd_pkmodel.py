from __future__ import division, print_function

import multiprocessing
import multiprocessing.pool
import time
import numpy as np
import yaml
import nibabel as nib

from pkview.widgets.PharmaWidgets import run_pk


def yaml_loader(filepath):
    with open(filepath, "r") as fd:
        data = yaml.load(fd)
    return data


def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    # In python every function is an object so this is a quick and dirty way of adding a variable
    # to a function for easy access later. Prob better to create a class out of compute?
    run_pk.queue = queue


def save_file(file1, hdr, data1):
    # get header
    header1 = hdr

    # modify header
    shp1 = header1.get_data_shape()
    header1.set_data_shape(shp1[:-1])
    header1.set_data_dtype(data1.dtype)

    # Save the current overlay or save a specific overlay
    img1 = nib.Nifti1Image(data1, header1.get_base_affine(), header=header1)
    # Save image
    img1.to_filename(file1)


# Load config from yaml
c1 = yaml_loader('cmd_pkconfig.yaml')
c1 = c1['RIT005']

queue = multiprocessing.Queue()
pool = multiprocessing.Pool(processes=2, initializer=pool_init, initargs=(queue,))

# get volumes to process

print("Loading images")
img = nib.load(c1['Files']['DCE'])
img1 = img.get_data()
hdr = img.get_header()
img_dims = img1.shape
img = nib.load(c1['Files']['ROI'])
roi1 = img.get_data()
img = nib.load(c1['Files']['T10'])
t101 = img.get_data()

print("Gettng parameters")
# Extract the text from the line edit options
R1 = c1['Param']['R1']
R2 = c1['Param']['R2']
DelT = c1['Param']['T']
InjT = c1['Param']['InjT']
TR = c1['Param']['TR']
TE = c1['Param']['TE']
FA = c1['Param']['flip_angle']
thresh1val = c1['Param']['v1thresh']
Dose = 0

# getting model choice from list
model_choice = c1['Configuration']['model_choice']

baseline1 = np.mean(img1[:, :, :, :3], axis=-1)

print("Convert to list of enhancing voxels")
img1vec = np.reshape(img1, (-1, img1.shape[-1]))
T10vec = np.reshape(t101, (-1))
roi1vec = np.array(np.reshape(roi1, (-1)), dtype=bool)
baseline1 = np.reshape(baseline1, (-1))

print("Make sure the type is correct")
img1vec = np.array(img1vec, dtype=np.double)
T101vec = np.array(T10vec, dtype=np.double)
roi1vec = np.array(roi1vec, dtype=bool)

print("subset")
# Subset within the ROI and
img1sub = img1vec[roi1vec, :]
T101sub = T101vec[roi1vec]
baseline1sub = baseline1[roi1vec]

# Normalisation of the image
img1sub = img1sub / (np.tile(np.expand_dims(baseline1sub, axis=-1), (1, img1.shape[-1])) + 0.001) - 1

print("Running pk")
# run_pk(img1sub, T101sub, R1, R2, DelT, InjT, TR, TE, FA, Dose, model_choice)
#
result = pool.apply_async(func=run_pk, args=(img1sub, T101sub, R1, R2, DelT, InjT, TR, TE, FA, Dose, model_choice))

progress = 0
while progress < 100:
    num_row, progress = queue.get()
    print("Progress: ", progress)
    time.sleep(5)

var1 = result.get()

roi1v = np.array(roi1vec, dtype=bool)

#Params: Ktrans, ve, offset, vp
Ktrans1 = np.zeros((roi1v.shape[0]))

ktemp = var1[2]
ktemp[ktemp < 0] = 0
ktemp[ktemp > 2] = 2
Ktrans1[roi1v] = ktemp

ve1 = np.zeros((roi1v.shape[0]))
ve1[roi1v] = var1[2][:, 1] * (var1[2][:, 1] < 2.0) + 2 * (var1[2][:, 1] > 2.0)
ve1 *= (ve1 > 0)

kep1p = Ktrans1 / (ve1 + 0.001)
kep1p[np.logical_or(np.isnan(kep1p), np.isinf(kep1p))] = 0
kep1p *= (kep1p > 0)
kep1 = kep1p * (kep1p < 2.0) + 2 * (kep1p >= 2.0)

offset1 = np.zeros((roi1v.shape[0]))
offset1[roi1v] = var1[2][:, 2]

vp1 = np.zeros((roi1v.shape[0]))
vp1[roi1v] = var1[2][:, 3]

estimated_curve1 = np.zeros((roi1v.shape[0], img_dims[-1]))
estimated_curve1[roi1v, :] = var1[1]

residual1 = np.zeros((roi1v.shape[0]))
residual1[roi1v] = var1[0]

# Convert to list of enhancing voxels
Ktrans1vol = np.reshape(Ktrans1, (img_dims[:-1]))
ve1vol = np.reshape(ve1, (img_dims[:-1]))
offset1vol = np.reshape(offset1, (img_dims[:-1]))
vp1vol = np.reshape(vp1, (img_dims[:-1]))
kep1vol = np.reshape(kep1, (img_dims[:-1]))
estimated1vol = np.reshape(estimated_curve1, img_dims)

# thresholding according to upper limit
# p = np.percentile(Ktrans1vol, thresh1val)
# Ktrans1vol[Ktrans1vol > p] = p
# p = np.percentile(kep1vol, thresh1val)
# kep1vol[kep1vol > p] = p

print("Saving File")
save_file('Ktrans.nii', hdr, Ktrans1vol)
save_file('model_curves.nii', hdr, estimated1vol)



