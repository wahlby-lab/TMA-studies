/**
 * @namespace dataUtils
 * @classdesc Sets of functions to prepare and preload data information and proteins
*/
dataUtils = {
    _nestingkey1:"case",
    _nestingkey2:"block",
    _rawdata : {},
    _casedata:[],
    _csv_header: [],
    _fixedElementName:"",
    _proteins:[],
    //in theory it is only one fixed protein
    // but if I dont want to commit to it
    //I can just have an array
    _fixedProteins:[], 
    _movingProteins:[],
    _case:"",
    _block:"",
    _experimentName:""
}

/** 
 * @param {File} thecsv 
 * @return {Array} The csv headers.
 * This reads the CSV and stores the raw data and sets the headers 
 * Later on it should be nested according to the main criteria */
dataUtils.readCSV = function (thecsv) {
    var request = d3.csv(
        thecsv,
        function (d) { return d; },
        function (rows) {
            dataUtils["_rawdata"] = rows;
            var csvheaders = Object.keys(dataUtils["_rawdata"][0]);
            dataUtils._csv_header = csvheaders;
            var allslides = d3.nest()
                .key(function (d) { return d[dataUtils._nestingkey1]; })
                .key(function (d) { return d[dataUtils._nestingkey2]; })
                .entries(rows);
    
            allslides.forEach(function (n) {
                dataUtils["_casedata"].push(n);
            });

            var cases=[];
            for(var c in dataUtils._casedata){
                cases.push(dataUtils._casedata[c].key);
            }
            
            //interfaceUtils.cleanSelect("select_case_fixed");
            interfaceUtils.addElementsToSelect("select_case_fixed",cases);
            interfaceUtils.listen("select_case_fixed","change",dataUtils.addBlocksForCase);
            interfaceUtils.enableElement("select_case_fixed");
        }
    );
}

dataUtils.addBlocksForCase=function(){
    var option=interfaceUtils.getSelectedIndexValue("select_case_fixed").key;
    //find blocks for selected case:
    var casekey=option.toString();

    dataUtils._case=casekey;

    for(var c in dataUtils._casedata){
        var strkey=dataUtils._casedata[c].key.toString();
        //if it returns 0 they are equal
        if(!casekey.localeCompare(strkey)){
            //bring blocks
            var list=[];
            dataUtils._casedata[c].values.forEach(
                element=>{list.push(element.key)
            });
            //interfaceUtils.cleanSelect("select_block_fixed");
            interfaceUtils.addElementsToSelect("select_block_fixed",list);
            interfaceUtils.enableElement("select_block_fixed");
            interfaceUtils.listen("select_block_fixed","change",function(){dataUtils.addProteinsFromBlock(true)});
            interfaceUtils.disableElement("select_case_fixed");
        }        
    }
}

dataUtils.addProteinsFromBlock= function(addtoui){
    //var caseoption=interfaceUtils.getSelectedIndexValue("select_case_fixed").key;
    var casekey=dataUtils._case;
    var blockoption=interfaceUtils.getSelectedIndexValue("select_block_fixed").key;
    var blockkey=blockoption.toString();
    dataUtils._block=blockkey;

    var proteins=[];

    for(var c in dataUtils._casedata){        
        var strkey=dataUtils._casedata[c].key.toString();
        //if it returns 0 they are equal
        if(!casekey.localeCompare(strkey)){
            //bring blocks
            for(var b in dataUtils._casedata[c].values){
                var bkey=dataUtils._casedata[c].values[b].key.toString();
                blockkey=blockkey.toString();
                if(!bkey.localeCompare(blockkey)){
                    
                    dataUtils._casedata[c].values[b].values.forEach( element=>{
                        var obj={};
                        obj.value=element.protein;
                        obj.innerHTML=element.protein+" "+element.filename
                        proteins.push(obj)
                    });

                    //interfaceUtils.cleanSelect("select_protein_fixed");
                    //this has to be called at least once!
                    if(addtoui){
                        interfaceUtils.addObjectsToSelect("select_protein_fixed",proteins);
                        interfaceUtils.enableElement("select_protein_fixed");
                        interfaceUtils.listen("select_protein_fixed","change",dataUtils.selectFixedProtein);
                        interfaceUtils.disableElement("select_block_fixed");
                    }
                }            
            }           
        }        
    }

    return proteins;
}

