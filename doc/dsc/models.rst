.. _dsc_models:

The DSC Vascular Model
======================

The standard vascular model
---------------------------

The model used is a specific physiological model for capillary transit of contrast within the blood generally termed the 
'vascular model' that was first described by Ostergaard [1]_ [2]_. This model has been extended to explicitly 
infer the mean transit time and also to optionally include correction for macro vascular contamination - contrast agent 
within arterial vessels [3]_.

An alternative to the model-based approach to the analysis of DSC-MRI data are 'non-parametric' approaches, that 
often use a Singular Value based Deconvolution to quantify perfusion. 

The CPI model
-------------

A key component of the DSC model is the *residue function* which describes the probability that a molecule of tracer 
that entered a voxel at :math:`t=0`, is still inside that voxel at a later time :math:`t`. As constructed this is a monotonically
decreasing function whose value at :math:`t=0` is 1 and which approaches 0 as :math:`t \rightarrow \infty`.

The CPI model [4]_ describes the residue function by performing cubic interpolation between a set of *control points*.
The control point at :math:`t=0` has a fixed value of 1 but the remaining control points are limited only by the
fact that each cannot take a larger value than the preceding one. By treating the control point values as
model parameters to infer we can infer the shape of the residue function without giving it an explicit mathematical
form.

By default the CPI model uses a fixed set of evenly spaced control points. In principle we can also allow these
points to move 'horizontally', i.e. change their time position. By doing so we might expect to be able to model
the residue function realistically with a smaller number of control points. In practice, while this is supported
by the model it can result in numerical instability which is linked to the fact that we need to prevent control
points from crossing each other, or degenerating to a single point. Adding a larger number of evenly spaced
fixed control points can be a better solution in this case.

References
----------

.. [1] *Mouridsen K, Friston K, Hjort N, Gyldensted L, Østergaard L, Kiebel S. Bayesian estimation of cerebral perfusion 
   using a physiological model of microvasculature. NeuroImage 2006;33:570–579. doi: 10.1016/j.neuroimage.2006.06.015.*

.. [2] *Ostergaard L, Chesler D, Weisskoff R, Sorensen A, Rosen B. Modeling Cerebral Blood Flow and Flow Heterogeneity From 
   Magnetic Resonance Residue Data. J Cereb Blood Flow Metab 1999;19:690–699.*

.. [3] *Chappell, M.A., Mehndiratta, A., Calamante F., "Correcting for large vessel contamination in DSC perfusion 
   MRI by extension to a physiological model of the vasculature", e-print ahead of publication. doi: 10.1002/mrm.25390*

.. [4] *Mehndiratta A, MacIntosh BJ, Crane DE, Payne SJ, Chappell MA. A control point interpolation method for the 
   non-parametric quantification of cerebral haemodynamics from dynamic susceptibility contrast MRI. NeuroImage 
   2013;64:560–570. doi: 10.1016/j.neuroimage.2012.08.083.*