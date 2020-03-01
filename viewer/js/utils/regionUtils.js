regionUtils = {
	/** if _isNewRegion is true then a new region will start */
	_isNewRegion: true,
	/** _currentlyDrawing:false, */
	_currentlyDrawing: false,
	/** __currentRegionId: keep then number of drawn regions and also let them be the id, */
	_currentRegionId: 0,
	/** _currentPoints: array of points for the current region, */
	_currentPoints: { "fixed": [], "moving": [] },
	/** _currentColor: hsl() or rgb() color of the region, to be appleid only to a region, */
	_currentColor: null,
	/** _colorInactiveHandle:"#cccccc", */
	_colorInactiveHandle: "#cccccc",
	/** _colorActiveHandle: Color of the point in the region, */
	_colorActiveHandle: "#ffff00",
	/** _scaleHandle: scale of the point in regions, */
	_scaleHandle: 0.0025,
	/** _polygonStrokeWidth: width of the stroke of the polygon, */
	_polygonStrokeWidth: 0.0006,
	/** _handleRadius:Radius of the point of the region, */
	_handleRadius: 0.1,
	/** _epsilonDistance: distance at which a click from the first point will consider to be closing the region, */
	_epsilonDistance: 0.004,
	/** _regions: object that contains the regions in the viewer, */
	_regions: {  },/*"fixed": {}, "moving": {}  */
	/** D3 groups to draw polys on */
	_regionD3Groups: { },/*"fixed": null, "moving": null*/
	/** _drawingclass: add this class to regionobejcts so that they can be removed easily */
	_drawingclass: "drawPoly",
	/** Movement delta for the moving regions buttons */
	_movementDelta: 0.01
}
regionUtils.resetManager = function () {
	//var drawingclass=regionUtils._drawingclass;
	//d3.select("."+drawingclass).remove();
	regionUtils._isNewRegion = true;
	regionUtils._currentColor = overlayUtils.randomColor();
	//regionUtils._regions= {  };/*"fixed": {}, "moving": {}  */
	//regionUtils._regionD3Groups= { };/*"fixed": null, "moving": null*/
}

regionUtils.clearCurrentRegionsArray=function(){
	for(var regionprotein in regionUtils._currentPoints){
		regionUtils._currentPoints[regionprotein]=[];
	}
}


