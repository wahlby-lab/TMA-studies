JSONUtils = {}
//This function calls all the points in the Fabric JS canvases and encodes them into JSON
//format in a way that is suitable for numpy.linalg.lstsq least squares to find the 
//affine transformation matrix.
//https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.lstsq.html
/**
 * @function
 * Take the currently drawn SVG points, look at their transform attribute using 
 * {@link overlayUtils.transformToObject} and then 
 * find the coordinate in the image space in pixels by calling {@link overlayUtils.pointToImage}
 * @returns {Object} An object with two keys to the arrays of the points locations in the
 * two viewers
 */
JSONUtils.pointsToJSON = function () {
    var me = {};
    me.reference = Array();
    me.floating = Array();

    d3.selectAll(".TMCP-fixed").each(function () {
        var d3node = d3.select(this);
        var transformObj = overlayUtils.transformToObject(d3node.attr("transform"));
        var OSDPoint = new OpenSeadragon.Point(Number(transformObj.translate[0]), Number(transformObj.translate[1]));
        var imageCoord = overlayUtils.pointToImage(OSDPoint, "fixed");
        me.reference.push(Array(imageCoord.x, imageCoord.y, 1));
        //console.log(OSDPoint,imageCoord);
    });

    d3.selectAll(".TMCP-moving").each(function () {
        var d3node = d3.select(this);
        var transformObj = overlayUtils.transformToObject(d3node.attr("transform"));
        var OSDPoint = new OpenSeadragon.Point(Number(transformObj.translate[0]), Number(transformObj.translate[1]));
        var imageCoord = overlayUtils.pointToImage(OSDPoint, "moving");
        me.floating.push(Array(imageCoord.x, imageCoord.y, 1));
        // console.log(OSDPoint,imageCoord);
    });

    return me;
}
JSONUtils.dataToJSON = function () {
    var data = { "regions": { "fixed": {}, "moving": {} }, "points": { "fixed": {}, "moving": {} } };
    data.regions = regionUtils._regions;
    data.points = markerUtils._TMCPS;

    return data;
}
/**
 * @function
 * Save the data from a hiden <a> tag into a json file containing the locations of the points.
 */
JSONUtils.downloadJSON = function () {
    var a = document.getElementById("hiddena");
    var a = document.createElement("a");
    var data = "text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(JSONUtils.dataToJSON(), 0, 4));
    a.setAttribute("href", "data:" + data);
    var caseSelector=document.getElementById("select_case_fixed");
    var caseName="";
    if(caseSelector){
        caseName = caseSelector.options[caseSelector.selectedIndex].value;
    }    
    var blockName="data";
    var blockSelector=document.getElementById("select_block_fixed");
    if(blockSelector){
        blockName = blockSelector.options[blockSelector.selectedIndex].value;
    }
    var filename="case"+caseName+"_"+blockName+".json";
    a.setAttribute("download", filename);
    a.setAttribute('visibility', 'hidden');
    a.setAttribute('display', 'none');
    a.click();
}
/**
 * @function
 * Fill the text area with the points JSON, be it current points in display or the imported points
 * @param {Object} jsonpoints - JSON obejct to stringify
 */
JSONUtils.setJSONString = function (jsonpoints) {
    var ta = document.getElementById('jsonpoints');
    ta.className = "form-control";

    if (jsonpoints) {
        ta.value = JSON.stringify(jsonpoints);
    } else {
        ta.value = JSON.stringify(JSONUtils.pointsToJSON(), 0, 4);
    }
}
/**
 * @function 
 * Read text area and create all the 
 * symbols dynamically. If the JSON is not well formatted or has different amount of points
 * in the images, the points will not be loaded.
 */


JSONUtils.readJSONToData = function () {
    overlayUtils.removeAllFromOverlay("fixed");
    overlayUtils.removeAllFromOverlay("moving");
    interfaceUtils.cleanSelect("select_region");
    //var tablebody = document.getElementById("tmcptablebody");
    //tablebody.innerHTML = "";
    overlayUtils.TMCPCount["fixed"] = 0;
    overlayUtils.TMCPCount["moving"] = 0;
    regionUtils._currentRegionId = 0;
    if (window.File && window.FileReader && window.FileList && window.Blob) {

        var text = document.getElementById("data_files_import");
        var file = text.files[0];
        if (!file) { alert('No file selected'); return; }
        if (file.type.match('json')) {
            //console.log(file);
            var reader = new FileReader();
            reader.onload = function (event) {
                JSONUtils.importDataFromJSON(JSON.parse(event.target.result));
                //console.log(JSON.parse(event.target.result));
            };
            //var result=
            reader.readAsText(file);
        }
    } else {
        alert('The File APIs are not fully supported in this browser.');
    }

}

JSONUtils.importDataFromJSON = function (datainJSONFormat) {

    //regionUtils._regions={"regions":{}};
    var keys=Object.keys(datainJSONFormat.regions);
    //console.log(datainJSONFormat.regions);
    //console.log(keys);
    if(keys.length==0){
        console.log("No regions or wrongly formatted");
    }else{
        var regionKeys=Object.keys(datainJSONFormat.regions[keys[0]]);
        var mainlength=regionKeys.length;
        //console.log("mainlength",mainlength,datainJSONFormat);
        for(protein in datainJSONFormat.regions){
            var regions=datainJSONFormat.regions[protein];
            var comparekeys=Object.keys(regions);
            if(comparekeys.length!=mainlength){
                console.log("Element "+protein+" is missing regions");
                return null;
            }else{
                mainlength=comparekeys.length; 
            }
        }
        //if we get here means all regions are correctly formated, 
        //load into json and then to viewres
    }
    
    var maxregionid=0;

    for(protein in datainJSONFormat.regions){
        //console.log("protein",protein);
        var elements=datainJSONFormat.regions[protein];

        //console.log("elements",elements);
        for(key in elements){
            if(key.includes("region")){
                //console.log("key",key);
                var region=datainJSONFormat.regions[protein][key];
                //console.log(region)
                var regionid=region.id;
                regionUtils._regions[protein][regionid]=regionUtils.cloneRegion(region);
            }
        }
    }
   

    var fixedProtein=interfaceUtils.getSelectedIndexValue("select_protein_fixed").key;interfaceUtils.getSelectedIndexValue
    var movingProtein=interfaceUtils.getSelectedIndexValue("select_protein_moving").key;interfaceUtils.getSelectedIndexValue
    
    for(element in regionUtils._regions[fixedProtein]){   
        if(element.includes("region")){
            var region=regionUtils._regions[fixedProtein][element];
            //console.log(region);
            var regionid=region.id;
            var id = regionid.replace(/\D/g, ''); id = Number(id);
            if(id>maxregionid) maxregionid=id;
            regionUtils._currentRegionId=id;
            regionUtils.importRegion(region,"fixed");
        }        
    }

    for(element in regionUtils._regions[movingProtein]){   
        if(element.includes("region")){
            var region=regionUtils._regions[movingProtein][element];
            //console.log(region);
            var regionid=region.id;
            var id = regionid.replace(/\D/g, ''); id = Number(id);
            if(id>maxregionid) maxregionid=id;
            regionUtils._currentRegionId=id;
            regionUtils.importRegion(region,"moving");
            //add only once
            interfaceUtils.addSingleElementToSelect("select_region","region" + id);
        }        
    }
    
    
    
    regionUtils._currentRegionId=maxregionid;  
}