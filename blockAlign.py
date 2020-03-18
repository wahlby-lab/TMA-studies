"""
This code asumes there are 3 items:

1) A CSV containing the information per case-block,
including the name of the protein and the name of the DZI file. 

2)A JSON file with regions per protein in a block with 
information on which is the reference protein

3) the DZI pyramids on the block

"""

import sys
import os
import json
import numpy as np
import json
from skimage import io
from skimage import transform as tf
from scipy.linalg import orthogonal_procrustes
from matplotlib.path import Path
import pandas as pd
import re
import setupTransform #Alpha-AMD registration framework. To change parameters #like the number of iterations 
import WSILibs.processing as wsip
import WSILibs.wsiregions as wsir
import imagelibs.DZICalculator as DZI
import helperFunctions as hf #These are helper functions that don't change
import logging
import datetime


#Steps:
# 1) Do color separation and create the regions based on the info in the csv and json and dzis
# 2) register such regions and apply to regions and masks
# 3) put those regions together in a map

doStep1=True
doStep2=False
doStep3=False

#locations of images, csvs, dzis, jsons
csvlocation=    "/location/TMA_ECAD_only.csv"
jsonlocation=   "/location/"
pyramidlocation="/location/"
savelocation=   "/location/tosaveat/"
colorprofilelocation="/location/colorProfiles/" 
#work with n levels below the maximum meaning dividing by 2, n number of times
desiredlevel=1
#stains, in this case H and DAB
H=0; DAB=1
stainnames=["H","DAB"]
#need white balance?
whitebalance=True

#overwrite the images? 
overwrite=False
#print extra information
debug=True

#for the alignment
stretchContrast=True
#Some times when the images are very different in size, 
# it helps the registration to adjust for this difference
adjustForAreaDifference=False
#if WSI 500 if TMA 100
registrationiterations=300

now = datetime.datetime.now()
stringdate=now.strftime("%Y-%m-%d-%H-%M-%S")
logging.basicConfig(filename=savelocation+stringdate+'.log',level=logging.DEBUG) 
logging.info('Log for '+csvlocation)

# -------------------------------------------------------------------------------------------------------------------
# 1) Do color separation and create the regions based on the info in the csv and json and dzis
# -------------------------------------------------------------------------------------------------------------------

#Read CSV organize by code and then by block
df = pd.read_csv(csvlocation)
df.sort_values(by=['case', 'block'])

#get unique cases, unique blocks and for each protein do a job.
cases=df["case"].unique().tolist()
#blocks contains arrays of blocks per case
blocks=[]
for i in cases:
    bs=df.loc[df['case'] == i]["block"].unique().tolist()
    blocks.append(bs)

if doStep1:
    for c in range(len(cases)):
        print("Case "+str(cases[c])+" has blocks", blocks[c])
        bs=blocks[c]
        for b in bs:
            colorProjectors={}
            print("Taking block "+str(b))
            #now find all available proteins of the block
            iterate=df.loc[(df['case'] == cases[c]) & (df['block'] ==b)]
            proteins=iterate["protein"].unique().tolist()

            #bring the json to know which is the reference protein in this block
            jsonfile=jsonlocation+iterate.iloc[0]["jsonname"]
            regiondata=DZI.getJSONRegions(jsonfile)

            #for each protein check if there is a color profile
            for p in proteins:
                cp=hf.colorProjectorGen(colorprofilelocation,p,stainnames[H],stainnames[DAB])
                colorProjectors[p]=cp        
            for i,row in iterate.iterrows():
                acase=row["case"]; ablock=row["block"]
                aprotein=row["protein"]; adzi=row["filename"]                
                ajson=row["jsonname"]

                print("acase,ablock,aprotein,adzi,ajson")
                print(acase,ablock,aprotein,adzi,ajson)

                #now bring dzi and start creating regions!
                dzifile=pyramidlocation+adzi
                dzitileloc=dzifile.replace(".dzi","_files/")
                
                if(not os.path.isfile(dzifile)):
                    print("The file: "+dzifile+" does not exist")
                    continue
                
                w,h,ts=DZI.getWHTsfromDZI(dzifile)
                highreslevel=DZI.getMaximumLevel(w,h)
                cols,rows,ws,hs=DZI.computeLevels(w,h,ts)
                #but work with the desired level
                workinglevel=highreslevel-desiredlevel
                #remember to divide everything by 2^n
                twon=2**desiredlevel
                #effective width
                ew=ws[workinglevel]
                eh=hs[workinglevel]
                #we are going to create the region maker with the effective size
                regionmaker=wsir.WSIRegions(ew,eh,ts)
                regionmaker.dziImage=dzifile
                regionmaker.mainSavePath=savelocation
                regionmaker.jsonregions=jsonfile
                regionmaker.mainPath=dzitileloc+str(workinglevel)+os.sep
                basename=adzi.replace(".dzi","_files"+os.sep+ablock+os.sep)
                regionmaker.createRegionImages(aprotein,acase,ablock, regiondata, basename, colorProjectors[aprotein], twon,savestains=[2],overwrite=overwrite,whitebalance=whitebalance,debug=debug)
                            
    print("Region creation process finished")

