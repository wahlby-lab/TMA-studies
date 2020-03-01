overlayUtils = {
    TMCPCount: { "fixed": 1, "moving": 1 },
    _drawRegions: true,
    _singleTMCPD3Groups: { "fixed": null, "moving": null }
}

overlayUtils.OSDimageWidth = function (overlay) {
    var width=tmcpoints[overlay+"_viewer"].world.getItemAt(0).getContentSize().x;
    return width;
}
overlayUtils.randomColor = function () {
    //I need random colors that are far away from the palette in the image
    //in this case Hematoxilyn and DAB so far away from brown and light blue
    //and avoid light colors because of the white  background 
    //in HSL color space this means L from 0.2 to 0.75
    //H [60,190],[220,360], S[0.3, 1.0]
    var rh1 = Math.floor(Math.random() * (190 - 60 + 1)) + 60;
    var rh2 = Math.floor(Math.random() * (360 - 220 + 1)) + 220;
    var H = 0.0;

    if (Math.random() > 0.5) { H = rh1; } else { H = rh2; }

    var L = Math.floor(Math.random() * (75 - 20 + 1)) + 20 + '%';
    var S = Math.floor(Math.random() * (100 - 30 + 1)) + 30 + '%';

    return 'hsl(' + H.toString() + ',' + S.toString() + ',' + L.toString() + ')';
}
//https://stackoverflow.com/questions/17824145/parse-svg-transform-attribute-with-javascript
overlayUtils.transformToObject = function (transform) {
    var b = {};
    for (var i in a = transform.match(/(\w+\((\-?\d+\.?\d*e?\-?\d*,?)+\))+/g)) {
        var c = a[i].match(/[\w\.\-]+/g);
        b[c.shift()] = c;
    }
    return b;

}
overlayUtils.objectToTransform = function (tobj) {
    var jsonstr = JSON.stringify(tobj);
    //console.log("jsonstr",jsonstr);
    jsonstr = jsonstr.replace("{", "");
    jsonstr = jsonstr.replace("}", "");
    jsonstr = jsonstr.replace(/("|:)/g, "");
    jsonstr = jsonstr.replace("[", "(");
    jsonstr = jsonstr.replace("]", ")");
    //console.log("after jsonstr",jsonstr);
    return jsonstr;
}

overlayUtils.addClosingHandlers = function (node) {
    new OpenSeadragon.MouseTracker({
        element: node,
        clickHandler: function (event) {
            var d3node = d3.select(node);
            if (d3node.classed("first")) {
                regionUtils.closePolygon();
                d3node.classed("first", false);//so that we dont call close anymore
            }
        }
    }).setTracking(true);
}

overlayUtils.addHandlersToNewTMCPS = function(id,overlay){
    d3.selectAll(".TMCP-" + overlay + "-" + id).each(function () {
		overlayUtils.addTrackingToDOMElement(this, overlay);
	});
}

overlayUtils.addTrackingToDOMElement = function (node, overlay) {
    new OpenSeadragon.MouseTracker({
        element: node,
        dragHandler:function (event) {
            var viewportDelta = overlayUtils.viewportDelta(event.delta, overlay);
            var d3node = d3.select(node);
            var transformobj = overlayUtils.transformToObject(d3node.attr("transform"));

            transformobj.translate[0] = Number(transformobj.translate[0]) + Number(viewportDelta.x);
            transformobj.translate[1] = Number(transformobj.translate[1]) + Number(viewportDelta.y);
            //console.log(transformobj);
            d3node.attr("transform", overlayUtils.objectToTransform(transformobj));
            //
            /*if (!d3node.classed("regionp")) {
                var id = d3node.attr("id").split("-")[2];
                var cellid = "cell-" + overlay + "-" + id;
                var cell = document.getElementById(cellid);
                var OSDPoint = new OpenSeadragon.Point(transformobj.translate[0], transformobj.translate[1]);
                var pToImageCoords = overlayUtils.pointToImage(OSDPoint, overlay);
                cell.textContent = "(" + Math.floor(pToImageCoords.x) + ", " + Math.floor(pToImageCoords.y) + ")";
            }*/
            //JSONUtils.setJSONString();
        },
        dragEndHandler: function (event) {
            var d3node = d3.select(node);
            //redraw regions to accomodate the change
            //perhaps do it only for region elements if possible
            //although this will imply differentiatin elemtns from regions ot nonreginos
            if (d3node.classed("regionp")) {
                //if a point from a region is dragged, erase the whole region and redraw
                var id = d3node.attr("class").split("regionp-")[1].split(" ")[0];
                //console.log(id);
                var overlay="";
                if(d3node.attr("class").includes("fixed")){
                    overlay="fixed"
                }else if(d3node.attr("class").includes("moving")){
                    overlay="moving"
                }
                //var overlay = d3node.attr("class").split("TMCP-")[1].split(" ")[0];
                //console.log(overlay);
                var color = d3node.select("path").attr("stroke");

                //according to the overlay, choose the selected proteins                
                var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key;                

                //console.log(id);
                regionUtils.removePoly("region"+id, overlay);
                var regionid = "region" + id.toString();
                var newpoints = []//apend arrays of 2 values
                d3.selectAll(".regionp-" + id + ".TMCP-" + overlay+"-"+id)["_groups"][0].forEach(function (TMCP) {
                    var transform = overlayUtils.transformToObject(d3.select(TMCP).attr("transform"));
                    var p0 = Number(transform["translate"][0]);
                    var p1 = Number(transform["translate"][1]);
                    newpoints.push([p0, p1]);
                });

                //console.log("newpoints ",newpoints)
                //var canvas=tmcpoints[overlay+"_svgov"].node();
                //var drawingclass="regionpolygr regionpolygr-"+id+" "+overlay;

                var regiongr = d3.select('.regionpolygr'+ '.'+ regionid + '.'+overlay);
                //var regiongr=d3.select("."+overlay+".regionpolygr-"+id);
                //console.log("regiongr ",regiongr);

                if (regionUtils._isNewRegion) {
                    regionUtils.modifyRegion(newpoints, id, overlay, protein);

                    regiongr.append('polygon').attr('points', newpoints)
                        .style('fill', 'none').style("stroke", color)
                        .attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
                        .attr('stroke', '#000').attr('class', "regionpoly regionpoly-" + id);
                } else {
                    regiongr.selectAll('polyline').remove();
                    regiongr.append('polyline').attr('points', newpoints)
                        .style('fill', 'none').style("stroke", "rgb(0,0,0)")
                        .attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
                        .attr('stroke', '#000').attr('class', "regionpoly regionpoly-" + id);
                }
                //regionUtils._regionD3Groups[overlay].select('regionpoly-'+id).remove();
            } else if (!d3node.classed("regionp")) {
                var htmlid = d3node.attr("id");
                //console.log(htmlid);
                var transformobj = overlayUtils.transformToObject(d3node.attr("transform"));
                markerUtils._TMCPS[overlay][htmlid] = { "x": Number(transformobj.translate[0]), "y": Number(transformobj.translate[1]) };
            }
        },
        clickHandler: function (event) {
            var d3node = d3.select(node);
            if (d3node.classed("first")) {
                regionUtils.closePolygon();
                d3node.classed("first", false);//so that we dont call close anymore
            }
        }
    }).setTracking(true);
}

overlayUtils.pointToImage = function (point, overlay) {
    if (overlay + "_viewer" in tmcpoints) {
        return tmcpoints[overlay + "_viewer"].viewport.viewportToImageCoordinates(point);
    }
}
overlayUtils.pointFromOSDPixel = function (position, overlay) {
    if (overlay + "_viewer" in tmcpoints) {
        return tmcpoints[overlay + "_viewer"].viewport.pointFromPixel(position);
    }
}
overlayUtils.imageToViewport = function (imcoords, overlay) {
    if (overlay + "_viewer" in tmcpoints) {
        return tmcpoints[overlay + "_viewer"].viewport.imageToViewportCoordinates(imcoords);
    }
}
overlayUtils.viewportDelta = function (eventdelta, overlay) {
    if (overlay + "_viewer" in tmcpoints) {
        return tmcpoints[overlay + "_viewer"].viewport.deltaPointsFromPixels(eventdelta);
    }
}

/** @function getMatchingPointsFromClickFixed takes an evnet happening in the fixed viewer
 * and returns the normalized coordinates in both viewers
 *  @param event comming from the fixed viewer   */
overlayUtils.getMatchingPointsFromClickFixed = function (event) {
    var normalizedPointF = overlayUtils.pointFromOSDPixel(event.position, "fixed");
    var imagePointF = overlayUtils.pointToImage(normalizedPointF, "fixed");
    var normalizedPointM = overlayUtils.imageToViewport(imagePointF, "moving");
    return { "fixed": normalizedPointF, "moving": normalizedPointM };
}
overlayUtils.removeAllFromOverlay = function (overlay) {
    d3.select(tmcpoints[overlay + "_svgov"].node()).selectAll("*").remove();
    //tmcpoints[overlay + "_singleTMCPS"] = d3.select(tmcpoints[overlay + "_svgov"].node()).append('g').attr('class', overlay + " singleTMCPS");
}
overlayUtils.moveSelectedRegion= function(direction){
    //var overlaybool=document.getElementById("radio_fixed").checked;
    var overlay="";
    if(interfaceUtils.isChecked("radio_moving")){
        overlay="moving";
    }else if(interfaceUtils.isChecked("radio_fixed")){
        overlay="fixed";
    }

    if(!overlay){
        console.log("Wrong overlay for moving region (\""+overlay+"\")");
    }
    
    //var regionid=interfaceUtils.getValueFromDOM("regionid_ta");
    var regionid=interfaceUtils.getSelectedIndexValue("select_region").key;
    //var regionid=document.getElementById("regionid_ta").value;
    var d=regionUtils._movementDelta;
    

    if(direction.includes("up"))
        {regionUtils.moveregion( regionid, 0,-d, false, overlay);}
    if(direction.includes("down"))
        {regionUtils.moveregion( regionid, 0, d, false, overlay);}
    if(direction.includes("left"))
        {regionUtils.moveregion( regionid,-d, 0, false, overlay);}
    if(direction.includes("right"))
        {regionUtils.moveregion( regionid, d, 0, false, overlay);}
}
overlayUtils.removeRegion=function(){
    //find region written in the text area:
    var regionid=interfaceUtils.getSelectedIndexValue("select_region").key;
    interfaceUtils.removeOptionFromSelect("select_region",regionid);
    regionUtils.deleteRegion(regionid);
}

overlayUtils.getZoom=function(overlay){
    var zoom= tmcpoints[overlay+"_viewer"].viewport.getZoom();
    return zoom;

}

overlayUtils.getCenter=function(overlay){
    var center= tmcpoints[overlay+"_viewer"].viewport.getCenter();
    return center;
}

overlayUtils.zoomTo=function(point,overlay){
    tmcpoints[overlay+"_viewer"].viewport.zoomTo(point);

}

overlayUtils.panTo=function(point,overlay){
    tmcpoints[overlay+"_viewer"].viewport.panTo(point);
}
/*
overlayUtils.addRowToTable = function (tableid, id, x1, y1, x2, y2) {

    var tablebody = document.getElementById(tableid);
    var row = tablebody.insertRow(0);

    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);

    cell1.textContent = id;
    cell2.id = "cell-fixed-" + id; cell2.textContent = "(" + Math.floor(x1) + ", " + Math.floor(y1) + ")";
    cell3.id = "cell-moving-" + id; cell3.textContent = "(" + Math.floor(x2) + ", " + Math.floor(y2) + ")";

}*/

/*
overlayUtils.addTMCPtoViewers = function (event) {
    // The canvas-click event gives us a position in web coordinates.
    //The evnet position is relative to OSD viewer 
    // Convert that to viewport coordinates, the lingua franca of OpenSeadragon coordinates.
    var normalizedPointF = overlayUtils.pointFromOSDPixel(event.position, "fixed");
    //draw in the fixed viewer, now we need to convert it to pixels and then to the moving space viewport to put there 
    var optionsF = overlayUtils.drawSingleTMCP("fixed", { "saveToTMCPS": true, "x": normalizedPointF.x, "y": normalizedPointF.y });
    //get the pixel coordinates in fixed image 
    var imagePointF = overlayUtils.pointToImage(normalizedPointF, "fixed");
    //get this pixel in moving normal space
    var normalizedPointM = overlayUtils.imageToViewport(imagePointF, "moving");
    //draw in the correct position in moving space
    var optionsM = overlayUtils.drawSingleTMCP("moving",
        { "saveToTMCPS": true, "x": normalizedPointM.x, "y": normalizedPointM.y, "strokeColor": optionsF.strokeColor });
    overlayUtils.addRowToTable("tmcptablebody", optionsF.id, imagePointF.x, imagePointF.y, imagePointF.x, imagePointF.y);
    //JSONUtils.setJSONString();
}*/
/* overlayUtils.drawSingleTMCP = function (overlay, options) {

    options.imageWidth = overlayUtils.OSDimageWidth(overlay);
    options.overlay = overlay;

    var elem = d3.select(tmcpoints[overlay + "_singleTMCPS"].node());
    return markerUtils.TMCP(elem, options);
} */