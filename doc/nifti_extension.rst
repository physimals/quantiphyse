NIFTI metadata extension
========================

Quantiphyse stores various metadata about its data sets which it would be useful to persist across loading and saving. 
The NIFTI format provides for this in the form of 'header extensions'.

Each header extension is identified by a code number so software can choose to pay attention only to header extensions that it knows about. Quantiphyse has been assigned the code ``42`` for its header extensions.
 
Quantiphyse extensions will be stored as strings in YAML format for easy serialization/deserialization to Python
and because YAML is already used as the basis for the batch format.

There has been suggestion that ``nibabel`` may add its own metadata as a NIFTI extension. This might
enable some of the Quantiphyse metadata to be deprecated, however this is not available at present.
 
The following set of metadata is an initial proposal, however any widget can save its own metadata by adding
a YAML-serializable object to the data sets ``metadata`` dictionary attribute. Hence this list is not
exhaustive.
 
Generic metadata
----------------
::

    Quantiphyse:
        roi : True/False        # Whether the data set should be treated as an ROI
        regions :               # ROI regions (codes and names)
            1 : tumour
            2 : nodes
        raw-2dt : True          # Indicates that 3D data should be interpreted as 2D+time
        dps: 3                  # Suggested number of decimal places to display for values
        
ASL data set structure
----------------------
::

    AslData:
      tis : [1.4, 1.6, ...]     # List of TIs
      plds : [2.5, 2.6, ...     # List of PLDs, alternative to TIs
      rpts : [4, 4, 4, ...]     # Repeats at each TI/PLD
      phases : [0, 45, 90, ...] # Phases in degrees for multiphase data
      nphases : 8               # Alternatively, number of evenly-spaced phases

CEST data set structure
-----------------------
::

    CestData:
      freq-offsets : [-300, -30, 0, 10, 20, ...] # Frequency offsets
      b0 : 9.4                                   # Field strength in T
      b1 : 0.55                                  # B1 in microT
      sat-time : 2                               # Continuous saturation time in s
      sat-mags : [1, 2, 3, 4, ...]               # Pulsed saturation magnitudes
      sat-durs : [1, 3, 2, 4, ...]               # Pulsed saturation durations in s
      sat-rpts : 1                               # Pulsed saturation repeats
  
