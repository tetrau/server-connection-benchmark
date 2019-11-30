import * as d3 from "d3";


function scaleCenterFactory(scale) {
    return function (d) {
        return scale(d) + scale.bandwidth() / 2;
    }
}

function scaleEndFactory(scale) {
    return function (d) {
        return scale(d) + scale.bandwidth();
    }
}

function scaleYFactory(step, paddingInner, domain) {
    function scaleY(d) {
        let index = domain.indexOf(d);
        return index * step;
    }
    scaleY.bandwidth = () => step * paddingInner;
    scaleY.step = () => step;
    return scaleY
}

function drawBarMatrix(data, primaryDataSelector, secondaryDataSelector, xSelector, ySelector, scaleX, scaleY, paddingX, paddingY) {
    let scaleYEnd = scaleEndFactory(scaleY);
    let rects = d3.select("svg").selectAll("rect.bar").data(data)

    rects.enter().append("rect").merge(rects).attr("width", scaleX.bandwidth())
        .attr("class", "bar")
        .attr("x", d => scaleX(xSelector(d)) + paddingX)
        .attr("height", d => scaleY.bandwidth() * primaryDataSelector(d))
        .attr("y", d => scaleYEnd(ySelector(d)) - scaleY.bandwidth() * primaryDataSelector(d) + paddingY)
        .attr("fill", d => d3.interpolateViridis(secondaryDataSelector(d)));;

}

function drawXAxis(xDomain, scaleX, paddingX, paddingY) {
    let scaleXCenter = scaleCenterFactory(scaleX);
    let xs = d3.select("svg").selectAll("text.x").data(xDomain)

    xs.enter().append("text").merge(xs)
        .attr("class", "x")
        .attr("x", d => scaleXCenter(d) + paddingX)
        .attr("y", paddingY)
        .attr("text-ancher", "start")
        .style("font", "12px sans-serif")
        .attr("transform", d => `rotate(${-45}, ${scaleXCenter(d) + paddingX}, ${paddingY})`)
        .text(d => d)
}

function drawYAxis(yDomain, scaleY, paddingX, paddingY) {
    let scaleYEnd = scaleCenterFactory(scaleY);
    let ys = d3.select("svg").selectAll("text.y").data(yDomain)

    ys.enter().append("text").merge(ys)
        .attr("class", "y")
        .attr("x", paddingX)
        .attr("y", d => scaleYEnd(d) + paddingY + 6)
        .attr("text-ancher", "start")
        .style("font", "12px sans-serif")
        .text(d => d)
}

function formatTime(t) {
    let d = new Date(t * 1000);
    let h = d.getHours();
    let m = d.getMinutes();
    return h.toString().padStart(2, "0") + ":" + m.toString().padStart(2, "0");
}

function groupBy(array, key) {
    let o = {}
    for (let i of array) {
        let k = key(i)
        if (k in o) {
            o[k].push(i)
        } else {
            o[k] = [i]
        }
    }
    return o;
}

function parseReport(report, accumulator) {
    let nameArray = report[0].result.map(x => x.vendor + ": " + x.location);
    let result = report.flatMap(s => {
        return s.result.map(x => { return { ...x, time: s.time } })
    })
    let groupedResult = groupBy(result, r => JSON.stringify([r.vendor, r.location, formatTime(r.time)]))
    let accumulatedResult = Object.values(groupedResult).map(accumulator);
    let timeArray = Array.from(new Set(accumulatedResult.map(r => formatTime(r.time)))).sort();
    return {
        "result": accumulatedResult,
        "timeArray": timeArray,
        "nameArray": nameArray
    }
}

function accumulatorFactory(accu) {
    return function (reports) {
        let time = reports[0].time;
        let vendor = reports[0].vendor;
        let location = reports[0].location;
        let latency = accu(reports.map(x => x.latency));
        let bandwidth = accu(reports.map(x => x.bandwidth));
        let packetLoss = accu(reports.map(x => x.packetLoss));
        return { time, vendor, location, latency, bandwidth, packetLoss }
    }
}

function draw4DPlot(xDomain, yDomain, data, primaryDataSelector, secondaryDataSelector, xSelector, ySelector) {
    let scaleX = d3.scaleBand(xDomain, [0, 780])
        .paddingInner(0.1);
    if (scaleX.bandwidth() > 20) {
        scaleX = scaleYFactory(20, 0.9, xDomain);
    }
    let scaleY = scaleYFactory(scaleX.bandwidth() * 2.25, 0.9, yDomain);

    drawXAxis(xDomain, scaleX, 160, 30);
    drawBarMatrix(data, primaryDataSelector, secondaryDataSelector, xSelector, ySelector, scaleX, scaleY, 160, 30);
    drawYAxis(yDomain, scaleY, 0, 30);
}

