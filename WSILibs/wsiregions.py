#

import numpy as np
import itertools
from skimage import io 
import os
from matplotlib.path import Path

def rasterizeMask(points,shape,debug=False):
    """This function takes polygon points whose minimum is 0,0, 
    possibly scaled and rasterizes a mask inside the polygon, and 
    the shape tuple for the image"""

    width=shape[1]
    height=shape[0]


    xmin = np.min(points[:,0]); xmax = np.max(points[:,0])
    ymin = np.min(points[:,1]); ymax = np.max(points[:,1])

    
    width=shape[1]
    height=shape[0]
        
    if(debug):
        print ("region height width")
        print(height,width)
        
    pointsinpolygon=[]

    for i in range(points.shape[0]):
        yy=np.clip(points[i,1],a_min=0,a_max=height)
        xx=np.clip(points[i,0],a_min=0,a_max=width)
        pointsinpolygon.append((yy-ymin,xx-xmin))
        
    if(debug):
        print ("pointsinpolygon")
        print(pointsinpolygon)
    
    poly_path=Path(pointsinpolygon)
    if(debug):
        print ("poly_path created")
    x, y = np.mgrid[:height, :width]
    if(debug):
        print ("mgrid created")
    coors=np.hstack((x.reshape(-1, 1), y.reshape(-1,1)))
    
    if(debug):
        print ("coors created")
    mask = poly_path.contains_points(coors)
    if(debug):
        print ("mask created")
    mask=mask.reshape(height,width)
    if(debug):
        print ("mask properties")
        print(mask.shape)

    mask=mask.astype("uint8")*255
    return mask


def standardizeRegion(jsonpoints,scale):
    bounds=[]
    minx=int(jsonpoints[0]["x"])
    miny=int(jsonpoints[0]["y"])
    for gp in jsonpoints:
        x=int(gp["x"])//scale
        y=int(gp["y"])//scale
        if(y<miny):
            miny=y

        if(x<minx):
            minx=x
        bounds.append([x,y,1])

    boundscorrected=[]
    for p in bounds:
        boundscorrected.append([p[0]-minx,p[1]-miny,1])

    
    boundscorrected=np.array(boundscorrected)
    return boundscorrected


