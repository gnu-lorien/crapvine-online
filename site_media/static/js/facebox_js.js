    jQuery(document).ready(function($) {
        $(document).bind('reveal.facebox', function() {
            $("form.uniForm").submit(function() {
                form = this;
                jQuery.facebox(function($) {
                    fields = jQuery(form).find("input[type='text']").filter(":enabled");
                    params = {}
                    fields.each(function() {
                        params[this.name] = this.value;
                    });
                    fields = jQuery(form).find("select").filter(":enabled");
                    fields.each(function() {
                        params[this.name] = this.value;
                    });
                    fields = jQuery(form).find("input[type='hidden']");
                    fields.each(function() {
                        params[this.name] = this.value;
                    });
                    jQuery.post(form.getAttribute('action'), params,
                        function(data, textStatus) {
                            jQuery.facebox(data);
                        }
                    );
                });
                return false;
            });
        });
     });