function maxInArray(dataArray, selector) {
    return d3.max(dataArray.map(selector));
}

function normalizedSelector(dataArray, selector) {
    let maxValue = maxInArray(dataArray, selector);
    let scale = d3.scaleLinear().domain([0, maxValue]);
    let f = x => scale(selector(x))
    f.scale = scale;
    return f;
}

function draw(rData) {
    let config = getConfigFromControlPanel();
    let accumulators = {
        average: accumulatorFactory(d3.mean),
        max: accumulatorFactory(d3.max),
        min: accumulatorFactory(d3.min)
    }
    let accumulator = accumulators[config.accumulator]
    let parsedData = parseReport(rData, accumulator);
    let xDomain = parsedData.timeArray;
    let yDomain = parsedData.nameArray;
    let data = parsedData.result;
    let bandwidthSelector = normalizedSelector(data, x => x.bandwidth);
    let latencySelector = normalizedSelector(data, x => x.latency);
    let packetLossSelector = x => x.packetLoss;
    packetLossSelector.scale = d3.scaleLinear();
    let selectors = {
        bandwidth: bandwidthSelector,
        latency: latencySelector,
        packetLoss: packetLossSelector
    }
    let primaryDataSelector = selectors[config.primaryDataSelector];
    let secondaryDataSelector = selectors[config.secondaryDataSelector];
    let timeSelector = x => formatTime(x.time);
    let nameSelector = x => x.vendor + ": " + x.location
    let scale = secondaryDataSelector.scale;
    drawLegendAxis(scale, 980, 50);
    draw4DPlot(xDomain, yDomain, data, primaryDataSelector, secondaryDataSelector, timeSelector, nameSelector)
}

function createControlPanel(drawPlot) {
    let selectors = ["bandwidth", "latency", "packetLoss"];
    let controlPanel = d3.select("div#control-panel-1");
    function createInput(message, className, select, candidates) {
        let controlPanelDiv = controlPanel.append("div");
        controlPanelDiv.append("label")
            .attr("for", className)
            .text(message)
            .style("font-family", "sans-serif");
        let controlPanelSelect = controlPanelDiv.append("select").attr("id", className);
        for (let s of candidates) {
            let i = controlPanelSelect.append("option")
                .attr("name", className)
                .attr("class", className)
                .attr("id", className + "-" + s)
                .attr("value", s)
                .style("font-family", "sans-serif")
                .text(s)
            if (s === select) {
                i.property('selected', true);
            }
        }
        controlPanelSelect.on("change", drawPlot)
    }

    createInput("Select Primary Value Field (Visualized by the Height of Bar): ", "primaryDataSelector", "bandwidth", selectors)
    createInput("Select Secondary Value Field (Visualized by the Color of Bar): ", "secondaryDataSelector", "latency", selectors)
    createInput("Select Accumulating Function: ", "accumulator", "average", ["average", "max", "min"])
}

function getConfigFromControlPanel() {
    let primaryDataSelector = d3.select("option.primaryDataSelector:checked").property("value");
    let secondaryDataSelector = d3.select("option.secondaryDataSelector:checked").property("value");
    let accumulator = d3.select("option.accumulator:checked").property("value");
    return { primaryDataSelector, secondaryDataSelector, accumulator }
}

function drawLegend(x, y, width, height) {
    var gradient = d3.select("svg").append('defs')
        .append('linearGradient')
        .attr('id', 'gradient')
        .attr('x1', '0%')
        .attr('y1', '100%')
        .attr('x2', '0%')
        .attr('y2', '0%')
        .attr('spreadMethod', 'pad');
    var stopCount = 100;
    var gradientData = [...Array(stopCount + 1).keys()].map(i => ({
        offset: Math.round((i / stopCount) * 100) + '%',
        color: d3.interpolateViridis(i / stopCount)
    }));
    gradientData.forEach(d =>
        gradient
            .append("stop")
            .attr('offset', d.offset)
            .attr('stop-color', d.color)
            .attr('stop-opacity', 1));

    d3.select("svg").append("rect")
        .attr("class", "legend")
        .attr("height", height)
        .attr("width", width)
        .attr("x", x)
        .attr("y", y)
        .style('fill', 'url(#gradient)');
}

function drawLegendAxis(scale, x, y) {
    scale = scale.copy().range([199, 0])
    d3.selectAll("g.legend-axis").remove()
    d3.select("svg")
        .append("g")
        .attr("class", "legend-axis")
        .attr("transform", `translate(${x}, ${y})`)
        .call(d3.axisRight(scale))
}


function drawAll(rData) {
    d3.select("body").append("svg").attr("height", 2000).attr("width", 1080);
    let drawPlot = () => draw(rData)
    createControlPanel(drawPlot);
    drawLegend(960, 50, 20, 200);
    drawPlot();
}

drawAll(data);