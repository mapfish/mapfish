
/*
 * @include OpenLayers/Map.js
 * @include OpenLayers/Projection.js
 * @include OpenLayers/Layer/XYZ.js
 * @include OpenLayers/Tile/Image.js
 * @include OpenLayers/Protocol/HTTP.js
 * @include OpenLayers/Request/XMLHttpRequest.js
 * @include OpenLayers/Control/Navigation.js
 * @include OpenLayers/Control/ZoomBox.js
 * @include OpenLayers/Control/NavigationHistory.js
 * @include OpenLayers/Control/GetFeature.js
 * @include OpenLayers/Format/GeoJSON.js
 * @include GeoExt/data/LayerStore.js
 * @include GeoExt/widgets/MapPanel.js
 * @include GeoExt/widgets/Action.js
 * @include GeoExt/widgets/ZoomSlider.js
 * @include GeoExt/widgets/tips/ZoomSliderTip.js
 * @include GeoExt/widgets/tree/LayerContainer.js
 * @include GeoExt/widgets/Popup.js
 */

Ext.namespace("App");

App.layout = (function() {
    /*
     * Private
     */

    /**
     * Method: createMap
     * Create the map.
     *
     * Returns:
     * {OpenLayers.Map} The OpenLayers.Map instance.
     */
    var createMap = function() {
        return new OpenLayers.Map({
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            units: "m",
            numZoomLevels: 18,
            maxResolution: 156543.0339,
            maxExtent: new OpenLayers.Bounds(-20037508, -20037508,
                                             20037508, 20037508.34),
            allOverlays: false,
            theme: null,
            controls: []
        });
    };

    /**
     * Method: createLayers
     * Create the layers.
     *
     * Returns:
     * {Array({OpenLayers.Layer}) Array of layers.
     */
    var createLayers = function() {
        return [
            new OpenLayers.Layer.OSM("OSM"),
            new OpenLayers.Layer.OSM(
                "OSMap (T@H)",
                "http://tah.openstreetmap.org/Tiles/tile/${z}/${x}/${y}.png"
            )
        ];
    };

    /**
     * Method: createLayerStore
     * Create a GeoExt layer store.
     *
     * Parameters:
     * map - {OpenLayers.Map} The Map instance.
     * layers - {Array({OpenLayers.Layer})} The layers to add to the store.
     *
     * Returns:
     * {GeoExt.data.LayerStore} The layer store.
     *
     */
    var createLayerStore = function(map, layers) {
        return new GeoExt.data.LayerStore({
            map: map,
            layers: layers
        });
    };

    /**
     * Method: createTbarItems
     * Create map toolbar items
     *
     * Returns:
     * {Array({GeoExt.Action})} An array of GeoExt.Action objects.
     */
    var createTbarItems = function(map) {
        var actions = [];
        actions.push(new GeoExt.Action({
            iconCls: "pan",
            map: map,
            pressed: true,
            toggleGroup: "tools",
            allowDepress: false,
            tooltip: "Navigate",
            control: new OpenLayers.Control.Navigation()
        }));
        actions.push(new GeoExt.Action({
            iconCls: "zoomin",
            map: map,
            toggleGroup: "tools",
            allowDepress: false,
            tooltip: "Zoom in",
            control: new OpenLayers.Control.ZoomBox({
                out: false
            })
        }));
        actions.push(new GeoExt.Action({
            text: "Query",
            map: map,
            toggleGroup: "tools",
            allowDepress: false,
            control: new OpenLayers.Control.GetFeature({
                protocol: new OpenLayers.Protocol.HTTP({
                    url: "countries",
                    params: {
                        epsg: "900913",
                        attrs: "pays,continent"
                    },
                    format: new OpenLayers.Format.GeoJSON()
                }),
                eventListeners: {
                    featureselected: function(e) {
                        var f = e.feature;
                        var html = "<p>Country: "+f.attributes.pays+"</p>" +
                            "<p>Continent: "+f.attributes.continent+"</p>";
                        f.geometry.transform(
                            map.displayProjection, map.projection);
                        if (!this._popup) {
                            this._popup = new GeoExt.Popup({
                                html: html,
                                map: map,
                                closeAction: 'hide',
                                unpinnable: false
                            });
                        }
                        else {
                            this._popup.body.update(html);
                            this._popup.doLayout();
                        }
                        this._popup.feature = f;
                        this._popup.show();
                    }
                }
            })
        }));
        var ctrl = new OpenLayers.Control.NavigationHistory();
        map.addControl(ctrl);
        actions.push(new GeoExt.Action({
            control: ctrl.previous,
            iconCls: "back",
            tooltip: "back",
            disabled: true
        }));
        actions.push(new GeoExt.Action({
            control: ctrl.next,
            iconCls: "next",
            tooltip: "next",
            disabled: true
        }));
        return actions;
    };

    /*
     * Public
     */
    return {

        /**
         * APIMethod: init
         * Initialize the page layout.
         */
        init: function() {

            var map = createMap();
            var layers = createLayers();
            var layerStore = createLayerStore(map, layers);

            new Ext.Viewport({
                layout: "border",
                items: [{
                    title: "Map",
                    region: "center",
                    xtype: "gx_mappanel",
                    map: map,
                    layers: layerStore,
                    center: new OpenLayers.LonLat(
                        14871588.220497, -3199348.255331
                    ),
                    zoom: 4,
                    items: [{
                        xtype: "gx_zoomslider",
                        aggressive: true,
                        vertical: true,
                        height: 100,
                        x: 10,
                        y: 20,
                        plugins: new GeoExt.ZoomSliderTip({
                            template: "Scale: 1 : {scale}<br>Resolution: {resolution}"
                        })
                    }],
                    tbar: createTbarItems(map)
                }, {
                    title: "Layer tree",
                    region: "west",
                    width: 150,
                    xtype: "treepanel",
                    loader: new Ext.tree.TreeLoader({
                        applyLoader: false
                    }),
                    root: {
                        nodeType: "gx_layercontainer",
                        layerStore: layerStore,
                        leaf: false,
                        expanded: true
                    },
                    rootVisible: false
                }]
            });
        }
    };
})();
