/*globals $ sitecats EasyMDE ymaps */

var pythonz = {

    bootstrap: function() {
        "use strict";

        $(function(){
            pythonz.makeGeopatterns();
            pythonz.markUser();
            pythonz.linkifyVersionMarks();
            pythonz.toggleTags();

            sitecats.bootstrap();
            sitecats.make_cloud('box-tags');

            $('.sticky').sticky({
                topSpacing: 80,
                zIndex: 1
            });

            $('.tooltipped').tooltip();
        });
    },

    toggleTags: function () {
        "use strict";
        $.each($('.tags_box'), function(idx, el) {
            var $el = $(el);
            if ($('.categories_box', $el).length === 0){
                $el.hide();
            }
        });
    },

    makeGeopatterns: function () {
        "use strict";
        $.each($('[data-geopattern]'), function(idx, el) {
            var $el = $(el);
            $el.css('background-image', GeoPattern.generate($el.data('geopattern') + 'a').toDataUrl());
        });
    },

    markUser: function() {
        "use strict";
        $('.py_user').each(function(i, el) {
            var html = el.innerHTML.replace(/\[u:(\d+):\s*([^\]]+)\s*\]/g, '<a href="https://pythonz.net/users/$1" title="Профиль на pythonz">$2</a>');
            $(el).html(html);
        });
    },

    linkifyVersionMarks: function() {
        "use strict";
        // Превращаем отметки актуальности/устаревания справочника
        // (ref-ver-add/ref-ver-del, размечаются на сервере) в ссылки на версии.
        $('.ref-ver-add, .ref-ver-del').each(function(i, el) {
            var $el = $(el),
                version = $.trim($el.text());
            $el.html('<a href="/versions/named/' + version + '/">' + version + '</a>');
        });
    },

    activateCommentsTab: function(timeout) {
        "use strict";
        setTimeout(function(){
            var maxCount = 0,
                ids = ['comments_vk'];

            $.each(ids, function(idx, tabId){
                var count = parseInt($('#' + tabId + '_cnt').text());
                if (count > maxCount) {
                    $('a[href="#' + tabId + '"]', '#tabs-comments').tab('show');
                    maxCount = count;
                }
            });


        }, timeout);
    },

    initEditor: function(textareaEl) {
        "use strict";

        if (!textareaEl) {
            return;
        }

        // _replaceSelection() взята из исходников EasyMDE.
        // https://github.com/Ionaru/easy-markdown-editor
        // После минификации она обфусцируется и далее недоступна.

        function _replaceSelection(cm, active, startEnd, url) {
            if(/editor-preview-active/.test(cm.getWrapperElement().lastChild.className)) {return;}

            var text;
            var start = startEnd[0];
            var end = startEnd[1];
            var startPoint = cm.getCursor("start");
            var endPoint = cm.getCursor("end");
            if(url) {
                end = end.replace("#url#", url);
            }
            if(active) {
                text = cm.getLine(startPoint.line);
                start = text.slice(0, startPoint.ch);
                end = text.slice(startPoint.ch);
                cm.replaceRange(start + end, {
                    line: startPoint.line,
                    ch: 0
                });
            } else {
                text = cm.getSelection();
                cm.replaceSelection(start + text + end);

                startPoint.ch += start.length;
                if(startPoint !== endPoint) {
                    endPoint.ch += start.length;
                }
            }
            cm.setSelection(startPoint, endPoint);
            cm.focus();
        }

        function simpleAction(editor, buttonName){
            _replaceSelection(
                    editor.codemirror,
                    editor.getState()[buttonName],
                    editor.options.insertTexts[buttonName]);
        }

        function getButton(name, icon, title) {
            return {
                name: name,
                action: function (editor) {simpleAction(editor, name);},
                className: 'fa fa-' + icon,
                title: title
            };
        }

        return new EasyMDE({
            element: textareaEl,
            forceSync: true,
            indentWithTabs: false,
            spellChecker: false,
            // Префикс для классов кнопок панели. Без него кнопка таблицы
            // получает класс table и растягивается Bootstrap-утилитой .table.
            toolbarButtonClassPrefix: 'mde',
            shortcuts: {
                // Предпросмотр осуществляется сервером (вкладка «Предпросмотр»),
                // встроенные средства редактора отключаем.
                togglePreview: null,
                toggleSideBySide: null
            },
            toolbar: [
                'bold',
                'italic',
                getButton('accent', 'flag', 'Акцент'),
                getButton('quote', 'quote-left', 'Цитата'),
                getButton('list_ul', 'list-ul', 'Маркированный список'),
                getButton('table', 'table', 'Таблица'),
                '|',
                getButton('image', 'picture-o', 'Изображение'),
                getButton('link', 'link', 'Ссылка'),
                '|',
                getButton('note', 'flag-o', 'На заметку'),
                getButton('warning', 'exclamation-triangle', 'Внимание'),
                getButton('code', 'code', 'Код'),
                '|',
                getButton('gist', 'github', 'Gist'),
                getButton('video', 'youtube-play', 'Видео'),
                getButton('podcast', 'headphones', 'Подкаст с podster.fm'),
                '|',
                'fullscreen'
            ],
            insertTexts: {
                image: ['![', '](https://)'],
                link: ['[', '](https://)'],
                accent: ['`', '`'],
                quote: ['\n> ', '\n'],
                list_ul: ['\n* ', '\n'],
                table: ['\n| Заголовок | Заголовок |\n|---|---|\n| ', ' |\n\n'],
                code: ['\n```python\n', '\n```\n\n'],
                note: ['\n!!! note\n    ', '\n\n'],
                warning: ['\n!!! warning\n    ', '\n\n'],
                gist: ['\n```gist\n', '\n```\n\n'],
                video: ['\n```video\n', '\n```\n\n'],
                podcast: ['\n```podcast\n', '\n```\n\n']
            }
        });

    },

    Map: function (mapElementId, objects) {
        "use strict";
        var self = this,
            _mapEl = $('#' + mapElementId),
            _mapObjs = objects;

        this.getBoundsForCoords = function(coords) {
            return ymaps.util.bounds.getCenterAndZoom(coords, [_mapEl.width(), _mapEl.height()])
        };

        this.getPlacemarksFromMapObjects = function(objects) {
            var allMarks = [],
                markIdx = 0;

            if (objects===undefined) {
                objects = _mapObjs;
            }

            $.each(objects, function(id, props) {
                var coords = props.coords,
                    title = props.title,
                    descr = props.descr,
                    link = props.link;

                allMarks[markIdx] = new ymaps.Placemark(coords, {
                        balloonContentHeader: title,
                        balloonContentBody: descr,
                        balloonContentFooter: link,
                        clusterCaption: title,
                        place_id: id
                    }, {
                        hideIconOnBalloonOpen: false,
                        preset: 'islands#darkBlueCircleDotIcon'
                    });

                markIdx++;
            });
            return allMarks;
        };

        this.getClusterer = function() {
            var objs = self.getPlacemarksFromMapObjects(),
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

        this.initMap = function () {
            ymaps.ready(function () {
                var clusterer = self.getClusterer(),
                    mapState = self.getBoundsForCoords(clusterer.getBounds());

                $.extend(mapState, {
                    controls: ['zoomControl']
                });

                var map = new ymaps.Map(_mapEl.attr('id'), mapState);
                map.geoObjects.add(clusterer);
            });
        };

        self.initMap();
    }

};

pythonz.bootstrap();