regionUtils.manager = function (event) {

	var drawingclass = regionUtils._drawingclass;
	var regiongrm;

	var viwerPoint = overlayUtils.getMatchingPointsFromClickFixed(event);
	var epointf = viwerPoint.fixed;
	var epointm = viwerPoint.moving;
	var canvasF = tmcpoints.fixed_svgov.node();
	var canvasM = tmcpoints.moving_svgov.node();

	// get the currently selected proteins to know which regions to create
	var fixedProtein =interfaceUtils.getSelectedIndexValue("select_protein_fixed").key;
	var movingProtein=interfaceUtils.getSelectedIndexValue("select_protein_moving").key;

	if (regionUtils._isNewRegion) {
		regionUtils.resetManager();
		//if this region is new then there should be no points, create a new array of points
		regionUtils.clearCurrentRegionsArray();
		regionUtils._currentPoints[fixedProtein] =[];
		regionUtils._currentPoints[movingProtein]=[];
		//it is not a new region anymore
		regionUtils._isNewRegion = false;
		//give a new id
		regionUtils._currentRegionId += 1;
		var id = regionUtils._currentRegionId;

		regionUtils._currentPoints[fixedProtein].push([epointf.x, epointf.y]);
		regionUtils._currentPoints[movingProtein].push([epointm.x, epointm.y]);
		//create a group to store region
		//these groups parents must exist thanks to @dataUtils.addProteinsFromBlock
		regionUtils._regionD3Groups["fixed"] = d3.select(canvasF).append('g').attr('class', "fixed regionpolygr region" + id +" "+fixedProtein);
		regionUtils._regionD3Groups["moving"] = d3.select(canvasM).append('g').attr('class', "moving regionpolygr region"+id +" "+movingProtein);

		regiongrf = regionUtils._regionD3Groups["fixed"];
		regiongrm = regionUtils._regionD3Groups["moving"];
		//instead of a circle put a TMCP
		markerUtils.TMCP(regiongrf, {
			"extraClass": "fixed first regionp regionp-" + id + " "+fixedProtein,
			"x": epointf.x, "y": epointf.y, "strokeColor": regionUtils._currentColor,
			"overlay": "fixed", "regionIDNumber": id
		})
		markerUtils.TMCP(regiongrm, {
			"extraClass": "moving first regionp regionp-" + id+" "+movingProtein,
			"x": epointm.x, "y": epointm.y, "strokeColor": regionUtils._currentColor,
			"overlay": "moving","regionIDNumber": id
		})

	} else {
		var id = regionUtils._currentRegionId;
		//var count = regionUtils._currentPoints.fixed.length - 1;

		regionUtils._currentPoints[fixedProtein].push([epointf.x, epointf.y]);
		regionUtils._currentPoints[movingProtein].push([epointm.x, epointm.y]);

		regiongrf = regionUtils._regionD3Groups["fixed"];
		regiongrm = regionUtils._regionD3Groups["moving"];

		//instead of a circle put a TMCP
		markerUtils.TMCP(regiongrf, {
			"extraClass": "fixed " +fixedProtein+ " regionp regionp-" + id ,
			"x": epointf.x, "y": epointf.y, "strokeColor": regionUtils._currentColor, 
			"overlay": "fixed", "regionIDNumber": id
		})
		markerUtils.TMCP(regiongrm, {
			"extraClass": "moving "+movingProtein+" regionp regionp-" + id,
			"x": epointm.x, "y": epointm.y, "strokeColor": regionUtils._currentColor, 
			"overlay": "moving", "regionIDNumber": id
		})

		regiongrf.select('polyline').remove();
		regiongrf.append('polyline').attr('points', regionUtils._currentPoints[fixedProtein])
			.style('fill', 'none')
			.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
			.attr('stroke', '#000').attr('class', "region" + id);

		regiongrm.select('polyline').remove();
		regiongrm.append('polyline').attr('points', regionUtils._currentPoints[movingProtein])
			.style('fill', 'none')
			.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
			.attr('stroke', '#000').attr('class', "region" + id);

	}
}
regionUtils.distance = function (p1, p2) {
	return Math.sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]))

}
regionUtils.addRegion = function (points, regionid, overlay) {
	//console.log(points);
	var id = regionUtils._currentRegionId;
	var region = { "id": "region" + id, "points": [], "globalPoints": [], "regionName": regionid, "regionClass": null, "color": regionUtils._currentColor };
	var imageWidth = overlayUtils.OSDimageWidth(overlay);
	region.len = points.length;
	var _xmin = points[0][0], _xmax = points[0][0], _ymin = points[0][1], _ymax = points[0][1];
	var objectPointsArray = [];
	for (var i = 0; i < region.len; i++) {
		if (points[i][0] > _xmax) _xmax = points[i][0];
		if (points[i][0] < _xmin) _xmin = points[i][0];
		if (points[i][1] > _ymax) _ymax = points[i][1];
		if (points[i][1] < _ymin) _ymin = points[i][1];
		region.points.push({ "x": points[i][0], "y": points[i][1] });
		region.globalPoints.push({ "x": points[i][0] * imageWidth, "y": points[i][1] * imageWidth });
	}
	region._xmin = _xmin, region._xmax = _xmax, region._ymin = _ymin, region._ymax = _ymax;
	region._gxmin = _xmin * imageWidth, region._gxmax = _xmax * imageWidth, region._gymin = _ymin * imageWidth, region._gymax = _ymax * imageWidth;
	
	region.protein="";

	//glitch of moving fixed protein is here!-------------------------------------------------------
	regionUtils.commitRegions(region,overlay);
	//and in case I have a region UI add it
	//regionUtils.regionUI(regionid);
}

regionUtils.commitRegions=function(region,overlay){
	var regionid=region.id;
	dataUtils["_"+overlay+"Proteins"].forEach(protein=>{
		var regionClone=regionUtils.cloneRegion(region);
		regionClone.protein=protein;
		regionUtils._regions[protein][regionid] = regionClone;
	});

}

regionUtils.cloneRegion = function(region){

	var regionClone = JSON.parse(JSON.stringify(region));
	return regionClone;

}

