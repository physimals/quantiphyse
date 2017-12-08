from __future__ import division, print_function

import nibabel as nib
import numpy as np

from quantiphyse.analysis.pk_model import PyPk

folder1 = "/local/engs1170/Dropbox/BioMedIA1/Code/9_GUI/data/"
#folder1 = "/home/benjamin/Dropbox/BioMedIA1/Code/9_GUI/data/"
file1 = "RIT005img_original.nii"

img = nib.load(folder1 + file1)
img1 = np.array(img.get_data())
T10 = np.ones(img1.shape[:3])

baseline1 = np.mean(img1[:, :, :, :3], axis=-1)
img1 = img1 / (np.tile(np.expand_dims(baseline1, axis=-1), (1, 1, img1.shape[-1])) + 0.001) - 1

# Convert to list of enhancing voxels
img1vec = np.reshape(img1, (-1, img1.shape[-1]))
T10vec = np.reshape(T10, (-1))

# Lydia's values
R1 = 3.7
R2 = 4.8

t1 = np.arange(0, img1.shape[-1])*12
t1 = t1 /60.0

Dose = 0.1

dce_flip_angle = 12.0
dce_TR = 4.108/1000.0
dce_TE = 1.832/1000.0

ub = [10, 1, 0.5, 0.5]
lb = [0, 0.05, -0.5, 0]

AIFin = [2.65, 1.51, 22.40, 0.23, 0]

# Doesn't play at all nicely with any changes to numpy arrays...
# Seems to be an issue with __cinit__ and passing in arrays where there is possibly some memory corruption or something.
# Might be best to set these values in a separate method and then manually copy them to a vector variable in the class?
#... set_data method and manually copy vectors?

# Otherwise just move back to swig which might be more stable


# Subset
img1sub = np.ascontiguousarray(np.array(img1vec[:11410, :], dtype=np.double))
T10sub = np.ascontiguousarray(T10vec[:11410], dtype=np.double)
t1 = np.ascontiguousarray(t1, dtype=np.double)


# Subset
#img1sub = np.ascontiguousarray(img1vec)
#T10sub = np.ascontiguousarray(T10vec)
#t1 = np.ascontiguousarray(t1)


Pkclass = PyPk(t1, img1sub, T10sub)
Pkclass.set_bounds(ub, lb)
Pkclass.set_AIF(AIFin)
Pkclass.set_parameters(R1, R2, dce_flip_angle, dce_TR, dce_TE, Dose)
Pkclass.rinit(1)
x = Pkclass.run(5000)
print(x)
x = Pkclass.run(5000)
print(x)

#print("get curve")
fcurve = Pkclass.get_residual()

fcurveb = Pkclass.get_fitted_curve()

print("convert to numpy")

fcurve2 = np.array(fcurveb)

print (fcurve2.shape)

