from skimage import io, morphology, img_as_float, exposure
import skimage.filters as sf
import skimage.exposure as se
import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import imagelibs.coloquantfunctions as tmaq

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
savefigat="/home/leslie/Documents/TMACOEXP/experiments/"

TMAQ=tmaq.TMAQuantifier()
TMAQ.proteins=["CD44v6", "Ecad"] #the first is the important space
TMAQ.stains=["H","DAB","mask","tumor","RGB"]
TMAQ.morphology=0 #morphology shown by H
TMAQ.expression=1 #protein expression by DAB
TMAQ.mask=2; TMAQ.tumor=3; TMAQ.RGB=4

doRoberts=True
saveimgs=False

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
            io.imsave(saveexperimentsat+"CD44v6_"+c+"_"+core+"_roberts_gamma_DAB.png",quanthere)

    #quanthere=trans(quanthere,0.2, 0.15, 1.0)
    quanthere=quanthere>=.03

    quanthereorig=quanthere*tumor
    
    p1q=np.sum(quanthereorig)

    df.loc[idx,"p1"]=p1q

    # Ecad quantification
    
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

    sumtum=np.sum(tumor)

    df.loc[idx,"tumor"]=sumtum

    df.loc[idx,"p1q"]=100*(p1q/sumtum)

    df.loc[idx,"p2q"]=100*(p2q/sumtum)
    
df.to_csv(mainloc+"quantification.csv",index=False)
