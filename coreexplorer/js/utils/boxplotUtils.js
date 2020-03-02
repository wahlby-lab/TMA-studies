boxplotUtils = {
    // set the dimensions and margins of the graph
    margin: { top: 10, right: 10, bottom: 50, left: 25 },
    width: 600 - 25 - 10, // width = 460 - margin.left - margin.right,
    height: 580 - 10 - 50, //    height = 400 - margin.top - margin.bottom;
    sumstat: null,
    padx:{in:0,out:20},
    pady:{in:0,out:10}
}

boxplotUtils.createview = function (blockkey) {
    dataUtils.fillSymbols();
    //first find the index in array that contains the right information
    var index = 0;
    var use = 0;
    var theentries= [];
    var colorbyslide=true;
    //console.log(index,use);
    if(blockkey){
        dataUtils._nest.forEach(block => {
            if (block.key == blockkey) {
                use = index;
            } else { index += 1; }
        });
        var colorbyslide=false;
        theentries=dataUtils._nest[use].values;
    }else{
        //if there is no key means use all the values, possibly color them by slide and not by degree
        theentries=dataUtils._rawdata

    }

    d3.select("#tm_boxplot").html("");
    var svg = d3.select("#tm_boxplot")
        .append("svg")
        .attr("width", boxplotUtils.width + boxplotUtils.margin.left + boxplotUtils.margin.right)
        .attr("height", boxplotUtils.height + boxplotUtils.margin.top + boxplotUtils.margin.bottom)
        .append("g")
        .attr("transform",
            "translate(" + boxplotUtils.margin.left + "," + boxplotUtils.margin.top + ")");
    // Compute quartiles, median, inter quantile range min and max --> these info are then used to draw the box.
    boxplotUtils.sumstat = d3.nest() // nest function allows to group the calculation per level of a factor
        .key(function (d) { return d[dataUtils._symbols.p1p]; })
        .rollup(function (d) {
            var gkey = dataUtils._symbols.p1q;
            q1 = d3.quantile(d.map(function (g) { return g[gkey]; }).sort(d3.ascending), .25);
            median = d3.quantile(d.map(function (g) { return g[gkey]; }).sort(d3.ascending), .5);
            q3 = d3.quantile(d.map(function (g) { return g[gkey]; }).sort(d3.ascending), .75);
            interQuantileRange = q3 - q1;
            min = q1 - 1.5 * interQuantileRange; if (min < 0) min = 0;
            max = q3 + 1.5 * interQuantileRange;
            return ({ q1: q1, median: median, q3: q3, interQuantileRange: interQuantileRange, min: min, max: max })
        })
        .entries(theentries)

    // Show the Y scale
    var y = d3.scaleBand()
        .range([boxplotUtils.height, 0])
        .domain(["0", "1", "2", "3"])
        .padding(0.3)
        
    svg.append("g")
        .call(d3.axisLeft(y).tickSize(0))
        .select(".domain").remove()

    // Show the X scale
    var x = d3.scaleLinear()
        .domain([0.0, 105.0])
        .range([0, boxplotUtils.width])
        
    svg.append("g")
        .attr("transform", "translate("+boxplotUtils.padx.out+"," + boxplotUtils.height + ")")
        .call(d3.axisBottom(x).ticks(6))
        .select(".domain").remove()


        var vertlines=[];
        var str=document.getElementById("vertlines").value;
        str.split(",").forEach(line => {
            if(line)
                vertlines.push({x:Number(line)})
        })
    
        svg
            .selectAll("verticalLines")
            .data(vertlines)
            .enter()
            .append("line")
            .attr("x1", function (d) { return (x(d.x))+boxplotUtils.padx.out })
            .attr("x2", function (d) { return (x(d.x))+boxplotUtils.padx.out })
            .attr("y1", function (d) { return  y.bandwidth() / 4 })
            .attr("y2", function (d) { return (boxplotUtils.height- y.bandwidth() / 4) })
            .attr("stroke", "black")
            .style("width", 40)
    

    // Color scale
    var myColor = d3.scaleSequential()
        .interpolator(d3.interpolatePlasma)
        .domain([0.0, 100.0])
    var myFeature=dataUtils._symbols.p1q;

    if(colorbyslide){
        myColor = d3.scaleOrdinal(d3.schemeCategory10)
        .domain([0.0, dataUtils._nest.length])
        myFeature=dataUtils._symbols.block;
    }

    // Add X axis label:
    svg.append("text")
        .attr("text-anchor", "end")
        .attr("x", boxplotUtils.width-boxplotUtils.padx.out)
        .attr("y", boxplotUtils.height + boxplotUtils.margin.top + 30)
        .text("Percentage of CD44v6 in tumor");

    // Show the main horizontal line
    svg
        .selectAll("horizontalLines")
        .data(boxplotUtils.sumstat)
        .enter()
        .append("line")
        .attr("x1", function (d) { return (x(d.value.min))+boxplotUtils.padx.out })
        .attr("x2", function (d) { return (x(d.value.max))+boxplotUtils.padx.out })
        .attr("y1", function (d) { return (y(d.key) + y.bandwidth() / 2) })
        .attr("y2", function (d) { return (y(d.key) + y.bandwidth() / 2) })
        .attr("stroke", "black")
        .style("width", 40)

    // rectangle for the main box
    svg
        .selectAll("boxes")
        .data(boxplotUtils.sumstat)
        .enter()
        .append("rect")
        .attr("x", function (d) { return (x(d.value.q1)+boxplotUtils.padx.out) }) // console.log(x(d.value.q1)) ;
        .attr("width", function (d) { ; return (x(d.value.q3) - x(d.value.q1)+boxplotUtils.padx.out) }) //console.log(x(d.value.q3)-x(d.value.q1))
        .attr("y", function (d) { return y(Number(d.key)); })
        .attr("height", y.bandwidth())
        .attr("stroke", "black")
        .style("fill", "#69b3a2")
        .style("opacity", 0.3)

    // Show the median
    svg
        .selectAll("medianLines")
        .data(boxplotUtils.sumstat)
        .enter()
        .append("line")
        .attr("y1", function (d) { return (y(d.key) + y.bandwidth() / 2) })
        .attr("y2", function (d) { return (y(d.key) + y.bandwidth() / 2) })
        .attr("x1", function (d) { return (x(d.value.median)+boxplotUtils.padx.out) })
        .attr("x2", function (d) { return (x(d.value.median)+boxplotUtils.padx.out) })
        .attr("stroke", "black")
        .style("width", 80)

    // create a tooltip
    var tooltip = d3.select("#tm_boxplot")
        .append("div")
        .style("opacity", 0)
        .attr("class", "tooltip")
        .style("font-size", "16px")
    // Three function that change the tooltip when user hover / move / leave a cell
    var mouseover = function (d) {
        var moveup=0;
        if(d[dataUtils._symbols.p1p]==0) moveup=25;
        tooltip
            .transition()
            .duration(200)
            .style("opacity", 1)
        tooltip
            .html("<span style='color:grey'> </span>B:" + d[dataUtils._symbols.block]
                +"<br>"+d[dataUtils._symbols.id]
                +"<br>"+d[dataUtils._symbols.p1q]) // + d.Prior_disorder + "<br>" + "HR: " +  d.HR)
            .style("left", (d3.mouse(this)[0] + 30+boxplotUtils.padx.out) + "px")
            .style("top", (d3.mouse(this)[1] + 30-moveup) + "px")
    }
    var mousemove = function (d) {
        var moveup=0;
        if(d[dataUtils._symbols.p1p]==0) moveup=25;
        tooltip
            .style("left", (d3.mouse(this)[0] + 30+boxplotUtils.padx.out) + "px")
            .style("top", (d3.mouse(this)[1] + 30-moveup) + "px")
    }
    var mouseleave = function (d) {
        tooltip
            .transition()
            .duration(200)
            .style("opacity", 0)
    }

    // Add individual points with jitter    
    var jitterWidth = 60;

    var imshow=function(d,blockkey){
        if(!blockkey){
            index=0;
            use=0;
            blockkey=d[dataUtils._symbols.block];
            dataUtils._nest.forEach(block => {
                if (block.key == blockkey) {
                    use = index;
                } else { index += 1; }
            });
            dataUtils.showImages(use, d[dataUtils._symbols.id]);
        }
        else{
            dataUtils.showImages(use, d[dataUtils._symbols.id]);
        }
    }
    

    svg
        .selectAll("indPoints")
        .data(theentries)
        .enter()
        .append("circle")
        .attr("cx", function (d) { return (x(d[dataUtils._symbols.p1q])+boxplotUtils.padx.out) })
        .attr("cy", function (d) { return (y(d[dataUtils._symbols.p1p]) + (y.bandwidth() / 2) - jitterWidth / 2 + Math.random() * jitterWidth) })
        .attr("r", 4)
        .style("fill", function (d) { return (myColor(d[myFeature])) })
        .attr("stroke", "black")
        .on("mouseover", mouseover)
        .on("mousemove", mousemove)
        .on("mouseleave", mouseleave)
        .on("click", function (d) { imshow(d,blockkey) });


}