dataUtils.selectFixedProtein=function(){
    var caseoption=interfaceUtils.getSelectedIndexValue("select_case_fixed");
    var casekey=caseoption.key.toString();
    var blockoption=interfaceUtils.getSelectedIndexValue("select_block_fixed");
    var blockkey=blockoption.key.toString();
    var proteins=dataUtils.addProteinsFromBlock(false);

    proteins.forEach(
        protein => { 
            var pname=protein.value
            //console.log("creating proteins everywhere");
            regionUtils._regions[pname]={};
            regionUtils._regionD3Groups[pname]=null;
            dataUtils._proteins.push(pname);

            regionUtils._regions[pname].case=dataUtils._case;
            regionUtils._regions[pname].block=dataUtils._block;
    });

    var mainprotein=interfaceUtils.getSelectedIndexValue("select_protein_fixed").key.toString();
    regionUtils._regions[mainprotein]["property"]="fixed";
    dataUtils._fixedProteins.push(mainprotein);
    proteins = proteins.filter(e => e.value !== mainprotein);
    proteins.forEach(protein=>{
        var pname=protein.value
        regionUtils._regions[pname]["property"]="moving";
        dataUtils._movingProteins.push(pname);
    });
    interfaceUtils.addObjectsToSelect("select_protein_moving",proteins);
    interfaceUtils.enableElement("select_protein_moving");
    interfaceUtils.disableElement("select_protein_fixed");
    interfaceUtils.listen("select_protein_moving","change",dataUtils.selectMovingProtein);
    
    //------tmcpoints.fixed_viewer.open(tmcpoints.url_prefix + tmcpoints.fixed_file);
    //interfaceUtils.emptyViewers( {containers:["fixed"]} );
    //load image in OSD fixed
    //create name to open
    var info = dataUtils.proteinInfo(casekey,blockkey,mainprotein);
    var dzifile=info.filename;
    interfaceUtils.openDZI(dzifile,"fixed");
}

dataUtils.selectMovingProtein=function(){
    //load image on OSD moving
    var caseoption=interfaceUtils.getSelectedIndexValue("select_case_fixed");
    var casekey=caseoption.key.toString();
    var blockoption=interfaceUtils.getSelectedIndexValue("select_block_fixed");
    var blockkey=blockoption.key.toString();
    var proteinoption=interfaceUtils.getSelectedIndexValue("select_protein_moving");
    var protein=proteinoption.key.toString();

    var info = dataUtils.proteinInfo(casekey,blockkey,protein);
    var dzifile=info.filename;
    //inside this there will be a call for "open" handlers
    interfaceUtils.openDZI(dzifile,"moving"); 

    //Also erase the current view of regions and replace with the regions from this protein
    //this will be as a hanlder for the open event in the OSD viewer

}

dataUtils.proteinInfo=function(casekey,block,protein){
    casekey=casekey.toString();
    block=block.toString();
    var info={};
    for(var c in dataUtils._casedata){        
        var strkey=dataUtils._casedata[c].key.toString();
        //if it returns 0 they are equal
        if(!casekey.localeCompare(strkey)){
            //bring blocks
            //console.log(casekey,"found");
            var blocksincase=dataUtils._casedata[c].values;
            for(var b in blocksincase){
                //console.log(b,blocksincase[b].key);
                var bkey=blocksincase[b].key.toString();
                bkey=bkey.toString();
                if(!bkey.localeCompare(block)){
                    //console.log(bkey,"found");
                    var allblockproteins=blocksincase[b].values;
                    //console.log(allblockproteins);
                    allblockproteins.forEach(p=>{
                        if(!protein.localeCompare(p.protein)){
                            //console.log(protein,"found");
                            info=p;
                        }
                    });
                }            
            }           
        }        
    }
    return info;
}

