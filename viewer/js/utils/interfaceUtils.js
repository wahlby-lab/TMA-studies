interfaceUtils={}

interfaceUtils.listen= function(domid,event,handler){
    var elem= document.getElementById(domid);
    if(elem){
        elem.addEventListener(event, handler);
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.addElementsToSelect=function(domid,elemlist){
    var select= document.getElementById(domid);
    if(select){
        elemlist.forEach(element => {
            var opt = document.createElement("option");
            opt.value= element;
            opt.innerHTML = element;
            select.appendChild(opt);
        });
    }else{
        console.log("Select with id "+domid+" doesn't exist");
    }
}

interfaceUtils.addObjectsToSelect=function(domid,objlist){
    var select= document.getElementById(domid);
    if(select){
        objlist.forEach(element => {
            var opt = document.createElement("option");
            opt.value= element.value;
            opt.innerHTML = element.innerHTML;
            select.appendChild(opt);
        });
    }else{
        console.log("Select with id "+domid+" doesn't exist");
    }
}

/**
 * domid string, element string, options, object with HTML options for opt
 */
interfaceUtils.addSingleElementToSelect=function(domid,element,options){
    if(!options) options={};
    var select= document.getElementById(domid);
    if(select){       
        var opt = document.createElement("option");
        if(options.id) opt.id="region_opt_"+element;
        opt.value= element;
        opt.innerHTML = element;
        select.appendChild(opt);        
    }else{
        console.log("Select with id "+domid+" doesn't exist");
    }
}

interfaceUtils.cleanSelect=function(domid){
    var select= document.getElementById(domid);
    if(select){       
        select.innerHTML = "";
    }else{
        console.log("Select with id "+domid+" doesn't exist");
    }
}

interfaceUtils.disableElement=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        elem.disabled="true";
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.enableElement=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        elem.removeAttribute("disabled");
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.isEnabled=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        if(elem.hasAttribute("disabled")){
            return false;
        }else{ return true; }
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

/**
 * Returns an object containing key and value of selection
 */
interfaceUtils.getSelectedIndexValue=function(domid){
    var selector= document.getElementById(domid);
    if(selector){
        var obj={};
        obj.key = selector.options[selector.selectedIndex].value;
        obj.value =selector.options[selector.selectedIndex].innerHTML;
        return obj;
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }

}

interfaceUtils.getElementById=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        return elem;
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.getValueFromDOM=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        return elem.value;
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.getInnerHTMLFromDOM=function(domid){
    var elem= document.getElementById(domid);
    if(elem){
        return elem.innerHTML;
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }
}

interfaceUtils.removeOptionFromSelect=function(domid,key){
    var select= document.getElementById(domid);
    if(select){
        var remove=0;
        for (var i=0; i<select.length; i++){
            if (select.options[i].value == key )
                remove=i;
        }
        select.remove(remove);
    }else{
        console.log("Select with id "+domid+" doesn't exist");
    }
}

interfaceUtils.emptyViewers = function (options) {
    var containers = options.containers || ["fixed", "moving"];
    containers.forEach(function (c) {
        var container = document.getElementById(c + "_viewer");
        while (container.lastChild) {
            container.removeChild(container.lastChild);
        }
    });  
}

interfaceUtils.openDZI=function(dzi,viewer){
    var possibleurlprefix=interfaceUtils.getValueFromDOM("url_prefix");
    if(possibleurlprefix){
        tmcpoints.url_prefix=possibleurlprefix;
    }
    tmcpoints[viewer+"_viewer"].open(tmcpoints.url_prefix + dzi);
    /*if(viewer=="moving"){

    }*/
    
}

interfaceUtils.isChecked=function(domid){
    var check= document.getElementById(domid);
    if(check){
        var checked=check.checked;
        return checked;
    }else{
        console.log("Check with id "+domid+" doesn't exist");
    }
}

interfaceUtils.checkSelectNotZero=function(domid){
    var selector= document.getElementById(domid);
    if(selector){
        var key = selector.options[selector.selectedIndex].value;
        if(key.toString()=="0") 
            return false;
        return true;
    }else{
        console.log("Element with id "+domid+" doesn't exist");
    }

}