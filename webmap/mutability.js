// z31 JS

//colors
function getColorarray(d, distribution) {
    return d > distribution[6] ? '#800026' :
        d > distribution[5]  ? '#BD0026' :
        d > distribution[4]   ? '#E31A1C' :
        d > distribution[3]  ? '#FC4E2A' :
        d > distribution[2]   ? '#FD8D3C' :
        d > distribution[1]   ? '#FEB24C' :
        d > distribution[0]   ? '#FED976' :
                            '#9002d0'; 
}

//breaks function
function calculateEqualIntervals(values, numClasses) 
{
    // Step 1: Find the minimum and maximum values in the data
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);

    // Step 2: Calculate the range of the data
    const range = maxValue - minValue;

    // Step 3: Calculate the size of each interval
    const intervalSize = range / numClasses;

    // Step 4: Initialize an array to store the class breaks
    const classBreaks = [];

    // Step 5: Calculate the class breaks
    for (let i = 0; i <= numClasses; i++) {
        const classBreak = minValue + i * intervalSize;
        classBreaks.push(classBreak);
    }

    return classBreaks;
}

//GeoJSON response
var data_response = $.ajax({//warning : data crs must be EPSG:4326
    url:"data/parc_amc3.geojson",
    dataType: "json",
    success: console.log("Parcels successfully found!"),
    error: function (xhr) {
        alert(xhr.statusText)
    }
})

//specify that this code should run once the parcels data request is complete
$.when(data_response).done(function() {

    //breaks choroplethe
    let values = data_response.responseJSON.features.map(feature => feature.properties['i_multi_crit']);
    console.log("i_multi_crit", values);
    
    //Apply equal fonction
    let EqualInt = calculateEqualIntervals(values, 7)
    console.log("EqualIntervals", EqualInt);

    function style(feature) // param EqualInt ?
    {
        return {
            fillColor: getColorarray(feature.properties.i_multi_crit,EqualInt),//EqualInt),breaks_jenks),
            weight: 2,
            opacity: 0.2,
            color: 'white',
            //dashArray: '3',
            fillOpacity: 0.7
        };
    }
    
    //interactions functions
    function highlightFeature(e) {
        var layer = e.target;

        layer.setStyle({
            weight: 5,
            color: '#666',
            dashArray: '',
            fillOpacity: 0.7
        });

        layer.bringToFront();
        info.update(layer.feature.properties);
    }

    function resetHighlight(e) {
        parcels_f.resetStyle(e.target);
        info.update();
    }

    function zoomToFeature(e) {
        map.fitBounds(e.target.getBounds());
    }

    function onEachFeature(feature, layer) {
        layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlight,
            click: zoomToFeature
        });
    }

    //map var
    const map = L.map('map', {
        center:[43.6013, 1.4447],//Toulouse
        zoom:14,
        //layers:[osm]
    });

    //base maps
    var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        minZoom: 8,
        maxZoom: 25,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });

    var Esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        minZoom: 8,
        maxZoom: 25,
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });
    
    osm.addTo(map)

    //layers
    var area_filter = 3000;
    
    var parcels_f = L.geoJSON(data_response.responseJSON,{
        style: style,
        onEachFeature: onEachFeature
    }).addTo(map);

    map.fitBounds(parcels_f.getBounds());

    console.log("Parcels loaded", parcels.responseJSON);

    var parcels_filt_response = geotoolbox.filter(parcels.responseJSON, (d) => d.area > area_filter);
    console.log("Area filter applied", parcels_filt_response);

    var parcels_fil = L.geoJSON(parcels_filt_response).addTo(map);

    var baseMaps = {
        'OpenStreetMap': osm,
        'Satellite': Esri_WorldImagery
    };

    var overlayMaps = {
        'Parcels': parcels_f
    };

    L.control.layers(baseMaps, overlayMaps).addTo(map);

    //legend
    var legend = L.control({position: 'bottomright'});

        legend.onAdd = function (map) {

        var div = L.DomUtil.create('div', 'info legend'),
            grades = EqualInt,
            labels = [];

        // loop through our density intervals and generate a label with a colored square for each interval
        for (var i = 0; i < grades.length; i++) {
            div.innerHTML +=
                '<i style="background:' + getColorarray(grades[i] + 0.0001,EqualInt) + '"></i> ' + // so that d is not == EqualInt to respect function
                (Math.floor(grades[i ]*100)/100) + ((Math.floor(grades[i + 1]*100)/100) ? ' &ndash; ' + (Math.floor(grades[i + 1]*100)/100) + '<br>' : ' et +');
        }

        return div;
    };

    console.log("Legend loaded", legend);

    legend.addTo(map);

    //scale
    L.control.scale().addTo(map);

    //interactions
    var info = L.control();

    info.onAdd = function (map) {
        this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
        this.update();
        return this._div;
    };

    info.update = function (parcels_f) {// method that we will use to update the control based on feature properties passed
        this._div.innerHTML = '<h4>Propriétés de la parcelle</h4>' +  (parcels_f ?
            '<b>' + (Math.round(parcels_f.i_multi_crit*1000)/1000) + '</b><br />' + parcels_f.area + ' area m<sup>2</sup>'
            : 'Survoler une parcelle');
    };

    info.addTo(map);

    //var parcels_filt = geo.filter(parcels_f, (d) => d.area > area_filter);
});            

