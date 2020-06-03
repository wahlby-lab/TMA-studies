from skimage import io, morphology, filters, img_as_float, exposure
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import imagelibs.coloquantfunctions as tmaq
import skimage.filters as sf
import skimage.exposure as se

def trans(z, param_threshold, param_transition, param_power):
    z_rel = (z - param_threshold) / (param_transition+1e-7)
    z_rel_abs = np.abs(z_rel)
    z_rel_sgn = np.sign(z_rel)

    return smoothystep(param_power, 0.5*np.clip(1.0+z_rel_sgn*z_rel_abs, a_min=0.0, a_max=2.0))

def smoothystep(po, x):
    z = np.zeros(x.shape)
    fac = 2.0*np.power(0.5, po)
    x_left = x <= 0.5
    x_right = x > 0.5
    y_left = np.power(x[x_left], po)/fac
    z[x <= 0.5] = y_left
    y_right = 1.0-np.power(1.0-x[x_right], po)/fac
    z[x_right] = y_right
    return z

#what will go into the list in pandas
dataframe=pd.DataFrame(columns=['block','core','CD44v6pwT','CD44v6pwIH-wIDAB-woT','CD44v6pwIH-wIDAB-wT'])
mainloc="/home/leslie/Documents/TMACOEXP/"
saveexperimentsat="/home/leslie/Documents/TMACOEXP/experiments/"
saveimat="/home/leslie/Documents/TMACOEXP/temporal/"

TMAQ=tmaq.TMAQuantifier()
TMAQ.proteins=["CD44v6", "Ecad"] #the first is the important space
TMAQ.stains=["H","DAB","mask","tumor","RGB"]
TMAQ.morphology=0 #morphology shown by H
TMAQ.expression=1 #protein expression by DAB
TMAQ.mask=2; TMAQ.tumor=3; TMAQ.RGB=4

doRoberts=True
saveimgs=True

pandascsv="/home/leslie/Documents/TMACOEXP/cores_slide2.csv"

df=pd.read_csv(pandascsv)

