TMA-studies
===========

This is the viewer we created to annotate several TMA slides simultaneously

![Using TissUUmaps](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/TissUUmaps.gif)

This is the format of the regions
![JSON and CSV formats](https://github.com/wahlby-lab/TMA-studies/blob/master/misc/JSON-CSV-example.jpg)

The CSV has to have the columns: protein,block,format,case,prefix,filename,jsonname
The JSON should contain all the regions (cores) per protein (can be more than 2 proteins) and each protein contains the property of "moving" or "fixed" which tells which is the reference protein slide that guides the registrtion.

Each region contains the spatial information of a core, such as points in pixels, points in global coordinates, bounding boxes, an associated protein and a length. A color can be used in TissUUmaps to find the different cores visually.
