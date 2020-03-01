var tmcpoints = {
    url_prefix:"https://tissuumaps.research.it.uu.se/",
    //url_prefix: "file:///home/leslie/Documents/Uppsala/portugalDataset/carla/",
    //fixed_file:  "images/portugal/CAIslands/vips.dzi",
    //moving_file: "images/portugal/combCA/vips.dzi",
    fixed_viewer: null,
    moving_viewer: null,
    fixed: null,
    moving: null,
    fixed_image_width: 0,
    moving_image_width: 0
}
//This function is called when the document is loaded. the tmcpoints object is built as an "app" and init is its main function 

tmcpoints.init = function (options) {
    var possibleurlprefix=interfaceUtils.getValueFromDOM("url_prefix");
    if(possibleurlprefix){
        tmcpoints.url_prefix=possibleurlprefix;
    }
    interfaceUtils.emptyViewers({});
    
    //OSD viewer for the fixed image
    var fixed_viewer;
    //OSD viewer for the moving image
    var moving_viewer;

    //Initialize OSD with options (Options are written at the end of this file)
    fixed_viewer = OpenSeadragon(tmcpoints.options_fixed);
    tmcpoints.fixed_viewer = fixed_viewer;
    tmcpoints.fixed_viewer.addHandler("open",function(){
        regionUtils.drawAllRegionsFromProtein("fixed");
    });

    //Do the same for moving images
    moving_viewer = OpenSeadragon(tmcpoints.options_moving);
    tmcpoints.moving_viewer = moving_viewer;
    tmcpoints.moving_viewer.addHandler("open",function(){
        regionUtils.drawAllRegionsFromProtein("moving");
    })

    if (tmcpoints.fixed_file == null || tmcpoints.moving_file == null) {
        console.log("Chose dzi files to open");
    }else{
        interfaceUtils.openDZI(tmcpoints.fixed_file,"fixed");
        interfaceUtils.openDZI(tmcpoints.moving_file,"moving");
    }


    tmcpoints.fixed_svgov = tmcpoints.fixed_viewer.svgOverlay();
    tmcpoints.moving_svgov = tmcpoints.moving_viewer.svgOverlay();

    tmcpoints.fixed_singleTMCPS = d3.select(tmcpoints.fixed_svgov.node()).append('g').attr('class', "fixed singleTMCPS");
    tmcpoints.moving_singleTMCPS = d3.select(tmcpoints.moving_svgov.node()).append('g').attr('class', "moving singleTMCPS");

    //This is the OSD click handler, when the event is quick it triggers the creation of an icon
    var click_handler = function (event) {
        if (event.quick) {
            if (!overlayUtils._drawRegions) {
                //overlayUtils.addTMCPtoViewers(event);
                console.log("Drawing points is temporarily disabled. Only regions can be drawn");
            } else {
                //call region creator and drawer
                //the viewer is that to whićh the click hanlder is added
                //so every veiwer will have a regionutils manager...
                //This is bound to this.fixed_viewer.canvas
                regionUtils.manager(event);
                //console.log("draw regions");
            }
        } else {
            //if it is not quick then it is dragged
            if (document.getElementById("syncpan").checked) {
                var f_center = fixed_viewer.viewport.getCenter();
                moving_viewer.viewport.panTo(f_center, true);
                //console.log("else");
            }
        }
    };

    var scaleZoom_handler = function (event) {
        if (document.getElementById("synczoom").checked) {
            var fixed_zoom = fixed_viewer.viewport.getZoom();
            moving_viewer.viewport.zoomTo(fixed_zoom, null, true);
            click_handler(event);
        }
    };

    //OSD handlers are not registered manually they have to be registered
    //using MouseTracker OSD objects 
    var fixed_mouse_tracker = new OpenSeadragon.MouseTracker({
        //element: this.fixed_svgov.node().parentNode, 
        element: this.fixed_viewer.canvas,
        clickHandler: click_handler,
        scrollHandler: scaleZoom_handler
    }).setTracking(true);

    //Assign the function to the button in the document (this will be done dynamically)
    interfaceUtils.listen("pointstojson","click",JSONUtils.downloadJSON);
    //document.getElementById('pointstojson').addEventListener('click', JSONUtils.downloadJSON);
    //Function to button
    //document.getElementById('jsontopoints').addEventListener('click', JSONUtils.importPointsFromJSON);
    interfaceUtils.listen("jsontodata","click", JSONUtils.readJSONToData);
    interfaceUtils.listen("drawregions_btn","click",regionUtils.regionsOnOff);
    interfaceUtils.listen("btn_mrup","click",function () { overlayUtils.moveSelectedRegion("up") });
    interfaceUtils.listen("btn_mrleft","click",function () { overlayUtils.moveSelectedRegion("left") });
    interfaceUtils.listen("btn_mrright","click",function () { overlayUtils.moveSelectedRegion("right") });
    interfaceUtils.listen("btn_mrdown","click",function () { overlayUtils.moveSelectedRegion("down") });
    interfaceUtils.listen("btn_region_delete","click",function () { overlayUtils.removeRegion() });

    interfaceUtils.disableElement("select_case_fixed");
    interfaceUtils.disableElement("select_block_fixed");
    interfaceUtils.disableElement("select_protein_fixed"); 
    interfaceUtils.disableElement("select_protein_moving"); 

}//finish init
//options for the fixed and moving OSD 
//https://openseadragon.github.io/docs/OpenSeadragon.html#.Options
tmcpoints.options_fixed = {
    id: "fixed_viewer",
    prefixUrl: "js/openseadragon/images/",
    navigatorSizeRatio: 1,
    wrapHorizontal: false,
    showNavigator: false,
    navigatorPosition: "BOTTOM_LEFT",
    navigatorSizeRatio: 0.25,
    animationTime: 0.0,
    blendTime: 0,
    minZoomImageRatio: 1,
    maxZoomPixelRatio: 1,
    zoomPerClick: 1.0,
    constrainDuringPan: true,
    visibilityRatio: 1
}
tmcpoints.options_moving = {
    id: "moving_viewer",
    prefixUrl: "js/openseadragon/images/",
    navigatorSizeRatio: 1,
    wrapHorizontal: false,
    showNavigator: false,
    navigatorPosition: "BOTTOM_LEFT",
    navigatorSizeRatio: 0.25,
    animationTime: 0.0,
    blendTime: 0,
    minZoomImageRatio: 1,
    maxZoomPixelRatio: 1,
    zoomPerClick: 1.0,
    constrainDuringPan: true,
    visibilityRatio: 1
}

