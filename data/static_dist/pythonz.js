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
            var html = el.innerHTML.replace(/\[u:\s*([^\]\s]+)\s*\]/g, '<a href="http://$1.at.pythonz.net" target="_blank" title="Профиль $1 на pythonz">$1</a>');
            $(el).html(html);
        });
    }

};

pythonz.bootstrap();
