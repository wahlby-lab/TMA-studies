TMA-studies
===========

This is a project to align TMA cores coming from different consecutive TMA slides stained for different proteins using IHC.

In this project we cover the following topics:

| <!-- -->       | <!-- -->               |
|:--------------:|:----------------------:|
| Unmixing       | Registration           |
| Segmentation   | protein co-expression  |
| Image analysis | Software               |


## Video tutorials

We have designed an example for setting up your own TissUUmaps. The videos also comment on the general aspects of the design of TissUUmaps.
For insight on the usage of the code see the following sections. This is not an end-to-end software but rather a collection of scripts that require a basic setup of data. We include inside this project some libraries, like [Alpha-AMD](https://github.com/MIDA-group/py_alpha_amd_release) for registration and our utility functions to deal with DZI tiled images and perform unmixing and other preprocessing operations,

<table>
    <tr>
        <td width="50%">
            <a href="https://tissuumaps.research.it.uu.se/TMA-studies/">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/videoAbstract.png" />
            </a>
        </td>        
        <td width="50%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-intro">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track1.png" />
            </a>
        </td>
    </tr>
    <tr>
        <td>
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Quant.png">
           </a>
        </td>        
        <td>
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Tumor.png">
           </a>
        </td>
    </tr>    
</table>

Basic data setup
----------

### DZI pyramids
For this specific implementation of our methodology, you need to have the TMA slides as DZI pyramids. Cores should be annotated and there needs to be a simple text configuration file to know which slides should be processed and where information must be found.

DZI tiles can be created using [VIPS](https://libvips.github.io/libvips/) and [Openslide](https://openslide.org/), which accept the formats as listed in their website:

*Aperio (.svs, .tif)
*Hamamatsu (.vms, .vmu, .ndpi)
*Leica (.scn)
*MIRAX (.mrxs)
*Philips (.tiff)
*Sakura (.svslide)
*Trestle (.tif)
*Ventana (.bif, .tif)
*Generic tiled TIFF (.tif)

### Core annotations

You can have several TMA slides, stained for different proteins, you must choose the one all the others will be aligned to, this will be called "fixed" and the rest will be "moving". Additionally, cores locations must be in a polygon format in image coordinates.

This implementation expects a JSON file with the following structure:

```javascript
{
    "regions": {
        "<protein name>":{
            "<case>": #
            "<block>": #
            "property": "moving" or "fixed"
            "regionX1":{
                "id":
                "points":[] //in normalized coordinates divigin by image width
                "globalPoints": [] //points in image coordinates
                "len": # //length of the point array
                //bounding box
                "_xmin",  //normalized values
                "_xmax",  //normalized values
                "_ymin",  //normalized values
                "_ymax",  //normalized values
                "_gxmin", //image coordinate values
                "_gxmax", //image coordinate values
                "_gymin", //image coordinate values
                "_gymax", //image coordinate values                
            }
        }
    }
}
```

### CSV with experiment data

You need a CSV telling the code where everything is. Each line contains the values: protein ,block, format of slide, case, a prefix to the files (if any), the location of the associated dzi, and the name of the JSON describing cores.

Se examples below

To annotate the cores we use our own interface available in this repository in [viewer](https://github.com/wahlby-lab/TMA-studies/tree/master/viewer). More information on how to use our viewer here: [TissUUmaps](https://github.com/wahlby-lab/TissUUmaps)


[(Click here to see video instead of gif)](https://tissuumaps.research.it.uu.se/TMA-studies/index.html#section-data)
![Using TissUUmaps](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/TissUUmaps.gif)
![JSON and CSV formats](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/JSON-CSV-example.jpg)

Steps for using the code
==========================

<table>
    <tr>
        <td width="65%">
            <p>To start, follow these instructions, there is no need to go over all the repository, just start here and if you want, watch the video:</p>
            <p>The file <a href="https://github.com/wahlby-lab/TMA-studies/blob/master/blockAlign.py">blockAlign.py</a> runs 3 steps:</p>
            <ul>
                <li>Color unmixing </li>
                <li>Registration </li>
                <li>Creating co-expression map of the TMA </li>
            </ul>
            <p>To begin, make sure you specify in the script: </p>
            <ul>
                <li>The location of the CSv we mentioned before. </li>
                <li>The location of the JSON file with the core spatial information (specified within the CSV). </li>
                <li>The location of the DZI pyramids</li>
                <li>The location where everything will be saved</li>
                <li>The location (if any) of a palette for the colors you want to unmix (one per stain) If no location is given, we use a default color for H and one for DAB </li>
                <li>Resolution level</li>
        </td>       
        <td width="35%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-intro">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track1.png" />
            </a>
        </td>
    </tr>    
</table>

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



