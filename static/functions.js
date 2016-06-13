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
            var position = $label.parent().offset();
            position.top -= $label.height() / 2;
            $label.offset(position);
            $label.css('display', 'block');
        },
        setAcceptRequestButtonHandlers: function($cell) {
            var $buttons = $('.pending-requests button').click(function () {
                var $button = $(this);
                var request_id = $button.data('request');
                $.ajax({
                    url: '/api/change-request/' + request_id + '/',
                    type: 'put',
                    dataType: 'json'
                })
                    .success(function (data, textStatus, jqXHR) {
                        VIEWER.cells.changeCellValue($cell, data.new_value);
                        $cell.popover('destroy');
                        VIEWER.cells.current_cell = null;
                    })
            })
        },
        changeCellValue: function ($cell, new_value) {
            $cell.text(new_value)
                .addClass('changed');
        },
        setRequestSubmitHandler: function ($cell) {
            var $forms = $('.request_form');
            $forms.submit(function (e) {
                e.preventDefault();
                var $form = $(this);
                $form.find("button").prop("disabled", true);
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
                                $cell.html(html + '<span class="label label-info request">Request</span>');
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
        },
        addPopover: function ($cell) {
            console.log("addPopover");
            $.ajax({
                url: '/document/popover/' + $cell.attr('data-id') + '/'
            })
                .done(function (data) {
                    console.log("addPopover ajax done");
                    $cell.on('inserted.bs.popover', function () {
                        console.log("inserted event handler");
                        VIEWER.cells.addPopoverEventHandlers($cell);
                        $('[name="new_value"]').focus()
                    });
                    $cell.popover({
                        html: true,
                        content: data,
                        template: '<div class="popover" role="tooltip"><div class="arrow"></div><div class="popover-content"></div></div>'

                    });
                    VIEWER.cells.current_cell = $cell;
                    $cell.popover('show');
                });

        },
        clickHandler: function () {
            var $cell = $(this);
            if ($cell.is(VIEWER.cells.current_cell)) {
                $(this).popover('toggle');
                console.log("toggle");
                $('[name="new_value"]').focus()
            }
            else {
                if (VIEWER.cells.current_cell) {
                    console.log("destroy");
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

    VIEWER.initialize = {
        init: function () {
            VIEWER.csrf.init();
            VIEWER.cells.init();
            VIEWER.messages.init();
        }
    };

    $(document).ready(VIEWER.initialize.init);

})(jQuery);