regionUtils.closePolygon = function () {
	var id = regionUtils._currentRegionId
	var regiongrf = regionUtils._regionD3Groups["fixed"];
	var regiongrm = regionUtils._regionD3Groups["moving"];
	var fixedProtein =interfaceUtils.getSelectedIndexValue("select_protein_fixed").key;
	var movingProtein=interfaceUtils.getSelectedIndexValue("select_protein_moving").key;

	regiongrf.select('polyline').remove();
	var polylinef = regiongrf.append('polygon').attr('points', regionUtils._currentPoints[fixedProtein])
		.style('fill', 'none').style("stroke", regionUtils._currentColor)
		.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
		.attr('class', "regionpoly regionpoly" + id);

	regiongrm.select('polyline').remove();
	var polylinem = regiongrm.append('polygon').attr('points', regionUtils._currentPoints[movingProtein])
		.style('fill', 'none').style("stroke", regionUtils._currentColor)
		.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
		.attr('class', "regionpoly regionpoly" + id);

	regionUtils._isNewRegion = true;

	regionUtils.addRegion(regionUtils._currentPoints[fixedProtein], "region" + id, "fixed");
	regionUtils.addRegion(regionUtils._currentPoints[movingProtein], "region" + id, "moving");

	interfaceUtils.addSingleElementToSelect("select_region","region" + id);

	// Add trackings to the points so they ca move
	overlayUtils.addHandlersToNewTMCPS(id,"fixed");
	overlayUtils.addHandlersToNewTMCPS(id,"moving");

	regionUtils.resetManager();
}

regionUtils.removeRegionIdOverlay = function (id, overlay) {
	d3.select('.regionpolygr .' + "region" + id).selectAll("polygon").remove();
}

//remove in both viewers for one regiononly
regionUtils.removeRegionContent = function (regionid) {
	for(var v in regionUtils._regions){
		var regiongr = d3.select('.regionpolygr.' + regionid+"."+v)
		regiongr.selectAll("*").remove();
	}
}
regionUtils.removePoly = function (regionid, overlay) {
	d3.select(".regionpolygr" + "."+regionid + "."+overlay).selectAll("polygon").remove();
}

/** This used to be selection per overlay
 * when overlay and d3 group, but now one thing
 * is the viewer and another thing is the
 * abstraction of a protein group of regions.
 * Now overlay should be protein in some areas.
 */
regionUtils.getRegion = function (id, protein) {
	//check if the protein exists in the list of proteins, if not, then maybe
	//it can be that protein is actually asking for an overlay so look
	//for the protein that is in that viewer (fixed moving) and log it to console
	if(dataUtils._proteins.includes(protein)){
		//it is correctly asking for a protein
		return regionUtils._regions[protein]["region" + id.toString()];
	}else if(protein=="fixed" || protein=="moving"){
		//it is asking for the viewer, tsk, tsk, mistake, let's still help out
		var selectedprotein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
		console.log("regionUtils.getRegion is asking "+
		   "for an overlay instead of a protein"+". Attempting to choose the"+
		   "correct region.");
		return regionUtils._regions[selectedprotein]["region" + id.toString()];
	}else{
		console.log("Bad id for region");
		return null;
	}
	
}
regionUtils.getRegionByRID = function (regionid,protein) {
	//check if the protein exists in the list of proteins, if not, then maybe
	//it can be that protein is actually asking for an overlay so look
	//for the protein that is in that viewer (fixed moving) and log it to console
	if(dataUtils._proteins.includes(protein)){
		//it is correctly asking for a protein
		return regionUtils._regions[protein][regionid];
	}else if(protein=="fixed" || protein=="moving"){
		//it is asking for the viewer, tsk, tsk, mistake, let's still help out
		var selectedprotein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
		console.log("regionUtils.getRegion is asking "+
		   "for an overlay instead of a protein"+". Attempting to choose the"+
		   "correct region.");
		return regionUtils._regions[selectedprotein][regionid];
	}
	else{
		console.log("Bad region id");
		return null;
	}
}

regionUtils.getRegionByOverlay = function(regionid,overlay){
	var selectedprotein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
	return regionUtils._regions[selectedprotein][regionid];
}

regionUtils.getRegionByIDandOverlay = function(id,overlay){
	var selectedprotein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
	return regionUtils._regions[selectedprotein]["region"+id];
}

