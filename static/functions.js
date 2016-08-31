var VIEWER = VIEWER || {};

(function ($) {
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
    VIEWER.login = {
        init: function () {
           $(window).on('resize orientationChange', VIEWER.login.resize);
        },
        resize: function () {
            var isMobile = window.matchMedia("only screen and (max-width: 768px)");
            if (isMobile.matches) {
                $('#login-nav').addClass("nav-stacked");
                $('#start-panel').addClass("small-start-panel");
            }
            else {
                $("#login-nav").removeClass("nav-stacked");
                $('#start-panel').removeClass("small-start-panel");
            }
        }
    };
    VIEWER.cells = {
        current_cell: null,
        init: function () {
            var $cells = $('[data-toggle="popover"]');
            if ($cells.length > 0) {
                $cells.on('click', VIEWER.cells.clickHandler);
                // $cells.on('click.popover', VIEWER.cells.addPopover);
            }
            VIEWER.cells.initLabels();

        },
        initLabels: function() {
            var $labels = $(".request");
            $labels.each(VIEWER.cells.setLabelCoordinates);
        },
        setLabelCoordinates: function() {
            var $label = $(this);
            var $value_span = $label.siblings("span.value");
            if ($value_span.length > 0) {
                var position = $value_span.offset();
                position.top -= $label.outerHeight();
                position.left += $value_span.width() / 2;
                $label.offset(position);
                $label.css('display', 'block');
            }
        },
        setAcceptRequestButtonHandlers: function($cell) {
            var $popover= $('#popover');

            // Handler for request buttons
            $popover.find('button.accept').click(function () {
                var $button = $(this);
                var request_id = $button.data('request');
                $popover.find("button").prop("disabled", true);
                $.ajax({
                    url: '/api/change-request/' + request_id + '/',
                    type: 'put',
                    dataType: 'json'
                })
                    .done(function (data, textStatus, jqXHR) {
                        VIEWER.cells.changeCellValue($cell, data.new_value);
                        $cell.children('.label.request').remove();
                        $cell.popover('destroy');
                        $popover.find("button").prop("disabled", false);
                        VIEWER.cells.current_cell = null;
                    })
            });
            // Handler for revoke button
            $popover.find('button.revoke').click(function () {
                var $button = $(this);
                var request_id = $button.data('request');
                $("#popover").find("button").prop("disabled", true);
                $.ajax({
                    url: '/api/change-request/' + request_id + '/',
                    type: 'delete',
                    dataType: 'json'
                })
                    .done(function (data, textStatus, jqXHR) {
                        VIEWER.cells.changeCellValue($cell, data.old_value);
                        if (! data.other_requests) {
                            $cell.children('.label.request').remove();
                        }
                        $cell.popover('destroy');
                        $popover.find("button").prop("disabled", false);
                        VIEWER.cells.current_cell = null;
                    })
            })


        },
        changeCellValue: function ($cell, new_value, remove_class) {
            remove_class = typeof remove_class !== 'undefined' ? remove_class : false;
            $cell.children('.value').text(new_value);
            var class_string = 'changed';
            if (remove_class) {
                $cell.removeClass(class_string);
            }
            else {
                $cell.addClass(class_string);
            }
        },
        setDeleteSubmitHandler: function ($cell) {
            $('#popover').find('.delete-form').click(function (e) {
                e.preventDefault();
                var $form = $(this);
                $("#popover").find("button").prop("disabled", true);
                var action_url = $form.data('action');
                $.ajax({
                    url: action_url,
                    type: 'delete'
                })
                    .done(function (data, textStatus, jqXHR) {
                        VIEWER.cells.changeCellValue($cell, data.old_value, true);
                    })
                    .always(function () {
                        $cell.popover('destroy');
                        VIEWER.cells.current_cell = null;
                    });

                });
        },
        setRequestSubmitHandler: function ($cell) {
            var $forms = $('.request_form');
            $forms.submit(function (e) {
                e.preventDefault();
                var $form = $(this);
                $("#popover").find("button").prop("disabled", true);
                var action_url = $form.data('action');
                $.ajax({
                    url: action_url,
                    type: 'post',
                    dataType: 'json',
                    data: $form.serialize()
                })
                    .done(function (data, textStatus, jqXHR) {
                        if (jqXHR.status == 201) { // CREATED
                            VIEWER.cells.changeCellValue($cell, data.new_value);
                        }
                        if (jqXHR.status == 202) {  // ACCEPTED
                            var $labels = $cell.children(".request");
                            if ($labels.length == 0) {
                                var html = $cell.html();
                                var stub = $("#request-stub").html();
                                $cell.html(html + stub);
                                VIEWER.cells.initLabels()
                            }
                        }
                    })
                    .always(function () {
                        $cell.popover('destroy');
                        VIEWER.cells.current_cell = null;
                    });
            });
        },
        addPopoverEventHandlers: function ($cell) {
            VIEWER.cells.setRequestSubmitHandler($cell);
            VIEWER.cells.setAcceptRequestButtonHandlers($cell);
            VIEWER.cells.setDeleteSubmitHandler($cell);

        },
        addPopover: function ($cell) {
            $.ajax({
                url: '/document/popover/' + $cell.attr('data-id') + '/'
            })
                .done(function (data) {
                    $cell.on('inserted.bs.popover', function () {
                        VIEWER.cells.addPopoverEventHandlers($cell);
                        VIEWER.cells.focusNewValue();
                    });
                    $cell.popover({
                        html: true,
                        content: data,
                        placement: 'auto right',
                        template: '<div class="popover" role="tooltip"><div class="arrow"></div><div id="popover" class="popover-content"></div></div>'

                    });
                    VIEWER.cells.current_cell = $cell;
                    $cell.popover('show');
                });

        },
        focusNewValue: function() {
            var isMobile = window.matchMedia("only screen and (max-width: 768px)");
            if (!isMobile.matches) {
                $('#new_value').select();
            }
            else {
                $('#new_value').one('click', function() {
                    $(this).select();
                })
            }
        },
        clickHandler: function () {
            var $cell = $(this);
            if ($cell.is(VIEWER.cells.current_cell)) {
                $(this).popover('toggle');
                VIEWER.cells.focusNewValue();
            }
            else {
                if (VIEWER.cells.current_cell) {
                    VIEWER.cells.current_cell.popover('destroy');
                    VIEWER.cells.current_cell = null;
                }
                VIEWER.cells.addPopover($cell);
            }
        }
    };
    VIEWER.messages = {
        init: function () {
            var $message_div = $("#messages");
            var messages = $message_div.children(".alert");

            $.each(messages, VIEWER.messages.setMessageTimeout);

            $(document).ajaxComplete(function (e, xhr, settings) {
                var contentType = xhr.getResponseHeader("Content-Type");

                if (contentType == "application/javascript" || contentType == "application/json") {
                    var json = xhr.responseJSON;

                    $.each(json.django_messages, function (i, item) {
                        VIEWER.messages.addMessage(item.message, item.extra_tags);
                    });
                }
            });
        },
        setMessageTimeout: function(index, message) {
            setTimeout(function () {
                var $msg = $(message);
                $msg.fadeOut(500, function () {
                    $msg.remove();
                });
            }, 3000);

        },
        addMessage: function addMessage(text, extra_tags) {
            var message = $('<div class="alert alert-dismissible alert-' + extra_tags + '" role="alert">' +
                '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>'
                + text + '</div>').hide();
            $("#messages").append(message);
            message.fadeIn(500);

            VIEWER.messages.setMessageTimeout(0, message);

        }
    };
    VIEWER.upload = {
        init: function() {
            $('#id_file').change(function() {
                var $form = $(this).parents('form');
                $form.find('[type=submit]').hide();
                var $target = $('#detail_div');
                $target.html(VIEWER.upload.loading);
                $form.ajaxSubmit({
                    target: $target,
                    success: function() {
                        $target.find("form").parsley();
                    },
                    error: function() {
                        $target.html('<div><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></div>');
                    }
                })

            })
        },
        loading: '<div class="cssload-container">' +
                 '<div class="cssload-speeding-wheel"></div>' +
                 '</div>'
    };

    VIEWER.initialize = {
        init: function () {
            VIEWER.csrf.init();
            VIEWER.cells.init();
            VIEWER.messages.init();
            VIEWER.login.init();
            VIEWER.upload.init();
        }
    };

    $(document).ready(VIEWER.initialize.init);

})(jQuery);