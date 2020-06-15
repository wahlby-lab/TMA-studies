TMA-studies
===========

This is a project to align TMA cores coming from different consecutive TMA slides stained for different proteins using IHC.

In this project we cover the following topics:

| <!-- -->       | <!-- -->               |
|:--------------:|:----------------------:|
| Unmixing       | Registration           |
| Segmentation   | protein co-expression  |
| Image analysis | Software               |


## Explanation and video tutorials

For insight on the usage of the code see the following sections. This is not an end-to-end software but rather a collection of scripts that require a basic setup of data. We include inside this project some libraries, like [Alpha-AMD](https://github.com/MIDA-group/py_alpha_amd_release) for registration and our utility functions to deal with DZI tiled images and perform unmixing and other preprocessing operations. We also provide 2 DZI pyramids if you want to try out this code. See the data section. We have created explanatory videos. You can see out video abstract and 3 videos showing different aspects of running the code and observing the results.

If you want to try this and have a similar question, don't hesitate to contact us at the [Bioimage informatics national facility at SciLifLab (Sweden)](https://www.scilifelab.se/facilities/bioimage-informatics/)

<table>
    <tr>
        <td width="25%">
            <a href="https://tissuumaps.research.it.uu.se/TMA-studies/">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/videoAbstract.png" />
            </a>
        </td>        
        <td width="25%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-intro">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track1.png" />
            </a>
        </td>
        <td width="25%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Tumor.png">
           </a>
        </td> 
        <td width="25%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Quant.png">
           </a>
        </td> 
    </tr>    
</table>

## Basic data setup


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
========================

<table>
    <tr>
        <td width="65%">
            <p>To start, we refer to this part as track 1. Follow these instructions, there is no need to go over all the repository. Just start here and, if you want, watch the video:</p>
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
            </ul>
        </td>       
        <td width="35%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-intro">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track1.png" />
            </a>
        </td>
    </tr>    
</table>

## Track 2 - Additional steps


### Tumor segmentation

<table>
    <tr>
        <td width="65%">
            <p>This track continues after everything has run in track 1. Sometimes, to solve the question, you need to perform tumor segmentation. We use Random Forests to do so. In here you will find a handy notebook to perform image segmentation based on sparse annotations. In our case, an expert pathologist marked several cores from the whole experiment to mark areas with tumor, non-tumor and background. These images (i.e. sparse seeds, masks, annotations) allow us to determine where to find distinctive features under them.</p>
            <p>To use the notebook go to the <a href="https://github.com/wahlby-lab/TMA-studies/blob/master/RandomForestTMmaster.ipynb">RandomForestTMmaster.ipynb</a> notebook. To understand more about this process, watch the video</p>
        </td>       
        <td width="35%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Tumor.png">
           </a>
        </td>
    </tr>    
</table>

### Co-expression quantification

<table>
    <tr>
        <td width="65%">
            <p>After having a visual way of determining co-expression in cores in the maps we obtain in track 1. We might want to quantify the co-expression. Such quantification can be related to clinical data or become evidence for interesting unstudied relationships.</p>
            <p>To quantify using this implementation of the pipeline you need to have all the data mentioned before and have run all track 1 and tumor segmentation.</p>
            <p>The file  <a href="https://github.com/wahlby-lab/TMA-studies/blob/master/colocQuantification.py">colocQuantification.py</a> is the one we use for this purpose.</p>
            <p>Here we will study the specific locations of shared pieces of tissue and within tumor segmentation to quantify co-expression. </p>
        </td>       
        <td width="35%">
             <a href="https://tissuumaps.research.it.uu.se/howto.html#section-using">
            <img src="https://tissuumaps.research.it.uu.se/media/images/posters/TMA-studies/Track2-Quant.png">
           </a>
        </td> 
    </tr>    
</table>

Data
==========================

We provide two DZi pyramids and the annotated cores in json format, in case you want to try out the pipeline (the links take you to our website first):
<table>
    <tr>
        <td width="35%">
            <a href="../tissuudata/TMA/CD44v6_2B.7z"><img src="https://tissuumaps.research.it.uu.se//media/images/misc/TMA-studies/CD44v6dzismall.png" width="260px" alt="">
            </a><h5><a href="https://tissuumaps.research.it.uu.se/TMA-studies/#section-data">CD44v6 slide 2B
            </a></h5>
        </td>       
        <td width="35%">
             <a href="../tissuudata/TMA/Ecad_2B.7z"><img src="https://tissuumaps.research.it.uu.se/media/images/misc/TMA-studies/Ecaddzismall.png" width="260px" alt="">
                  </a><h5><a href="https://tissuumaps.research.it.uu.se/TMA-studies/#section-data">Ecad slide 2B
                </a></h5>
        </td> 
        <td width="35%">
             <a href="https://tissuumaps.research.it.uu.se/TMA-studies/#section-data"><img src="https://tissuumaps.research.it.uu.se/media/images/misc/TMA-studies/annotatedTMA.png" width="260px" alt="" />
                  <h5>Annotated cores in both slides
                </a></h5>
        </td> 
    </tr>    
</table>
