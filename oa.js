//<![CDATA[
(function () {
    function oaDOMWait_d8wjw4() {
        createTopCont('d8wjw4');

        function createTopCont(id) {
            var s = document.getElementsByTagName("script"), rx = new RegExp('/loader.js.*[?&]id=' + id), t, u, i, d;
            for (i = s.length; i--;) {
                t = s[i], u = t.getAttribute("src");
                if (rx.test(u)) {
                    d = document.createElement('div'); d.setAttribute('class', 'oax-top-cont oax-top-cont-d8wjw4'); t.parentElement.insertBefore(d, t);
                    return;
                }
            }
            null.myselfnotfound;
        }

        if (typeof window.oa !== 'undefined' && oa.api && oa.API_CFG.build !== 'mini') {
            initOA_d8wjw4();
        } else if (window.oa_cb_arr) {
            window.oa_cb_arr.push(initOA_d8wjw4);
        } else {
            window.oa_cb_arr = [initOA_d8wjw4];
            var s = document.createElement('script'), h = location.search.match(/(?:\?|&)oaserver=([^&]+)/), h2 = 'api-oa.com', uri = '/alpportal/oa_head.js?lang=ro&proj=api-anii-drumetiei&key=proj-missing-key&leaflet_gshim=1&revbust=c3197b05&callback=initOA';
            s.setAttribute('type', 'text/javascript');
            s.setAttribute('src', 'https://' + (h && h.length > 1 && h[1] || h2) + uri);
            document.body.appendChild(s);
        }

    };

    document.addEventListener('DOMContentLoaded', oaDOMWait_d8wjw4);
    if (document.readyState === 'interactive' || document.readyState === 'complete') oaDOMWait_d8wjw4();

})();

function initOA() {
    alp.forEach(window.oa_cb_arr, "v()");
}

function initOA_d8wjw4() {
    var cfg = {
        "lang": "ro",
        "mapInit": {
            "basemap": "oac",
            "style": "summer",
            "network": "",
            "overlay": []
        },
        "recommendations": [
            "249704940"
        ],
        "recommendationsGeometry": true
    }
        , k = ['id', 'recommendations', 'recommendationsGeometry', , 'preselectAll', 'fitBounds', 'fitDataBounds', 'categories']
        , fc = alp.opt(cfg, alp.filter(alp.oKeys(cfg), '!this[v]', alp.arr2oSimple(k)), true)
        , lc = alp.opt(cfg, k, true)
        , fmp = window.fmp = oa.api.flexmappage(alp.mix({ topCont: 'oax-top-cont-d8wjw4' }, fc));
    lc.fitBounds = !((cfg.zoom && cfg.center) || cfg.bbox);
    delete lc.fitDataBounds;
    fmp.addLayer('oa.x.RecommendationsLayer', lc);

}
//]]>
