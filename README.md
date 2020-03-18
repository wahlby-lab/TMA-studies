TMA-studies
===========

This is a project to streamline the alignment of cores coming from different TMA slides.

The slides are consecutive and each is stained for a different protein using IHC.

TissUUmaps
----------

This code is adapted to our problem and it is adaptable to similar questions.

To use it, we asume the cores are selected using the [TissUUmaps viewer](https://github.com/wahlby-lab/TissUUmaps) to create a JSON file containing the information. If you don't want to use TissUUmaps we can still show you how to create the information file.

We also asume that the slides are converted to [DeepZoom pyramids](https://github.com/wahlby-lab/TissUUmaps#How-to-start) and we expect a CSV file with the information of your experiment.

The following images show the formats expected.

![Using TissUUmaps](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/TissUUmaps.gif)
![JSON and CSV formats](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/JSON-CSV.jpg)

The CSV has to have the columns: protein,block,format,case,prefix,filename,jsonname
The JSON should contain all the regions (cores) per protein (can be more than 2 proteins) and each protein contains the property of "moving" or "fixed" which tells which is the reference protein slide that guides the registrtion.

Each region contains the spatial information of a core, such as points in pixels, points in global coordinates, bounding boxes, an associated protein and a length. A color can be used in TissUUmaps to find the different cores visually.

3 Steps for using the code
==========================

The file [blockAlign.py](https://github.com/wahlby-lab/TMA-studies/blob/master/blockAlign.py) runs 3 steps:
* Color unmixing
* Registration
* Creating co-expression map of the TMA

To begin, make sure you specify in the script: 
* The location of the CSv we mentioned before. 
* The location of the JSON file with the core spatial information (specified within the CSV). 
* The location of the DZI pyramids
* The location where everything will be saved
* The location (if any) of a palette for the colors you want to unmix (one per stain) If no location is given, we use a default color for H and one for DAB
* Resolution level

Step 1 - Unmixing
-----------------
In this first step the program will go through the JSON file, finding the regions (cores) in every slide and creating an individual RGB image of the cores. These images will be unmixed with the information available, either a palette or default values. The images will be saved. This step also creates a binary mask that will inform the next step on where to find the information to find the transformations

Step 2 - Registration
---------------------
In this second step, we use the H stain which is common to pairs of cores, to find the alignment. If step 1 ran succesfully, then we have the H images of each core so we give them to [py_alpha-AMD](https://github.com/MIDA-group/py_alpha_amd_release) to find the registration. This is the only registration framework that combines spatial and intensity information making it ideal for this purpose. The transformation T is applied and serialized for possible future use.
Once T is found, H and DAB images are transformed and saved.

Step 3 - Wrapping up
--------------------
Once the individual cores have been transformed, they can be arranged back in the same position as the original TMA and we can create a Co-expression map of the proteins and an H colocalizaiton map to verify the transformations T. This step is not fully necessary. The images can be created separately and inspected. For this you cna use [combineImages.py](https://github.com/wahlby-lab/TMA-studies/blob/master/combineImages.py)



