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
mainloc="/home/leslie/Documents/Uppsala/portugalDataset/carla/TMAProcessing/"
saveexperimentsat="/home/leslie/Documents/Uppsala/portugalDataset/carla/TMAProcessing/m-3-allRoberts/"
savefigat="/home/leslie/Documents/Uppsala/portugalDataset/carla/TMAProcessing/m-3-allHisto/"

TMAQ=tmaq.TMAQuantifier()
TMAQ.proteins=["CD44v6", "Ecad"] #the first is the important space
TMAQ.stains=stains=["H","DAB","mask","Tumor","RGB"]
TMAQ.morphology=0 #morphology shown by H
TMAQ.expression=1 #protein expression by DAB
TMAQ.mask=2; TMAQ.tumor=3; TMAQ.RGB=4

doRoberts=False
saveimgs=False

pandascsv="allcores.csv"

df=pd.read_csv(pandascsv)

for idx, row in df.iterrows():
    b=str(row["TMA_Slide"])
    core=row["Regions"]
    #print("block" + str(b)+"-"+core)
    TMAQ.block=str(b)
    TMAQ.corename=core

    TMAQ.imagelocations[("CD44v6", "H")  ]=mainloc+"m-3-allH/"+b+"_"+core+"_H.png"
    if(not os.path.isfile(TMAQ.imagelocations[("CD44v6", "H")])):
        print("H does not exist for "+b+"_"+core)
        continue

    TMAQ.imagelocations[("CD44v6", "mask") ]=mainloc+"m-3-allMask/CD44v6_"+b+"_"+core+"_mask.png"
    TMAQ.imagelocations[("CD44v6", "DAB")  ]=mainloc+"m-3-allDAB/"+b+"_"+core+"_DAB.png"
    TMAQ.imagelocations[("CD44v6", "tumor")  ]=mainloc+"ilastikSegmentation/CD44v6_"+b+"_B_RGB_"+core+"-SimpleSegmentation.png"
    TMAQ.imagelocations[("CD44v6", "Tumor0")]=mainloc+"LoResSegFromHiREs/CD44v6_"+b+"_"+core+"_mask0.png"
    TMAQ.imagelocations[("CD44v6", "Tumor1")]=mainloc+"LoResSegFromHiREs/CD44v6_"+b+"_"+core+"_mask1.png"
    TMAQ.imagelocations[("CD44v6", "Tumor2")]=mainloc+"LoResSegFromHiREs/CD44v6_"+b+"_"+core+"_mask2.png"
    TMAQ.imagelocations[("CD44v6", "Tumor4")]=mainloc+"LoResSegFromHiREs/CD44v6_"+b+"_"+core+"_mask4.png"
  
    TMAQ.imagelocations[("Ecad"  , "DAB")  ]=mainloc+"ReAlignLoRes/Ecad_"+b+"_"+core+"_DAB_T.png" 
    
    
    if(TMAQ.checkExistance()):
        continue

    tumor=TMAQ.getStainFromProtein("CD44v6","tumor",value_at=85,as_bool=True)

    mainDAB=TMAQ.getStainFromProtein("CD44v6","DAB",load_as_float=True)
    ecadDAB=TMAQ.getStainFromProtein("Ecad","DAB",load_as_float=True)
    mask=TMAQ.getStainFromProtein("CD44v6","mask",as_bool=True)

    tumor*=mask

    #CD44v6 quantification

    quanthere=mainDAB

    if(doRoberts):
        roberts=sf.roberts(mainDAB)
        quanthere=                np.greater(mainDAB, 0.5)  * np.minimum( 1.0-(1.0-2.0*(mainDAB-0.5))*(1.0-roberts) , 1.0) 
        quanthere+=np.logical_not(np.greater(mainDAB, 0.5)) * np.minimum( roberts * (mainDAB * 2.0), 1.0 )
        
        if(saveimgs):            
            roberts*=255.0
            roberts=roberts.astype("uint8")
            io.imsave(saveexperimentsat+"CD44v6_"+b+"_"+core+"_roberts_gamma_DAB.png",quanthere)

    quanthere=trans(quanthere,0.2, 0.15, 1.0)
    quanthere=quanthere>=.03

    quanthereorig=quanthere*tumor0
    
    p1q=np.sum(quanthereorig)

    df.loc[idx,"p1"]=p1q

    #Ecad quantification
    
    quanthere2=ecadDAB
    
    if(doRoberts):
        roberts2=sf.roberts(ecadDAB)
        quanthere2=                np.greater(ecadDAB, 0.5)  * np.minimum( 1.0-(1.0-2.0*(ecadDAB-0.5))*(1.0-roberts2) , 1.0) 
        quanthere2+=np.logical_not(np.greater(ecadDAB, 0.5)) * np.minimum( roberts2 * (ecadDAB * 2.0), 1.0 )

    #quanthere2=trans(quanthere2,0.2, 0.15, 1.0)

    #some possible consideration
    #quanthere2=se.rescale_intensity(quanthere2)
    #p2, p98 = np.percentile(quanthere2, (1, 99))
    #0.3 because we dont want to have a black image turn into white
    #quanthere2 = exposure.rescale_intensity(quanthere2, in_range=(p2, 0.3))
    
    quanthere2=quanthere2>=.03
    
    quanthereEorig=quanthere2*tumor
    
    p2q=np.sum(quanthereEorig)
    
    df.loc[idx,"p2"]=p2q

    sumtumorig=np.sum(tumor)
    
    sumtum0=np.sum(tumor0)

    df.loc[idx,"tumor"]=sumtumorig

    df.loc[idx,"p1q"]=100*(p1q/sumtum0)

    df.loc[idx,"p2q"]=100*(p2q/sumtum0)
    
df.to_csv(mainloc+"N261DAB-oldtumor-noroberts-trans-02-015-1.csv")
