var VIEWER = VIEWER || {};

(function($){
    VIEWER.csrf = {
        getCookie: function (name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
        csrfSafeMethod: function (method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        },
        init: function () {
            var csrftoken = VIEWER.csrf.getCookie('csrftoken');
            $.ajaxSetup({
                beforeSend: function (xhr, settings) {
                    if (!VIEWER.csrf.csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });

        }
    };
    VIEWER.cells = {
        init: function () {
            var $cells = $('[data-toggle="popover"]');
            if ($cells.length > 0) {
                $cells.on('click.popover', VIEWER.cells.addPopover);
            }
            VIEWER.cells.initLabels();

        },
        initLabels: function() {
            var $labels = $(".request");
            $labels.each(VIEWER.cells.setLabelCoordinates);
        },
        setLabelCoordinates: function() {
            var $label = $(this);
            var position = $label.parent().offset();
            position.top -= $label.height()/ 2;
            $label.offset(position);
            $label.css('display', 'block');
        },
        setRequestSubmitHandler: function($cell) {
            var $forms = $('.request_form');
            $forms.submit(function (e) {
                e.preventDefault();
                var $form = $(this);
                var action_url = e.currentTarget.action;
                $.ajax({
                    url: action_url,
                    type: 'post',
                    dataType: 'json',
                    data: $form.serialize()
                })
                    .done(function (data, textStatus, jqXHR) {
                        if (jqXHR.status == 201) { // CREATED
                            $cell.text(data.new_value)
                                 .addClass('changed')

                        }
                        if (jqXHR.status == 202) {  // ACCEPTED
                            var $labels = $cell.children(".request");
                            if($labels.length == 0){
                                var html = $cell.html();
                                $cell.html(html + '<span class="label label-info request">Request</span>');
                                VIEWER.cells.initLabels()
                            }
                        }
                        $cell.popover('destroy');
                        $cell.off('click.popover-toggle');
                        $cell.on('click.popover', VIEWER.cells.addPopover);
                        console.log("Form submit done")
                    })
            });
        },
        addPopover: function () {
            console.log("add popover");
            var $cell = $(this);
            $cell.off('click.popover');
            $.ajax({
                url: '/document/popover/' + $cell.attr('data-id') + '/'
            })
                .fail(function () {
                    $cell.one('click.popover')
                })
            .done(function(data) {
                console.log("ajax call done");
                $cell.one('inserted.bs.popover', function() {
                    console.log("popover inserted in dom");
                    VIEWER.cells.setRequestSubmitHandler($cell);
                    $cell.on('click.popover-toggle', VIEWER.cells.clickHandler);
                });
                $cell.popover({
                    html:true,
                    content:  data
                });
                $cell.popover('show');
            });

        },
        clickHandler: function () {
            $(this).popover('toggle')
        }
    };

    VIEWER.initialize = {
        init: function() {
            VIEWER.csrf.init();
            VIEWER.cells.init();
        }
    };

    $(document).ready(VIEWER.initialize.init);

})(jQuery);