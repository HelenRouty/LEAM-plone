// Define simmap namespace using a "module pattern" (essentially an
// anonymous closure) as demonstrated on 
// http://javascriptweblog.wordpress.com/2010/12/07/namespacing-in-javascript/
// 
// jQuery and Openlayers libraries are imported directly rather than 
// referencing them as implied globals.
var simmap = (function(jq, ol) {
    var layers = {};
    var olmap;

    return {
        init: function() {

            ol.ImgPath = "++resource++ol_images/";

            var options = {
                projection: "EPSG:3857",
                theme: null,
                //allOverlays: true,
                };
            olmap = new ol.Map('map', options);
            olmap.addControl(new ol.Control.LayerSwitcher());
            olmap.events.register('changelayer', null, function(evt) {

                // should update the legend here
                if (evt.property === "visibility") {
                    var dummy = 0;
                    //alert(evt.layer.map + " visibility changed");
                }
            });

            var blayer = new ol.Layer.Google("Google Map",
                { sphericalMercator: true,
                  displayInLayerSwitcher: true,
                });
            olmap.addLayer(blayer);

            // ywkim added for google street map
            var blayer2 = new ol.Layer.Google("Google Hybrid",
                { type: google.maps.MapTypeId.HYBRID,
                  sphericalMercator: true,
                  displayInLayerSwitcher: true,
                });
            olmap.addLayer(blayer2)

            //var osm = new ol.Layer.OSM("Simple OSM");

            // get list of all layers specified
            //  -- current  assumes that all layers are visible
            //  -- centering is done on first (prime) map
            jq('.map-url').each(function(idx) {
                var url = jq(this).html();
                if (idx === 0) {
                    var prime = url;
                }
                if (!(url in layers)) {
                    layers[url] = "";
                    jq.getJSON(
                        url + '/getMapMeta',
                        function(data) {
                            layers[url] = data;
                            simmap.addLayer(url, false);
                            if (url === prime) {
                                simmap.setVis(url, true)
                                simmap.centerOnLayer(url);
                            }
                        }
                    );
                }
            });

            // add any layers from the navigation portlet
            // NOTE: should this be optional based on site? on the simmap?
            // NOTE: check for layers that are in the current directory
            jq('.navTreeItem .contenttype-simmap').each(function() {
                var url = jq(this).attr('href');
                if (!(url in layers))  {
                    layers[url] = "";
                    jq.getJSON(
                        url+'/getMapMeta',
                        function(data) {
                            layers[url] = data;
                            simmap.addLayer(url, false);
                        }
                    );
                }
            });
        },

        addLayer: function(url, vis) {
            layers[url].olLayer = new ol.Layer.WMS(
                layers[url].title,
                layers[url].mapserve,
                { "map": layers[url].mappath,
                  "sphericalMercator": true,
                  "transparent": true,
                  "format": "image/png",
                  "layers": "final4",
                },
                { "isBaseLayer": false,
                  "opacity": layers[url].transparency,
                  "visibility": vis,
                }
            );
            olmap.addLayer(layers[url].olLayer);
        },

        // basic methods for controlling layer visibility
        setVis: function(url, vis) {
            layers[url].olLayer.setVisibility(vis);
        },

        toggleVis: function(url) {
            l = layers[url].olLayer;
            if (l.visibility) {
                l.setVisibility(false); }
            else {
                l.setVisibility(true);
            }
        },

        // centers the map on the specified layer
        centerOnLayer: function(url) {
            var ll = layers[url].latlong.split(' ')
            olmap.setCenter(new ol.LonLat(ll[1],ll[0]).transform(
               new ol.Projection("EPSG:4326"),
               olmap.getProjectionObject()), layers[url].zoom);    
        },

        // OLDER CODE BELOW

        enableOverlay: function(mapName, rawmarks, trans) {
          
            // Add Markers
            var markers=rawmarks.split('|');
            var arrCount = 0;
            var maCount = 1;
        
            addLegend(mapName);

        },

        addLegend: function(mapName)  {

            try {
                var mapDiv = document.getElementById(mapName).innerHTML;
            }

            catch(err) { 
                mapDiv = "<div id=\"" +mapName + "\">";
                var oldHTML = document.getElementById('legend').innerHTML;
                var wholeHTML = oldHTML + mapDiv;
                document.getElementById('legend').innerHTML = wholeHTML;
            }
        
            finally {
                var imgHTML = "<img src=\""+mapserver+"?SERVICE=WMS&VERSION=1.1.1&layer=final4&REQUEST=getlegendgraphic&FORMAT=image/png&map="+mapName+"\">";
                document.getElementById(mapName).innerHTML = imgHTML;
            }
        },

        removeLegend: function(mapName) {
            document.getElementById(mapName).innerHTML = " ";
        },
    };
})(jQuery, OpenLayers);


