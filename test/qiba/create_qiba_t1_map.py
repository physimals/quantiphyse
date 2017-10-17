import nibabel as nib 
import numpy as np
import math

t1 = np.full([50, 80, 1], 1)

#img = nib.Nifti1Image(t1, np.identity(4))
#img.to_filename("qiba_t1_new.nii")

#mask = np.ones([50, 80, 1])
#img = nib.Nifti1Image(mask, np.identity(4))
#img.to_filename("qiba_mask.nii")

#mask = np.zeros([50, 80, 1])
#mask[16, 12] = 1
#img = nib.Nifti1Image(mask, np.identity(4))
#img.to_filename("qiba_mask_onevox.nii")

#img = nib.load("c:\\Users\\ctsu0221\\build\data\\testdata\\qiba\\qiba.nii")
#d = img.get_data()
#d2 = np.zeros(list(d.shape[:3]) + [1+d.shape[3]/20])
#print(d.shape, d2.shape)
#for t in range(d.shape[-1]):
#    if t % 20 == 0:
#        print(t, t/20)
#        d2[:,:,:,t/20] = d[:,:,:,t]
#i2 = nib.Nifti1Image(d2, np.identity(4))
#i2.to_filename("qiba_lesst_20.nii")

#img = nib.load("c:\\Users\\ctsu0221\\build\data\\testdata\\qiba\\qiba_lesst_20.nii")
img = nib.load("c:\\Users\\ctsu0221\\build\data\\testdata\\qiba\\qiba.nii")
d = img.get_data()
aif = d[25, 5, 0, :]

TR = 0.005
FA = math.radians(30)
s0 = float(aif[0])
T10 = 1.4
Rg = 4.5
R10 = 1.0/T10
E10 = math.exp(-TR/T10)
B = (1.0-E10) / (1.0-math.cos(FA) * E10)
HCT = 0.45
M0 = s0 / (B*math.sin(FA))
M00 = 50000

#o1 = open("aif_qiba_sig.txt", "w")
#o2 = open("aif_qiba_nohct.txt", "w")
#o3 = open("aif_qiba_hct.txt", "w")
#o4 = open("aif_qiba4.txt", "w")
for t, v in enumerate(aif):
	s = float(v)
	#se = (s-s0)/s0
	#c = 4.5*se
#	A = B*s/s0
	A1 = s/(M00*math.sin(FA))
	R11 = -(1.0/TR) * math.log((1.0-A1) / (1.0-math.cos(FA)*A1))
	C = (R11 - R10)/Rg

	# Alt method
	CA = s/s0
	v = math.log((1-CA*B)/(1-CA*B*math.cos(FA)))
	roft = (-1/TR)*v
	cb = (roft - R10)/Rg
	print(float(t)/2, C/(1-HCT))

	#print(a, b, e10, R1)
	#r1 = (1.0/TR) * math.log((s0*math.sin(FA) - s*math.cos(FA))/(s0*math.sin(FA) - s))
	#if r10 == -1: r10 = r1
	#if R10 == -1: R10 = R1
	#t1  = 1.0/r1
	#c2 = (1.0/4.5)*(r1 - r10)
	#C2 = (1.0/4.5)*(R1 - R10)
	#o1.write("%f\n" % se)
	#o2.write("%f\n" % c)
	#o3.write("%f %f %f\n" % (s, R1, C2))
	#o1.write("%f\n" % s)
	#o2.write("%f\n" % cb)
	#o3.write("%f\n" % (cb / (1-HCT)))
	#bs = s0*(1-math.exp(-TR*(R10 + R1 * C2)))/(1-math.cos(FA)*math.exp(-TR*(1/T10 + R1*C2)))
	R12 = Rg*cb + R10
	A2 = math.exp(-TR*R12)
	S2 = M00 * math.sin(FA) * (1.0-A2) / (1.0-A2*math.cos(FA) )
	#print(s, A1, R11, C, R12, A2, S2)
	


#t1 = np.full([320, 320, 128], 1)
#img = nib.Nifti1Image(t1, np.identity(4))
#img.to_filename("T10.nii")

#f = open("qin_data/aif.txt", "r")
#o = open("qin_data/aif_ds10.txt", "w")
#for idx, line in enumerate(f.readlines()):
#	s = float(line)
#	if idx % 10 == 0:
#		o.write("%f\n" % (s*4.5))
#f.close()
#o.close()

T1 = 1.4
E1 = math.exp(-TR/T1)
s = M00 * math.sin(FA)*(1-E1)/(1-math.cos(FA)*E1)
print(s)

print(s0*(1.0-math.cos(FA)*E10)/(math.sin(FA)*(1-E10)))