regionUtils.modifyRegion = function (points, id, overlay, protein) {

	if(points.len<3) console.log("Zero points, cant modify region");
	if (regionUtils._isNewRegion) {
		var region = regionUtils.getRegion(id, protein);
		//console.log("Region before strarting to modify ",region);
		//return null;
		region.points = []
		region.globalPoints = []
		var imageWidth = overlayUtils.OSDimageWidth(overlay);
		region.len = points.length;
		var _xmin = points[0][0], _xmax = points[0][0], _ymin = points[0][1], _ymax = points[0][1];
		var objectPointsArray = [];
		for (var i = 0; i < region.len; i++) {
			if (points[i][0] > _xmax) _xmax = points[i][0];
			if (points[i][0] < _xmin) _xmin = points[i][0];
			if (points[i][1] > _ymax) _ymax = points[i][1];
			if (points[i][1] < _ymin) _ymin = points[i][1];
			region.points.push({ "x": points[i][0], "y": points[i][1] });
			region.globalPoints.push({ "x": points[i][0] * imageWidth, "y": points[i][1] * imageWidth });
		}
		region._xmin = _xmin, region._xmax = _xmax, region._ymin = _ymin, region._ymax = _ymax;
		region._gxmin = _xmin * imageWidth, region._gxmax = _xmax * imageWidth, region._gymin = _ymin * imageWidth, region._gymax = _ymax * imageWidth;
		regionUtils._regions[protein]["region" + id] = region;
		//and in case I have a region UI add it
		//regionUtils.regionUI(regionid);
	} else {
		console.log("region is still under construction");
	}
}
regionUtils.importRegion = function (region, overlay){//, options) {
	//regionUtils._currentRegionId+=1;
	//region obejcts contain id,points,globalPoints,regionName,regionClass,color,len,_xmin,_xmax,_ymin,_ymax,_gxmin,_gxmax,_gymin,_gymax
	var canvas = tmcpoints[overlay + "_svgov"].node();
	var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
	
	//var id=regionUtils._currentRegionId;
	var id = region.id.match(/\d+/)[0];
	//if (Number(id) > regionUtils._currentRegionId) regionUtils._currentRegionId = Number(id);
	var imwidth = overlayUtils.OSDimageWidth(overlay);
	//create a group to store region
	var regiongr = d3.select(canvas).append('g')
		.attr('class', overlay + " " + "region" + id + " regionpolygr "+protein);

	//regionUtils._regions[protein]["region" + id] = region;
	var xmax = region.points[0].x, xmin = region.points[0].x, ymin = region.points[0].y, ymax = region.points[0].y;
	var svgpolygonformattedpoints = [];
	region.points.forEach(function (point) {
		svgpolygonformattedpoints.push([point.x, point.y]);
		if (point.x > xmax) xmax = Number(point.x);
		if (point.x < xmin) xmin = Number(point.x);
		if (point.y > ymax) ymax = Number(point.y);
		if (point.y < ymin) ymin = Number(point.y);
		markerUtils.TMCP(regiongr, {
			"extraClass": overlay+" "+protein + " regionp regionp-" + id,
			"x": point.x, "y": point.y, "strokeColor": region.color,
			"overlay": overlay, "regionIDNumber": id
		});
	});
	region._gxmax = xmax * imwidth; region._gxmin = xmin * imwidth; region._gymax = ymax * imwidth; region._gymin = ymin * imwidth;
	region._xmax = xmax; region._xmin = xmin; region._ymax = ymax; region._ymin = ymin;
	regiongr.append('polygon').attr('points', svgpolygonformattedpoints)
		.style('fill', 'none').style("stroke", region.color)
		.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
		.attr('class', "regionpoly regionpoly-" + id+" "+protein);

	// Add trackings to the points so they ca move
	overlayUtils.addHandlersToNewTMCPS(id,"fixed");
	overlayUtils.addHandlersToNewTMCPS(id,"moving");
	
}
regionUtils.regionsOnOff = function () {
	overlayUtils._drawRegions = !overlayUtils._drawRegions;
	if (overlayUtils._drawRegions) {
		document.getElementById('drawregions_btn').setAttribute("class", "btn btn-primary")
	} else {
		regionUtils.resetManager();
		document.getElementById('drawregions_btn').setAttribute("class", "btn btn-secondary")
	}
}
//if a region already exists you can re draw it
regionUtils.redrawRegion = function (regionid, overlay) {
	var regiongr = d3.select('.regionpolygr.' + regionid+"."+overlay);
	var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key; 
	
	regiongr.selectAll("*").remove();
	//extract number from regionid
	var id = regionid.replace(/\D/g, ''); id = id.toString();
	
	var region = regionUtils._regions[protein][regionid];
	//console.log(region);

	var svgpolygonformattedpoints = [];
	region.points.forEach(function (point) {
		svgpolygonformattedpoints.push([point.x, point.y]);
		//console.log(point);
		markerUtils.TMCP(regiongr, {
			"extraClass":overlay +" "+protein + " regionp regionp-" + id,
			"x": point.x, "y": point.y, "strokeColor": region.color,
			"overlay": overlay, "regionIDNumber": id
		});
	});

	regiongr.append('polygon').attr('points', svgpolygonformattedpoints)
		.style('fill', 'none').style("stroke", region.color)
		.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
		.attr('class', "regionpoly regionpoly-" + id);

	overlayUtils.addHandlersToNewTMCPS(id,overlay);
}
//regionid, x, y, bool global, string overlayid
regionUtils.moveregion = function (regionid, x, y, global, overlay) {

	if(!regionid.includes("region")){
		console.log("No region selected ("+regionid+")");
		return null;
	}

	var imwidth = overlayUtils.OSDimageWidth(overlay);
	var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key;                

	var region = regionUtils.getRegionByRID(regionid,protein);

	var points = [];
	var globalPoints = []
	if (!global) {
		region.points.forEach(function (elem) {
			var temp = elem;
			temp.x += x; temp.y += y;
			points.push(temp);
		});
		region.globalPoints.forEach(function (elem) {
			var temp = elem;
			elem.x += x * imwidth; elem.y += y * imwidth;
			globalPoints.push(temp);
		});
	} else {
		region.points.forEach(function (elem) {
			var temp = elem;
			elem.x += x / imwidth; elem.y += y / imwidth;
			points.push(temp);
		});
		region.globalPoints.forEach(function (elem) {
			var temp = elem;
			elem.x += x; elem.y += y;
			globalPoints.push(temp);
		});
	}
	var xmax = points[0].x, xmin = points[0].x, ymin = points[0].y, ymax = points[0].y;

	points.forEach(function (point) {
		if (point.x > xmax) xmax = Number(point.x);
		if (point.x < xmin) xmin = Number(point.x);
		if (point.y > ymax) ymax = Number(point.y);
		if (point.y < ymin) ymin = Number(point.y);
	});
	regionUtils._regions[protein][regionid]._gxmax = xmax * imwidth;
	regionUtils._regions[protein][regionid]._gxmin = xmin * imwidth;
	regionUtils._regions[protein][regionid]._gymax = ymax * imwidth;
	regionUtils._regions[protein][regionid]._gymin = ymin * imwidth;
	regionUtils._regions[protein][regionid]._xmax = xmax;
	regionUtils._regions[protein][regionid]._xmin = xmin;
	regionUtils._regions[protein][regionid]._ymax = ymax;
	regionUtils._regions[protein][regionid]._ymin = ymin;

	regionUtils._regions[protein][regionid].points = points;
	regionUtils._regions[protein][regionid].globalPoints = globalPoints;

	regionUtils.redrawRegion(regionid, overlay);

}