# -------------------------------------------------------------------------------------------------------------------
# 2) register the regions created
# -------------------------------------------------------------------------------------------------------------------
if doStep2:
    #now all the image regions are created, find the transformations
    for c in range(len(cases)):
        print("Case "+str(cases[c])+" has blocks", blocks[c])
        bs=blocks[c]
        for b in bs:
            print("Taking block "+str(b))
            #now find all available proteins of the block
            iterate=df.loc[(df['case'] == cases[c]) & (df['block'] ==b)]
            proteins=iterate["protein"].unique().tolist()

            #bring the json to know which is the reference protein in this block
            jsonfile=jsonlocation+iterate.iloc[0]["jsonname"]
            regiondata=DZI.getJSONRegions(jsonfile)
            regions=regiondata["regions"]

            fixedp=None
            movingps=[]

            #for each protein check which is fixed and which are moving
            for p in proteins:
                if p in regions:
                    if regions[p]["property"]=="fixed":
                        fixedp=p
                    elif regions[p]["property"]=="moving":
                        movingps.append(p)
                    else:
                        print("protein "+p+" doesnt have a property (fixed or moving). Assigning to moving")
                else:
                    print("Protein "+p+" does not have regions in json")

            if fixedp is None:
                print("No fixed reference was found for case"+str(cases[c])+", block "+b)
                continue

            transformations={}

            #temp whitelist
            wl=[""]
            bl=[""]
            #loop thorugh regions which are common anyway
            for region in regiondata["regions"][fixedp].keys():
                if not region.startswith("region"):
                    continue

                if region not in wl:
                    continue

                if region in bl:
                    continue

                #Do the region and mask for the fixed ONCE without adding T because there is no T -----------------------------

                info=df.loc[(df['case'] == cases[c]) & (df['block'] ==b) & (df['protein'] ==fixedp)]
                adzi=info["filename"].values[0]
                basename=adzi.replace(".dzi",os.sep+b+os.sep)
                #find the fixed protein's H
                fixedPs1=savelocation+basename+region+"_"+stainnames[H]+".png"
                if(not os.path.isfile(fixedPs1)):
                    print("No region "+fixedPs1)
                
                masknamefixed=savelocation+basename+fixedp+region+"_mask.png"

                # <End of fixed p region and mask>---------------------------------------------------------------------------

                for movp in movingps:
                    info=df.loc[(df['case'] == cases[c]) & (df['block'] ==b) & (df['protein'] ==movp)]
                    adzi=info["filename"].values[0]
                    basename=adzi.replace(".dzi",os.sep+b+os.sep)
                    movingPs1= savelocation+basename+region+"_"+stainnames[H]+".png"
                    if(not os.path.isfile(movingPs1)):
                        print("No "+movingPs1)
                        continue

                    #find transformation between f and m
                    T=None

                    movingPs2= savelocation+basename+region+"_"+stainnames[DAB]+".png"
                    saveMPs2T=savelocation+basename+movp+region+"_"+stainnames[DAB]+"_T.png"
                    saveMPs1T=savelocation+basename+movp+region+"_"+stainnames[H]+"_T.png"

                    masknamemovT=savelocation+basename+movp+region+"_mask_T.png"
                    masknamemov=savelocation+basename+movp+region+"_mask.png"

                    #if trasnformations exist for this, don't run transform.
                    if(os.path.isfile(saveMPs2T) and os.path.isfile(saveMPs1T) and os.path.isfile(masknamemovT)):
                        print('T exists for: '+str(cases[c])+' '+str(b)+' '+movp+' '+region)
                        logging.info('T exists for: '+str(cases[c])+' '+str(b)+' '+movp+' '+region)
                        continue

                    #For us the best parameters for TMA where these 
                    transformer=setupTransform.setupTransform(fixedPs1,movingPs1,[32,16,8,4],[15.0,8.0,4.0,2.0],savelocation, \
                        adjustForAreaDifference,stretchContrast,False,screen=movingPs2)
                    transformer.param_iterations = registrationiterations
                    #If you have masks for your images:
                    #transformer.maskRef=None#masknamefixed
                    #transformer.maskFlo=None#savelocation+basename+movp+region+"_mask.png"
                    transformer.param_report_freq=registrationiterations
                    T=transformer.doRegistration()

                    if T is None:
                        print("Error in do registration for region "+region+", protein "+movp)

                    logging.info('Transformation: '+str(cases[c])+' '+str(b)+' '+movp+' '+region+':'+repr(T.get_params()))
                        
                    transformer.applyTnSave(T,fixedPs1,movingPs2,saveMPs2T)
                    transformer.applyTnSave(T,fixedPs1,movingPs1,saveMPs1T)

                    #WE NEED MASKS AND OR THE TRANSFORM ------------------------------------------------------------
                    
                    transformer.applyTnSave(T,fixedPs1,masknamemov,masknamemovT)

                # And also do it for fixed P whose transformation is not need because it 
                # is the identity (1) so simply bring the regions and make masks

                print("finished all alignments for region "+region)

    print("Region alignment process finished")

