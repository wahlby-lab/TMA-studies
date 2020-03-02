dataUtils={
    _rawdata:{},
    _CSVHeader:[],
    _symbols:{block:"block",p1q:"p1q", p2q:"Ecadquantification",p1p:"CD44v6score",p2p:"Ecadscore",id:"Regions"},
    _scale:1
}

dataUtils.fillSymbols=function(){
    if(document.getElementById("dataSymbols").value){
        dataUtils._symbols=JSON.parse(document.getElementById("dataSymbols").value)
    }
    else{
        dataUtils._symbols={block:"block",p1q:"p1q", p2q:"Ecadquantification",p1p:"CD44v6score",p2p:"Ecadscore",id:"Regions"}
    }
}
/** 
 * @param {File} thecsv 
 * @return {Promise} 
 * Returns the promise of the raw data. Use then to call the data handler
 * */
dataUtils.readCSV = function (thecsv) {
    dataUtils.fillSymbols();
    dataUtils._rawdata = {};
    dataUtils._CSVHeader = [];
    
    var promise= new Promise(function(resolve, reject){
        var request = d3.csv(
            thecsv,
            function (d) { 
                //d[dataUtils._symbols.block]=Number(d[dataUtils._symbols.block])
                d[dataUtils._symbols.p1p]=Number(d[dataUtils._symbols.p1p])
                d[dataUtils._symbols.p1q]=Number(d[dataUtils._symbols.p1q])*dataUtils._scale;
                d[dataUtils._symbols.p2p]=Number(d[dataUtils._symbols.p2p])
                d[dataUtils._symbols.p2q]=Number(d[dataUtils._symbols.p2q])*dataUtils._scale;
                
                return d; },
            function (rows) {
                resolve( rows );
            }
        );
    });
    return promise;
}

dataUtils.processData=function(data){
    dataUtils.fillSymbols();
    dataUtils._rawdata = data;
    dataUtils._CSVHeader = Object.keys(dataUtils._rawdata[0]);
    var buttonsdiv=document.getElementById("blockButtons");

    var btn=document.createElement("button")
    btn.setAttribute("class","btn-primary")
    btn.addEventListener("click",function(){dataUtils.display()})
    btn.innerText="All"
    buttonsdiv.appendChild(btn)

    //sort by block
    dataUtils._nest=d3.nest().key(function(d){return d[dataUtils._symbols.block]})
        .entries(dataUtils._rawdata)
    dataUtils._nest.forEach(block => {
        var str=String(block.key);
        var btn=document.createElement("button")
        btn.setAttribute("class","btn-primary")
        btn.addEventListener("click",function(){dataUtils.display(block.key)})
        btn.innerText=block.key
        buttonsdiv.appendChild(btn)
    });

}

dataUtils.display=function(block_key){
    dataUtils.fillSymbols();
    boxplotUtils.createview(block_key);
}

dataUtils.showImages=function(indexinnestarray,region){
    console.log("in showimages"+indexinnestarray,region);
    var blockname=dataUtils._nest[indexinnestarray].key;
  /*  var rgbi="/media/carla/IPATIMUP8/TMAprocessing/"+blockname+"B/case"+blockname+"/CD44v6/CD44v6_"+blockname+"_B_RGB_"+region+".png";
    var H="/media/carla/IPATIMUP8/TMAprocessing/Ilastik/ilastik_allH/"+blockname+"_"+region+"_H.png";
    //var DAB="/media/carla/IPATIMUP8/TMAprocessing/Ilastik/ilastik_allDAB/"+blockname+"_"+region+"_DAB.png";
    var DAB="/media/carla/IPATIMUP8/TMAprocessing/experimentImages/CD44v6_"+blockname+"_"+region+"hardDAB.png"
    var tumor="/media/carla/IPATIMUP8/TMAprocessing/ilastikSegmentation/CD44v6_"+blockname+"_B_RGB_"+region+"-SimpleSegmentation.png"; 
    //var Hcells="/media/carla/IPATIMUP8/TMAprocessing/IlastikOutput_H/new"+blockname+"_"+region+"_H-SimpleSegmentation.png";
    var Hcells="/media/carla/IPATIMUP8/TMAprocessing/IlastikOutput_H/new"+blockname+"_"+region+"_H-ssdilated.png";
    var DABilastik="/media/carla/IPATIMUP8/TMAprocessing/IlastikOutput_DAB/new"+blockname+"_"+region+"_DAB-SimpleSegmentation.png";
*/
    var blockname=dataUtils._nest[indexinnestarray].key;
    var rgbi="ilastik/Ilastik_AllRGB/CD44v6_"+blockname+"_B_RGB_"+region+".png";
    //var H="ilastik/ilastik_allH/"+blockname+"_"+region+"_H.png";
    var H="ilastik/somebadcasesimages/"+blockname+"_"+region+"oldstyleH.png";
    var DAB="ilastik/somebadcasesimages/"+blockname+"_"+region+"hard.png";
    var tumor="ilastik/ilastikSegmentation/CD44v6_"+blockname+"_B_RGB_"+region+"-SimpleSegmentation.png";
    //var tumor="ilastik/somebadcasesimages/"+blockname+"_"+region+"hard.png";
//1_region11farid.png
    
    var rgbimelem=document.createElement("img");
    var tumimelem=document.createElement("img");
    var Himelem=document.createElement("img");
    var DABimelem=document.createElement("img");
    var Hcellsimelem=document.createElement("img");
    var DABilastikimelem=document.createElement("img");

    rgbimelem.setAttribute("class","img-fluid img-thumbnail")
    tumimelem.setAttribute("class","img-fluid img-thumbnail")
    Himelem.setAttribute("class",  "img-fluid img-thumbnail")
    DABimelem.setAttribute("class","img-fluid img-thumbnail")
    Hcellsimelem.setAttribute("class","img-fluid img-thumbnail")
    DABilastikimelem.setAttribute("class","img-fluid img-thumbnail")

    rgbimelem.setAttribute("alt",rgbi)
    tumimelem.setAttribute("alt",H)
    Himelem.setAttribute("alt",  DAB)
    DABimelem.setAttribute("alt",tumor)
    Hcellsimelem.setAttribute("alt",tumor)
    DABilastikimelem.setAttribute("alt",tumor)

    rgbimelem.src=rgbi;
    tumimelem.src=tumor;
    Himelem.src=H;
    DABimelem.src=DAB;
    Hcellsimelem.src=Hcells;
    DABilastikimelem.src=DABilastik;

    document.getElementById("currentregion").innerHTML=blockname+" "+region;

    document.getElementById("rgbimage").innerHTML="";
    document.getElementById("tumorimage").innerHTML="";
    document.getElementById("Himage").innerHTML="";
    document.getElementById("DABimage").innerHTML="";
    document.getElementById("Hcells").innerHTML="";
    document.getElementById("DABilastik").innerHTML="";

    document.getElementById("rgbimage").append(rgbimelem);
    document.getElementById("tumorimage").append(tumimelem);
    document.getElementById("Himage").append(Himelem);
    document.getElementById("DABimage").append(DABimelem);
    document.getElementById("Hcells").append(Hcellsimelem);
    document.getElementById("DABilastik").append(DABilastikimelem);

}
