//xross.debug = true;

pythonz = {

    bootstrap: function() {
        xross.automate();
        $(function(){
            pythonz.mark_user();
        });
    },

    xrossreinit: function() {
        //pythonz.bootstrap();
    },

    mark_user: function() {
        $('.py_user').each(function(i, el) {
            var html = el.innerHTML.replace(/\[u:(\d+):\s*([^\]\s]+)\s*\]/g, '<a href="http://pythonz.net/users/$1" title="Профиль на pythonz">$2</a>');
            $(el).html(html);
        });
    },

    Map: function (map_el_id, objects) {

        var self = this,
            _map_el = $('#'+map_el_id),
            _map_objs = objects;

        this.get_bounds_for_coords = function(coords) {
            return ymaps.util.bounds.getCenterAndZoom(coords, [_map_el.width(), _map_el.height()])
        };

        this.get_placemarks_from_map_objects = function(objects) {
            var all_marks = [],
                mark_idx = 0;

            if (objects===undefined) {
                objects = _map_objs
            }

            $.each(objects, function(id, props) {
                var coords = props.coords,
                    title = props.title,
                        descr = props.descr,
                        link = props.link;

                all_marks[mark_idx] = new ymaps.Placemark(coords, {
                        balloonContentHeader: title,
                        balloonContentBody: descr,
                        balloonContentFooter: link,
                        clusterCaption: title,
                        place_id: id
                    }, {
                        hideIconOnBalloonOpen: false,
                        preset: 'islands#darkBlueCircleDotIcon'
                    });

                mark_idx++;
            });
            return all_marks
        };

        this.get_clusterer = function() {
            var objs = self.get_placemarks_from_map_objects(),
                clusterer = new ymaps.Clusterer({
                    preset: 'islands#darkBlueClusterIcons',
                    clusterDisableClickZoom: true,
                    clusterBalloonPanelMaxMapArea: 0,
                    clusterBalloonContentLayoutWidth: 250,
                    clusterBalloonContentLayoutHeight: 100,
                    clusterBalloonLeftColumnWidth: 100
                });
            clusterer.add(objs);
            return clusterer;
        };

        this.init_map = function () {
            ymaps.ready(function () {
                var clusterer = self.get_clusterer(),
                    map_state = self.get_bounds_for_coords(clusterer.getBounds());

                $.extend(map_state, {
                    controls: ['zoomControl']
                });

                var map = new ymaps.Map(_map_el.attr('id'), map_state);
                map.geoObjects.add(clusterer);
            })
        };

        self.init_map();
    }

};

pythonz.bootstrap();