regionUtils.deleteRegion=function(regionid){
	for(var overlay in regionUtils._regions){
		regionUtils.removeRegionContent(regionid);
		delete regionUtils._regions[overlay][regionid];
	}
}

regionUtils.drawAllRegionsFromProtein=function(overlay){
	var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key;                
	overlayUtils.removeAllFromOverlay("moving");
    for(var r in regionUtils._regions[protein]){
        //there is a property that is not a region
        if(r.includes("region")){
			var region=regionUtils._regions[protein][r];
			//console.log("region.id: "+region.id);
			//This line should not fail if it is called
			//after having successfully loaded a tile
			//so that the world content can be called
            regionUtils.drawRegion(region.id, overlay);
        }
	}
	//overlayUtils.addHandlersToNewTMCPS(id,overlay);
}

regionUtils.drawRegion=function(regionid,overlay){
	var canvas = tmcpoints[overlay+"_svgov"].node();
	var protein=interfaceUtils.getSelectedIndexValue("select_protein_"+overlay).key;                
	regionUtils._regionD3Groups[overlay] = d3.select(canvas)
		.append('g')
		.attr('class', overlay+" regionpolygr "+regionid +" "+protein);
	regiongr = regionUtils._regionD3Groups[overlay];
	var region = regionUtils._regions[protein][regionid];
	//console.log(region);
	var id = regionid.replace(/\D/g, ''); id = id.toString();

	var svgpolygonformattedpoints = [];
	region.points.forEach(function (point) {
		svgpolygonformattedpoints.push([point.x, point.y]);
		//console.log(point);
		markerUtils.TMCP(regiongr, {
			"extraClass":overlay +" "+protein + " regionp regionp-" + id,
			"x": point.x, "y": point.y, "strokeColor": region.color,
			"overlay": overlay, "regionIDNumber": id
		});
	});

	regiongr.append('polygon').attr('points', svgpolygonformattedpoints)
		.style('fill', 'none').style("stroke", region.color)
		.attr('stroke-width', regionUtils._polygonStrokeWidth.toString())
		.attr('class', "regionpoly regionpoly-" + id);

	overlayUtils.addHandlersToNewTMCPS(id,overlay);

}
