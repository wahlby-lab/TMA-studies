import math
import xml.etree.ElementTree as ET
import os
import json

#all based on this blog
#https www.gasi.ch blog inside-deep-zoom-1

def getMaximumLevel(w,h):
    return int(math.ceil(math.log(max(w,h),2)))

def computeLevels(w,h,tilesize,debug=False):
    widths=[]
    heights=[]
    columns=[]
    rows=[]
    maxlevel=getMaximumLevel(w,h)
    for i in range(int(maxlevel),-1,-1):
        c = math.ceil( w / tilesize )
        r = math.ceil( h / tilesize )
        columns.insert(0,int(c))
        rows.insert(0,int(r))
        widths.insert(0,int(w))
        heights.insert(0,int(h))
        if(debug):
            print ("level "+ str(i)+ " is "+str(w)+" x "+str(h)+ " ("+str(c)+" columns, "+str(r)+" rows)")
        w  = math.ceil( w / 2 )
        h = math.ceil( h / 2 )
    return (columns,rows,widths,heights)
        
def getTilePosition(col,row,tilesize=1024,overlap=1):
    #I decided to make overlap default to 1 since it is the most common
    #tileSize: Dimensions of tile, e.g Image TileSize=256
    #tileOverlap: Overlap in pixels, e.g. Image  Overlap="1"/
    offsetX = 0 if col==0 else overlap
    offsetY = 0 if row==0 else overlap

    return ((col * tilesize) - offsetX , ( row * tilesize ) - offsetY )

def getWHTsfromDZI(dzifile):
    if(not os.path.isfile(dzifile)):
        print("DZI does not exist")
        #except IOError
    tree = ET.parse(dzifile)
    root = tree.getroot()
    width=None
    height=None
    tileSize=None
    for child in root.iter():
        if any(size in child.tag for size in ["Size","size","SIZE"]):
            width=child.attrib["Width"]
            height=child.attrib["Height"]

    for a in ["TileSize","tileSize","TILESIZE","tilesize"]:
        if a in root.attrib:
            tileSize=root.attrib[a]
    
    width=int(width)
    height=int(height)
    tileSize=int(tileSize)
    
    return width, height, tileSize

    
def getJSONRegions(jsonfile):
    if os.path.isfile(jsonfile):
        with open(str(jsonfile)) as data_file:  
            print("Reading "+str(jsonfile))
            data = json.load(data_file)
            return data
    else: 
        print(jsonfile + " does not exist.")
        
