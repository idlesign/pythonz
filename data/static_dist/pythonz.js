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
    }

};

pythonz.bootstrap();
