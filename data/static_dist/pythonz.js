/*globals $ xross sitecats SimpleMDE ymaps */

var pythonz = {

    bootstrap: function() {
        "use strict";
        xross.automate();

        $(function(){
            pythonz.makeGeopatterns();
            pythonz.markUser();
            pythonz.toggleTags();

            sitecats.bootstrap();
            sitecats.make_cloud('tags_box');

            $('.mod__has_tooltip').tooltip();
        });
    },

    toggleTags: function () {
        "use strict";
        $.each($('.tags_box'), function(idx, el) {
            var $el = $(el);
            if ($('.categories_box', $el).length == 0){
                $el.hide();
            };
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
            var html = el.innerHTML.replace(/\[u:(\d+):\s*([^\]]+)\s*\]/g, '<a href="http://pythonz.net/users/$1" title="Профиль на pythonz">$2</a>');
            $(el).html(html);
        });
    },

    activateCommentsTab: function(timeout) {
        "use strict";
        setTimeout(function(){
            var maxCount = 0,
                ids = ['comments_vk', 'comments_fb', 'comments_disqus', 'comments_internal'];

            $.each(ids, function(idx, tabId){
                var count = parseInt($('#' + tabId + '_cnt').text());
                if (count > maxCount) {
                    $('a[href="#' + tabId + '"]', '#comments_tabs').tab('show');
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

        // _replaceSelection() взята из исходников SimpleMDE.
        // https://github.com/NextStepWebs/simplemde-markdown-editor
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

        return new SimpleMDE({
            element: textareaEl,
            forceSync: true,
            indentWithTabs: false,
            spellChecker: false,
            toolbar: [
                'bold',
                'italic',
                getButton('accent', 'flag', 'Акцент'),
                getButton('quote', 'quote-left', 'Цитата'),
                getButton('list_ul', 'list-ul', 'Маркированный список'),
                getButton('table', 'table', 'Таблица'),
                '|',
                'image',
                'link',
                '|',
                getButton('note', 'flag-o', 'На заметку'),
                getButton('warning', 'exclamation-triangle', 'Внимание'),
                getButton('code', 'code', 'Код'),
                '|',
                getButton('gist', 'github', 'Gist'),
                getButton('podster', 'headphones', 'Подкаст с podster.fm'),
                '|',
                'fullscreen'
            ],
            insertTexts: {
                image: ['.. image:: ', ''],
                gist: ['.. gist:: ', ''],
                note: ['.. note:: ', ''],
                warning: ['.. warning:: ', ''],
                podster: ['.. podster:: ', ''],
                link: ['`', '<>`_'],
                accent: ['``', '``'],
                table: ['\n.. table::\n ', '|\n\n\n'],
                code: ['\n.. code::\n', '\n\n\n'],
                quote: ['\n```\n', '\n```'],
                list_ul: ['\n* ', '\n\n']
            }
        });

    },

    Reference: {

        RULE_PYVERSION_ADDED: [
            /\+py([\w\.]+)/g,
            '<small><div class="label label-info" title="Актуально с версии"><a href="/versions/named/$1/">$1</a></div></small>'],

        RULE_PYVERSION_REMOVED: [
            /-py([\w\.]+)/g,
            '<small><div class="label label-danger" title="Устрело в версии"><a href="/versions/named/$1/">$1</a></div></small>'],

        RULE_LITERAL: [/'([^']+)'/g, '<strong class="cl__green">$1</strong>'],
        RULE_UNDERMETHOD: [/(__[^\s]+__)/g, '<i>$1</i>'],
        RULE_BASE_TYPES: [
            /([^\w/])(bool|callable|dict|False|int|iterable|iterator|list|None|object|set|str|True|tuple|unicode)([^\w])/g,
            '$1<small><code>$2</code></small>$3'
        ],
        RULE_EXCEPTIONS: [
            /([^\w])(AttributeError|AssertionError|ImportError|IndexError|KeyError|NotImplementedError|RuntimeError|StopIteration|SyntaxError|SystemError|TypeError|UnboundLocalError|ValueError|OSError)([^\w])/g,
            '$1<small><div class="label label-warning">$2</div></small>$3'
        ],
        RULE_EMDASH: [/\s+-\s+/g, ' &#8212; '],

        decorateDescription: function(areaId) {
            "use strict";
            this.decorateArea(areaId,
                [
                    this.RULE_PYVERSION_REMOVED,
                    this.RULE_PYVERSION_ADDED,
                    this.RULE_BASE_TYPES,
                    this.RULE_EXCEPTIONS,
                    this.RULE_EMDASH
                ]
            );
        },

        decorateFuncResult: function(areaId) {
            "use strict";
            this.decorateArea(areaId,
                [
                    this.RULE_PYVERSION_REMOVED,
                    this.RULE_PYVERSION_ADDED,
                    this.RULE_BASE_TYPES,
                    this.RULE_EMDASH
                ]
            );
        },

        decorateFuncParams: function(areaId) {
            "use strict";
            var funcProcessArgs = function (matchStr, argName, separator) {
                    argName = argName.replace(/([^=]+)(=.+)/g, '$1<span class="text-muted">$2</span>');
                    return '<small><span class="glyphicon glyphicon-certificate"></span></small> <b>' + argName + '</b>' + separator;
                };

            this.decorateArea(areaId,
                [
                    [/([^>\s]+)(\s--)/g, funcProcessArgs],
                    [/--/g, ':'],
                    this.RULE_PYVERSION_REMOVED,
                    this.RULE_PYVERSION_ADDED,
                    this.RULE_LITERAL,
                    this.RULE_UNDERMETHOD,
                    this.RULE_BASE_TYPES,
                    this.RULE_EXCEPTIONS,
                    this.RULE_EMDASH
                ]
            );
        },

        decorateArea: function(areaId, rules) {
            "use strict";
            var $area = $('#' + areaId),
                html = $area.html();

            if (html !== undefined) {
                $.each(rules, function (idx, rule) {
                    html = html.replace(rule[0], rule[1]);
                });
            }

            $area.html(html);

        }

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