# -------------------------------------------------------------------------------------------------------------------
# 3) put those regions together in a map
# -------------------------------------------------------------------------------------------------------------------
if doStep3:
    # load regions from json, create a stage for all the regions, of size maxlevel-desiredlevel, 
    # load the regions and put them in the right place, by taking the coordinates 
    # of the fixed (reference) as an initial point

    #in this case we have to do a map per protein
    for c in range(len(cases)):
        print("Case "+str(cases[c])+" has blocks", blocks[c])
        bs=blocks[c]
        for b in bs:
            print("Taking block "+str(b))
            #now find all available proteins of the block
            iterate=df.loc[(df['case'] == cases[c]) & (df['block'] ==b)]
            proteins=iterate["protein"].unique().tolist()

            #bring the json to know which is the reference protein in this block
            jsonfile=jsonlocation+iterate["jsonname"].unique().tolist()[0]
            regiondata=DZI.getJSONRegions(jsonfile)
            regions=regiondata["regions"]

            fixedp=None
            movingps=[]

            for p in proteins:
                if p in regions:
                    if regions[p]["property"]=="fixed":
                        fixedp=p
                    elif regions[p]["property"]=="moving":
                        movingps.append(p)
                    else:
                        print("protein "+p+" doesnt have a property (fixed or moving). Assigning to moving")
                else:
                    print("Protein "+p+" does not have regions in json")

            if fixedp is None:
                print("No fixed reference was found for case"+str(cases[c])+", block "+b)
                continue

            fixedpinfo=iterate.loc[(iterate["protein"]==fixedp)]
            fixeddzilocalpath=fixedpinfo["filename"].unique().tolist()[0]
            fixeddzifile=pyramidlocation+fixeddzilocalpath

            w,h,ts=DZI.getWHTsfromDZI(fixeddzifile)
            highreslevel=DZI.getMaximumLevel(w,h)
            cols,rows,ws,hs=DZI.computeLevels(w,h,ts)
            #but work with the desired level
            workinglevel=highreslevel-desiredlevel
            #remember to divide everything by 2^n
            twon=2**desiredlevel
            #effective width
            few=ws[workinglevel] #size for stage
            feh=hs[workinglevel] #size for stage

            #do this for the FIXED first 
            # Do it once for the fixed P which eventhough there are no transformations it still 
            # needs to be masked with the selected regions
            basename=fixeddzilocalpath.replace(".dzi",os.sep+b+os.sep)
            mapname=savelocation+str(cases[c])+"_"+str(b)+"_"+fixedp+"_map_"+stainnames[H]+".png"
                
            if(not os.path.isfile(mapname)):
                 #create new stage for this protein:
                stageforfixed=np.zeros((feh,few),dtype="uint8")

                #regions data exists in local variable "regions" 
                fixedpregions=regions[fixedp].keys()

                #for every region key in the regions.
                for regk in fixedpregions:
                    if not regk.startswith("region"):
                        continue

                    #location in fixed:
                    fstartx=int(regions[fixedp][regk]["_gxmin"])//twon
                    fstarty=int(regions[fixedp][regk]["_gymin"])//twon

                    #load fixedp H and its mask and put in stage. THIS ONES DO NOT HAVE TRANSFORMATION
                    FPs1T=savelocation+basename+regk+"_"+stainnames[H]+".png"
                    masknamef=savelocation+basename+fixedp+regk+"_mask.png"

                    fixed_H=io.imread(FPs1T)
                    maskf=io.imread(masknamef)

                    my, mx = np.where(maskf)
                    myr=my+fstarty
                    mxr=mx+fstartx
                    #mymax=np.amax(my); mxmax=np.amax(mx)

                    myr=np.clip(myr,a_min=0,a_max=feh-1)
                    mxr=np.clip(mxr,a_min=0,a_max=few-1)

                    stageforfixed[myr,mxr]=fixed_H[my,mx]

                print("Saving map of "+fixedp +stainnames[H]+" at "+mapname)
                logging.info("Saving map of "+movp +stainnames[H]+" at "+mapname)
                io.imsave(mapname,stageforfixed)
            else:
                print("Map for H for "+fixedp+" exists at "+mapname)

            
            #AND AGAIN FOR DAB

             #do this for the FIXED first 
            # Do it once for the fixed P which eventhough there are no transformations it still 
            # needs to be masked with the selected regions
            basename=fixeddzilocalpath.replace(".dzi",os.sep+b+os.sep)
            mapname=savelocation+str(cases[c])+"_"+str(b)+"_"+fixedp+"_map_"+stainnames[DAB]+".png"
                
            if(not os.path.isfile(mapname)):
                 #create new stage for this protein:
                stageforfixed=np.zeros((feh,few),dtype="uint8")

                #regions data exists in local variable "regions" 
                fixedpregions=regions[fixedp].keys()

                #for every region key in the regions.
                for regk in fixedpregions:
                    if not regk.startswith("region"):
                        continue

                    #location in fixed:
                    fstartx=int(regions[fixedp][regk]["_gxmin"])//twon
                    fstarty=int(regions[fixedp][regk]["_gymin"])//twon

                    #load fixedp H and its mask and put in stage. THIS ONES DO NOT HAVE TRANSFORMATION
                    FPs2T=savelocation+basename+regk+"_"+stainnames[DAB]+".png"
                    masknamef=savelocation+basename+fixedp+regk+"_mask.png"

                    fixed_H=io.imread(FPs2T)
                    maskf=io.imread(masknamef)

                    my, mx = np.where(maskf)
                    myr=my+fstarty
                    mxr=mx+fstartx

                    #mymax=np.amax(my); mxmax=np.amax(mx)

                    myr=np.clip(myr,a_min=0,a_max=feh-1)
                    mxr=np.clip(mxr,a_min=0,a_max=few-1)

                    stageforfixed[myr,mxr]=fixed_H[my,mx]

                print("Saving map of "+fixedp +stainnames[DAB]+" at "+mapname)
                logging.info("Saving map of "+movp +stainnames[DAB]+" at "+mapname)
                io.imsave(mapname,stageforfixed)
            else:
                print("Map for DAB for "+fixedp+" exists at "+mapname)

            # END OF FIXED STEP------------------------------------


            #do all this for the H maps, and then again for the DABs to save memory 
            for movp in movingps:
                mapname=savelocation+str(cases[c])+"_"+str(b)+"_"+movp+"_map_"+stainnames[H]+"_T.png"
                
                if(os.path.isfile(mapname)):
                    print("H map exists for "+movp)
                    continue
                #go thorugh all regions load their masks and put them in the map
                
                #create new stage for this protein:
                stageformovp=np.zeros((feh,few),dtype="uint8")

                #regions data exists in local variable "regions" 
                movpregions=regions[movp].keys()

                #for every region key in the regions.
                for regk in movpregions:
                    if not regk.startswith("region"):
                        continue
                    # bring region T, bring its mask and bring the same region 
                    # in fixed p to know where it starts in stage

                    #dzi infor for movp
                    movpinfo=iterate.loc[(iterate["protein"]==movp)]
                    movdzipath=movpinfo["filename"].unique().tolist()[0]
                    movdzifile=pyramidlocation+movdzipath

                    #location in fixed:
                    fstartx=int(regions[fixedp][regk]["_gxmin"])//twon
                    fstarty=int(regions[fixedp][regk]["_gymin"])//twon

                    basename=movdzipath.replace(".dzi",os.sep+b+os.sep)

                    #load movp H_T and its mask_T and put in stage
                    MPs1T=savelocation+basename+movp+regk+"_"+stainnames[H]+"_T.png"
                    masknameT=savelocation+basename+movp+regk+"_mask_T.png"

                    movp_H_T=io.imread(MPs1T)
                    mask_T=io.imread(masknameT)

                    my, mx = np.where(mask_T)
                    myr=my+fstarty
                    mxr=mx+fstartx

                    #mymax=np.amax(my); mxmax=np.amax(mx)

                    myr=np.clip(myr,a_min=0,a_max=feh-1)
                    mxr=np.clip(mxr,a_min=0,a_max=few-1)

                    stageformovp[myr,mxr]=movp_H_T[my,mx]

                print("Saving map of "+movp +stainnames[H]+" at "+mapname)
                logging.info("Saving map of "+movp +stainnames[H]+" at "+mapname)
                io.imsave(mapname,stageformovp)

            #Now for DAB maps
            for movp in movingps:
                mapname=savelocation+str(cases[c])+"_"+str(b)+"_"+movp+"_map_"+stainnames[DAB]+"_T.png"
                if(os.path.isfile(mapname)):
                    print("DAB map exists for "+movp)
                    continue
                #go thorugh all regions load their masks and put them in the map
                
                #create new stage for this protein:
                stageformovp=np.zeros((feh,few),dtype="uint8")

                #regions data exists in local variable "regions" 
                movpregions=regions[movp].keys()

                #for every region key in the regions.
                for regk in movpregions:
                    if not regk.startswith("region"):
                        continue
                    # bring region T, bring its mask and bring the same region 
                    # in fixed p to know where it starts in stage

                    #dzi infor for movp
                    movpinfo=iterate.loc[(iterate["protein"]==movp)]
                    movdzipath=movpinfo["filename"].unique().tolist()[0]
                    movdzifile=pyramidlocation+movdzipath

                    #location in fixed:
                    fstartx=int(regions[fixedp][regk]["_gxmin"])//twon
                    fstarty=int(regions[fixedp][regk]["_gymin"])//twon

                    basename=movdzipath.replace(".dzi",os.sep+b+os.sep)

                    #load movp H_T and its mask_T and put in stage
                    MPs2T=savelocation+basename+movp+regk+"_"+stainnames[DAB]+"_T.png"
                    masknameT=savelocation+basename+movp+regk+"_mask_T.png"

                    movp_DAB_T=io.imread(MPs2T)
                    mask_T=io.imread(masknameT)

                    my, mx = np.where(mask_T)
                    myr=my+fstarty
                    mxr=mx+fstartx

                    #mymax=np.amax(my); mxmax=np.amax(mx)

                    myr=np.clip(myr,a_min=0,a_max=feh-1)
                    mxr=np.clip(mxr,a_min=0,a_max=few-1)

                    stageformovp[myr,mxr]=movp_DAB_T[my,mx]

                print("Saving map of "+movp +stainnames[H]+" at "+mapname)
                logging.info("Saving map of "+movp +stainnames[H]+" at "+mapname)
                io.imsave(mapname,stageformovp)