class WSIRegions:
    
    def __init__(self,w,h,ts):
        self.imageWidth =int(w)
        self.imageHeight=int(h)
        self.tileSize=int(ts)
        self.dziImage=""
        #For loading images, it is better to have a main path
        #But doesnt have to be set in the constructor 
        self.mainPath=""
        #when saving images save here:
        self.mainSavePath=""
        self.prefix=""
        self.suffix=""
        self.imformat=".png"
        self.pathtoregions=""
        self.jsonregions=""
        #some typical stains, could be anything
        self.stainnames=["H","DAB","RGB","mask"]
        #which of these is color
        self.colorindex=2
        self.maskindex=3

        
    def findRegionTileLimits(self,xmin, xmax, ymin, ymax):
        """Given image and region dimensions, find the information
        needed to select the appropriate tiles"""
        if( (self.imageWidth is None) or \
            (self.imageHeight is None) or \
            (self.tileSize is None) ):
            raise ValueError('You need to set the image space')

        startx=int(xmin%self.tileSize)
        endx=int(xmax%self.tileSize)
        starty=int(ymin%self.tileSize)
        endy=int(ymax%self.tileSize)
        tilestartx=int(xmin//self.tileSize)
        tileendx=int(xmax//self.tileSize)
        tilestarty=int(ymin//self.tileSize)
        tileendy=int(ymax//self.tileSize)

        return startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy

    def clipAndInform(self,val,clip,message=""):
        if(val > clip):
            print(message)
        val=np.clip(val,0,clip)
        return val

    def createRegionFromTiles(self ,regiondata,effectivesize, colorProjector, stain,dtype="uint8",colorexists=None,overwrite=False, whitebalance=False,debug=False):
        """This function takes the global bounding box of a desired region and 
        load the necessary tiles to complete it and then mask it and save it.
        It is better that loading a whole image
        It assumes a vips tiling which ends in _files
        This method will also run the deconvolution before returning the file
        """
        location=self.mainPath
        #check if those globals are outside the image size 
        #and if so, clip them but let me know
        message="WARNING: value for a region limit was bigger than the image size, clipping."
        xmin=int(regiondata["_gxmin"])//effectivesize; xmax=int(regiondata["_gxmax"])//effectivesize 
        ymin=int(regiondata["_gymin"])//effectivesize; ymax=int(regiondata["_gymax"])//effectivesize
        xmin=self.clipAndInform(xmin,self.imageWidth-1,message)
        xmax=self.clipAndInform(xmax,self.imageWidth-1,message)
        ymin=self.clipAndInform(ymin,self.imageHeight-1,message)
        ymax=self.clipAndInform(ymax,self.imageHeight-1,message)        
        
        regionimage=None

        if(debug):
            print(location)
            
        startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy =\
            self.findRegionTileLimits(xmin, xmax, ymin, ymax) 
        tilesinx=tileendx-tilestartx+1
        tilesiny=tileendy-tilestarty+1

        if(debug):
            print("startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy")
            print(startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy)
            print(tilesinx,tilesiny)


        #if black only, just call the black_like
        if(stain==-1):
            regionimage=self.black_like(startx, endx, starty, endy, tilestartx, tileendx, tilestarty, \
                tileendy, tilesinx,tilesiny, dtype=dtype, debug=debug)

        #if greyscale, separate into stains
        if(stain !=self.colorindex and stain !=self.maskindex):
            regionimage=self.greyFromStainRegion(startx, endx, starty, endy, tilestartx, tileendx, \
                tilestarty, tileendy, tilesinx,tilesiny, colorProjector,  stain,colorexists=colorexists,\
                dtype=dtype,overwrite=overwrite, whitebalance=whitebalance, debug=debug)
        #if color, no need to separate
        if (stain==self.colorindex):
            regionimage=self.RGBRegion(startx, endx, starty, endy, tilestartx, tileendx, tilestarty,\
                tileendy, tilesinx,tilesiny,colorProjector,overwrite=overwrite, whitebalance=whitebalance, debug=debug)

        if (stain==self.maskindex):
            regionimage=self.createRegionMask(regiondata,effectivesize)

        return regionimage

    def RGBRegion(self, startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy,tilesinx,tilesiny, colorProjector, overwrite=False, whitebalance=True, debug=False):
        # make an image of the correct size to receive all the tiles
        stage=np.zeros((tilesiny*self.tileSize,tilesinx*self.tileSize,3),dtype="uint8")

        if(debug):
            print(stage.shape)
            
        for i, j in itertools.product(range(tilestartx,tileendx+1), range(tilestarty,tileendy+1)):
            ist=(i-tilestartx)*self.tileSize
            jst=(j-tilestarty)*self.tileSize
            name=str(i)+"_"+str(j)+self.imformat
            tile=None
            #file=dirname+name
            fullpath=self.mainPath+name
            try:
                tile=io.imread(fullpath)
                if (whitebalance and (colorProjector is not None)):
                    tile=colorProjector.whiteBalance(tile)
            except IOError:
                print("Tile "+fullpath+" doesn't exist. Did you go out of bounds? is it the right region?")
                return None

            if(tile is not None):
                sh=tile.shape
                if(len(sh)>2):
                    if(sh[2]==3):
                        stage[ jst:jst+sh[0], ist:ist+sh[1],:]=tile
                    else:
                        stage[ jst:jst+sh[0], ist:ist+sh[1],:]=tile[:,:,:3]
                else:
                    print("Tile "+str(i)+" "+ str(j)+" is not RGB") 
                    return None
        
        regionimage=stage[starty:tilesiny*self.tileSize-self.tileSize+endy,startx:tilesinx*self.tileSize-self.tileSize+endx,:]
        
        return regionimage

    def greyFromStainRegion(self ,startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy,tilesinx,tilesiny, colorProjector, stain,dtype="uint8",overwrite=False, colorexists=None, whitebalance=False,debug=False):
        # make an image of the correct size to receive all the tiles
        if((colorexists != None) and (stain != self.colorindex)):
            if(os.path.isfile(colorexists)):
                #if color exists dont create it again
                rgbimg=io.imread(colorexists)
                stainimg=colorProjector.separateStains(rgbimg,stain=stain)
                return stainimg
            else:
                print("colorexists is not None but the image doesnt exist, attemting to create stain image from tiles")


        stage=np.zeros((tilesiny*self.tileSize,tilesinx*self.tileSize),dtype=dtype)

        if(debug):
            print(stage.shape)
            
        for i, j in itertools.product(range(tilestartx,tileendx+1), range(tilestarty,tileendy+1)):
            ist=(i-tilestartx)*self.tileSize
            jst=(j-tilestarty)*self.tileSize
            name=str(i)+"_"+str(j)+self.imformat
            tile=None
            #file=dirname+name
            fullpath=self.mainPath+name
            try:
                tile=io.imread(fullpath)
                if (whitebalance and colorProjector):
                    tile=colorProjector.whiteBalance(tile)
            except IOError:
                print("Tile "+fullpath+" doesn't exist. Did you go out of bounds? is it the right region?")
                return None

            staintile=None
            if(colorProjector):
                staintile=colorProjector.separateStains(tile,stain=stain)
            else:
                #try to bring the image if it is on channel only
                if(len(tile.shape)<=2):
                    staintile=tile
                else:
                    print("Tile  "+fullpath+"  is not single channel, returning none, or falling back to black")

            if(debug):
                print("adding tile "+fullpath)

            sh=staintile.shape
            stage[ jst:jst+sh[0], ist:ist+sh[1] ]=staintile
        
        regionimage=stage[starty:tilesiny*self.tileSize-self.tileSize+endy,startx:tilesinx*self.tileSize-self.tileSize+endx]
        
        return regionimage
    
    def black_like(self ,startx, endx, starty, endy, tilestartx, tileendx, tilestarty, tileendy,tilesinx,tilesiny,dtype="uint8", debug=False):
        """Create a black image the size of the region in the desired resolution """
        size=( (tilesiny-1)*self.tileSize+endy-starty,(tilesinx-1)*self.tileSize+endx-startx)
        stage=np.zeros(size,dtype=dtype)
        return stage

    def createRegionImages(self, protein, case,block, data, dirname, colorProjector, effectivesize ,savestains=[0,1,2,3],savenames=["H","DAB","RGB","mask"],overwrite=False,whitebalance=False,debug=False):
        #let's do this in a smart way because creating images takes time specially in hi res
        #first we check if we have to create color, if we selected not to create them, check if they exist
        #if they dont exit and we still need the stains then we have still to create the colored one

        #the two "viewers" have more information than the regions, so look for a keyword, in this case "region"
        for region in data["regions"][protein].keys():
            #images of tissue
            if not region.startswith("region"):
                continue
            print(region)
            d=data["regions"][protein][region]

            #check for color so there is no need to create it even if it is not to be saved again
            #save dab
            for stain in savestains:
                #basename=dirname.replace("_files","")
                savelocation=self.mainSavePath+savenames[stain]+os.sep+protein+"_"+str(case)+"_"+block+"_"+savenames[stain]+"_"+region+".png"
                #masknamef=self.mainSavePath+protein+"_"+str(case)+"_"+block+"_mask_"+region+".png"
                colorexists=self.mainSavePath+savenames[self.colorindex]+os.sep+protein+"_"+str(case)+"_"+block+"_"+savenames[self.colorindex]+"_"+region+".png"
                if(not overwrite):
                    if(os.path.isfile(savelocation)):
                        print("Already exists, don't overwrite "+savelocation)
                        continue 
                #modify regions by dividing by the effective desired size
                
                regionimage=self.createRegionFromTiles(d,effectivesize,colorProjector, stain,colorexists=colorexists,overwrite=overwrite, whitebalance=whitebalance,debug=debug)
                 
                if regionimage is not None:                  
                    folder=self.mainSavePath+savenames[stain]
                    if(not os.path.isdir(folder)):
                        print("creating ",folder)
                        os.makedirs(folder) 

                    print("save "+savelocation)                  
                    io.imsave(savelocation,regionimage)

            #if it arrives till here it means the folder exist, dont check again
    
    def createRegionMask(self, regiondata,effectivesize):
        
        #def rasterizeMask(points,shape,debug=False):
        xmin=int(regiondata["_gxmin"])//effectivesize; xmax=int(regiondata["_gxmax"])//effectivesize 
        ymin=int(regiondata["_gymin"])//effectivesize; ymax=int(regiondata["_gymax"])//effectivesize
        polygon=regiondata["globalPoints"]
        #print("Mask does not exist")
        shape=(ymax-ymin,xmax-xmin)
        rd=standardizeRegion(polygon,effectivesize)
        mask=rasterizeMask(rd,shape)
        #io.imsave(masknamef,mask)  
        #print("Saving mask for protein "+protein+region)
        return mask
