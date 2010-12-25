jQuery(document).ready(function($) {
    var mappings = [
        {
            id: "#id_status",
            se: 667,
        },
        {
            id: "#id_nature",
            se: 41,
        },
        {
            id: "#id_demeanor",
            se: 41,
        },
        {
            id: "#id_clan",
            se: 127,
        },
        {
            id: "#id_path",
            se: 460,
        },
        {
            id: "#id_sect",
            se: 615,
        },
        {
            id: "#id_title",
            se: 708,
        }
    ]

    $.each(mappings, function(index, loop) {
         $(loop.id).autocomplete({
            source: function( request, response ) {
                        $.getJSON( "/characters/menu/" + loop.se + "/", {'format': 'json', 'term': request.term}, response );
                    }

        });       
    });
});