for idx, row in df.iterrows():
    c=str(row["TMA_Slide"])
    core=row["Regions"]
    TMAQ.case=str(c)
    TMAQ.corename=core

    TMAQ.imagelocations[("CD44v6", "H")  ]=mainloc+TMAQ.stains[TMAQ.morphology]+os.sep+"CD44v6_"+c+"_B_"+TMAQ.stains[TMAQ.morphology]+"_"+core+".png"
    if(not os.path.isfile(TMAQ.imagelocations[("CD44v6", "H")])):
        print("H does not exist for "+c+"_"+core)
        continue

    TMAQ.imagelocations[("CD44v6", "mask") ]=mainloc+os.sep+TMAQ.stains[TMAQ.mask]+os.sep+"CD44v6_"+c+"_B_"+TMAQ.stains[TMAQ.mask]+"_"+core+".png"
    TMAQ.imagelocations[("CD44v6", "DAB")  ]=mainloc+os.sep+TMAQ.stains[TMAQ.expression]+os.sep+"CD44v6_"+c+"_B_"+TMAQ.stains[TMAQ.expression]+"_"+core+".png"
    TMAQ.imagelocations[("CD44v6", "tumor")  ]=mainloc+os.sep+TMAQ.stains[TMAQ.tumor]+"/CD44v6_"+c+"_B_RGB_"+core+"-SimpleSegmentation.png"
  
    TMAQ.imagelocations[("Ecad"  , "DAB")  ]=mainloc+os.sep+TMAQ.stains[TMAQ.expression]+os.sep+"Ecad_"+c+"_B_"+TMAQ.stains[TMAQ.expression]+"_"+core+"_T.png"
    TMAQ.imagelocations[("Ecad"  , "H")  ]=mainloc+os.sep+TMAQ.stains[TMAQ.morphology]+os.sep+"Ecad_"+c+"_B_"+TMAQ.stains[TMAQ.morphology]+"_"+core+"_T.png"
    
    if(TMAQ.checkExistance()):
        continue

    tumor=TMAQ.getStainFromProtein("CD44v6","tumor",value_at=85,as_bool=True)

    CD44v6DAB=TMAQ.getStainFromProtein("CD44v6","DAB",load_as_float=True)
    EcadDAB=TMAQ.getStainFromProtein("Ecad","DAB",load_as_float=True)
    mask=TMAQ.getStainFromProtein("CD44v6","mask",as_bool=True)

    tumor*=mask   

    #DO RCM
    CD44v6H=img_as_float(io.imread(TMAQ.imagelocations[("CD44v6", "H")]))
    EcadH=img_as_float(io.imread(TMAQ.imagelocations[("Ecad", "H")]))
    CD44v6H=np.clip(CD44v6H,0.06,1.0)
    EcadH=np.clip(EcadH,0.06,1.0)
    CD44v6H=se.adjust_gamma(CD44v6H,0.5)
    EcadH=se.adjust_gamma(EcadH,0.5)
    CD44v6thr=sf.threshold_triangle(CD44v6H)
    Ecadthr=sf.threshold_triangle(EcadH)

    RCM=np.zeros_like(CD44v6H)
    RCM[EcadH[:,:]>Ecadthr]+=2
    RCM[CD44v6H[:,:]>CD44v6thr]+=1
    RCM[RCM<3]*=0
    RCM=RCM.astype("bool")
    RCM=morphology.binary_dilation(RCM)
    RCM=morphology.binary_erosion(RCM)

    if(saveimgs):            
        RCMint=RCM.astype("uint8")*255
        io.imsave(saveimat+"RCM_"+c+"_"+core+".png",RCMint)

    RCMxSegTum=RCM*tumor

    if(saveimgs):            
        RCMTumorint=RCMxSegTum.astype("uint8")*255
        io.imsave(saveimat+"RCMxTUMOR_"+c+"_"+core+".png",RCMTumorint)

    #Load DABS to quantify individual and in CQM
    CD44v6DAB=img_as_float(io.imread(TMAQ.imagelocations[("CD44v6", "DAB")]))
    EcadDAB=img_as_float(io.imread(TMAQ.imagelocations[("Ecad", "DAB")]))
    
    #CD44v6 quantification
    quanthere=CD44v6DAB

    if(doRoberts):
        roberts=sf.roberts(CD44v6DAB)
        quanthere=                np.greater(CD44v6DAB, 0.5)  * np.minimum( 1.0-(1.0-2.0*(CD44v6DAB-0.5))*(1.0-roberts) , 1.0) 
        quanthere+=np.logical_not(np.greater(CD44v6DAB, 0.5)) * np.minimum( roberts * (CD44v6DAB * 2.0), 1.0 )
        if(saveimgs):            
            robertsint=roberts*255.0
            robertsint=robertsint.astype("uint8")
            io.imsave(saveimat+"CD44v6_Roberts_"+c+"_"+core+".png",robertsint)

    #quanthere=trans(quanthere,0.2, 0.15, 1.0)
    quanthere=quanthere>=.03

    quanthereorig=quanthere*tumor
    
    p1q=np.sum(quanthereorig)

    df.loc[idx,"p1"]=p1q

    # Ecad quantification    
    quanthere2=EcadDAB
    
    if(doRoberts):
        roberts2=sf.roberts(EcadDAB)
        quanthere2=                np.greater(EcadDAB, 0.5)  * np.minimum( 1.0-(1.0-2.0*(EcadDAB-0.5))*(1.0-roberts2) , 1.0) 
        quanthere2+=np.logical_not(np.greater(EcadDAB, 0.5)) * np.minimum( roberts2 * (EcadDAB * 2.0), 1.0 )
        if(saveimgs):            
            robertsint=roberts2*255.0
            robertsint=robertsint.astype("uint8")
            io.imsave(saveimat+"Ecad_Roberts_"+c+"_"+core+".png",robertsint)

    #quanthere2=trans(quanthere2,0.2, 0.15, 1.0)

    quanthere2=quanthere2>=.03
    
    quanthereEorig=quanthere2*tumor
    
    p2q=np.sum(quanthereEorig)

    df.loc[idx,"p2"]=p2q
    sumtumorig=np.sum(tumor)

    df.loc[idx,"tumor"]=sumtumorig
    df.loc[idx,"p1q"]=100.0*(p1q/sumtumorig)

    df.loc[idx,"p2q"]=100.0*(p2q/sumtumorig)

    quanthere=0
    quanthere2=0
    quanthereEorig=0
    quanthereorig=0


    #CQM continuation
    CD44v6DAB=np.clip(CD44v6DAB,0.06,1.0)
    EcadDAB=np.clip(EcadDAB,0.06,1.0)
    CD44v6DAB=se.adjust_gamma(CD44v6DAB,0.5)
    EcadDAB=se.adjust_gamma(EcadDAB,0.5)
    amountoftumor0=np.prod(np.where(RCMxSegTum)[0].shape)
    CD44v6thrd=sf.threshold_triangle(CD44v6DAB)
    Ecadthrd=sf.threshold_triangle(EcadDAB)

    CD44v6DAB=CD44v6DAB[:,:]>CD44v6thrd
    EcadDAB=EcadDAB[:,:]>Ecadthrd

    CD44v6DAB=morphology.binary_opening(CD44v6DAB)
    EcadDAB=morphology.binary_opening(EcadDAB)

    if(saveimgs):
        CQMint=np.zeros((CD44v6DAB.shape[0],CD44v6DAB.shape[1],3),dtype="uint8")
        CQMint[...,0]=EcadDAB*255
        CQMint[...,1]=CD44v6DAB*255
        io.imsave(saveimat+"CQM_"+c+"_"+core+".png",CQMint)

    #now the CQM is done

    #vals is used only for counting and percentages
    vals=np.zeros_like(CD44v6DAB,dtype="uint8")
    vals[EcadDAB[:,:]>0]+=2
    vals[CD44v6DAB[:,:]>0]+=1

    vals=vals*RCMxSegTum
    onlyCD44v6=np.prod(np.where(vals==1)[0].shape)
    onlyEcad=np.prod(np.where(vals==2)[0].shape)
    onlycomb=np.prod(np.where(vals==3)[0].shape)
    amountCD44v6=np.prod(np.where(RCMxSegTum*CD44v6DAB[:,:]>0)[0].shape)
    amountEcad=np.prod(np.where(RCMxSegTum*EcadDAB[:,:]>0)[0].shape)

    if(amountoftumor0>50): #bigger ahn 50 pixels...
        df.loc[idx,"CD44v6_p"]=amountCD44v6/amountoftumor0
        df.loc[idx,"Ecad_p"]=amountEcad/amountoftumor0
        df.loc[idx,"free_CD44v6_p"]=onlyCD44v6/amountoftumor0
        df.loc[idx,"free_Ecad_p"]=onlyEcad/amountoftumor0
        df.loc[idx,"coloc"]=onlycomb/amountoftumor0
        df.loc[idx,"extra_tissue"]=1.0-onlyCD44v6/amountoftumor0-onlyEcad/amountoftumor0-onlycomb/amountoftumor0
        df.loc[idx,"amountTumour"]=amountoftumor0
    else:
        #little to no tumorreport zeroes all over because even if there is protein there is no tumor.
        df.loc['CD44v6_p']=0
        df.loc['Ecad_p']=0,
        df.loc['free_CD44v6_p']= 0
        df.loc['free_Ecad_p']=0,
        df.loc['coloc']=0
        df.loc['extra_tissue']=0
        df.loc['amountTumour']= amountoftumor0
    
df.to_csv(mainloc+"quantification.csv")
