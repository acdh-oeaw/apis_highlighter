function GetFormAjaxHighl(FormName, ObjectID, ButtonText) {
        function add_form_highl(data, ajax) {
            if (!ajax) {
                var hidden_forms = '<input type=\"hidden\" name=\"HL_start\" id=\"id_HL_start\" /> <input type=\"hidden\" name=\"HL_end\" id=\"id_HL_end\" /> <input type=\"hidden\" name=\"HL_text_id\" id=\"id_HL_text_id\" />'
                data.form = data.form.replace('<div class=\"form-actions\">', hidden_forms+'<div class=\"form-actions\">')
                data.form = data.form.replace(/LS_notes_refs/g, 'LS_notes_refs_high')
            };
            try {
                if ($.ApisHigh.tt_instance["__state"] == 'stable') {
                    $.ApisHigh.tt_instance.content(data.form);
                    console.log('instance content')} else {
                    $.ApisHigh.tt_instance_detail.content(data.form);
                    };
                    }
                catch (err){
                $.ApisHigh.tt_instance_detail.content(data.form)
                    }
                $(".form.ajax_form").unbind()

                $('#id_HL_start').val($.ApisHigh.selected_text.start);
                $('#id_HL_end').val($.ApisHigh.selected_text.end);
                $('#id_HL_text_id').val($.ApisHigh.selected_text.id);
        };
        if (ButtonText === undefined) {
        ButtonText = 'create/modify';
        };
        if (ObjectID === undefined) {
		console.log('objct id false')
        ObjectID = false;
        var FormName2 = FormName.replace('HighlighterForm', 'Form');
        if ($.ApisForms[FormName2+'_'+$.ApisHigh.vars.entity_type]) {
          var new_data = $.extend(true, {}, $.ApisForms[FormName2+'_'+$.ApisHigh.vars.entity_type]);
          new_data.form = new_data.form
              .replace(new RegExp('##ENT_PK##', 'g'), $.ApisHigh.vars.instance_pk);
          new_data.form = new_data.form
              .replace(new RegExp(FormName2, 'g'), FormName);
            new_data.form = new_data.form.replace(/LS_notes_refs/g, 'LS_notes_refs_high')
          add_form_highl(new_data, false);
        } else {

        $.ajax({
                type: 'POST',
                url: $.ApisHigh.vars.urls.get_form_ajax,
                beforeSend: function(request) {
                  var csrftoken = getCookie('csrftoken');
                    request.setRequestHeader("X-CSRFToken", csrftoken);
                  },
                data: {'FormName':FormName,'SiteID':$.ApisHigh.vars.instance_pk,'ObjectID':ObjectID,'ButtonText':ButtonText, 'entity_type': $.ApisHigh.vars.entity_type},
                success: function(data) {
                    console.log(data)
                    data.form = data.form.replace(/LS_notes_refs/g, 'LS_notes_refs_high')
                    add_form_highl(data, true);
                }
            })
	};
        } else {
        $.ajax({
                type: 'POST',
                url: $.ApisHigh.vars.urls.get_form_ajax,
                beforeSend: function(request) {
                  var csrftoken = getCookie('csrftoken');
                    request.setRequestHeader("X-CSRFToken", csrftoken);
                  },
                data: {'FormName':FormName,'SiteID':$.ApisHigh.vars.instance_pk,'ObjectID':ObjectID,'ButtonText':ButtonText, 'entity_type': $.ApisHigh.vars.entity_type},
                success: function(data) {
                    data.form = data.form.replace(/LS_notes_refs/g, 'LS_notes_refs_high')
                    add_form_highl(data, true);
                }
            });}
    };


function highlight_detail(event) {
        //
	
        var entity_type = $(this).data('entity-type');
        var ann_id = $(this).data('hl-ann-id');
        var entity_class = $(this).data('entity-class').toLowerCase().replace($.ApisHigh.vars.entity_type.toLowerCase(), '');
        var entity_class_rel = $(this).data('entity-class').substr(0,1).toLowerCase() + $(this).data('entity-class').substr(1);
        var entity_pk_rel =  $(this).data('entity-pk')

        if (entity_type == 'apis_relations') {
            var entity_pk_lst = $(this).data('related-entity-pk').split(',')

        if(entity_pk_lst.length == 2) {
        var ind_entity_pk = $.inArray(String($.ApisHigh.vars.instance_pk), entity_pk_lst)
        entity_pk_lst.splice(ind_entity_pk, 1)
        var entity_pk = entity_pk_lst[0]}
        if(entity_pk_lst.length == 1) {
            var entity_p = entity_pk_lst[0]
        }}
        var html = '<div class="card list-group" id="accordion2">'
        html += '<a class="list-group-item" onclick=DeleteTempEntity("'+ann_id+'","HLAnnotation")>Delete Annotation</a>'
        if (entity_type == 'apis_relations') {
        html += '<a class="list-group-item" onclick=DeleteAnnTempEntity("'+ann_id+'","'+entity_class_rel.toLowerCase()+'","'+entity_pk_rel+'","'+entity_type.substr(5)+'")>Delete Complete</a>'
        html += '<a class="list-group-item" href="/apis/entities/entity/'+entity_class+'/'+entity_pk+'/edit">Goto entity</a>'
        if ($(this).data('entity-class')) {
        html += '<a class="list-group-item" onclick=GetFormAjaxHighl("'+$(this).data('entity-class')+'Form","'+entity_pk_rel+'")>Edit Entity</a>'}}
        if (entity_type == 'entities' && $(this).data('entity-class')){
            html += '<a class="list-group-item" onclick=GetFormAjaxHighl("'+$(this).data('entity-class')+'HighlighterForm","'+ann_id+'")>Edit Entity</a>'
        }
        html += '</div>';
        $(this).tooltipster({
                content: html,
                contentAsHTML: true,
                interactive: true,
                trigger: 'click',
                multiple: true,
                zIndex: 999,
                theme: 'tooltipster-light',
                functionBefore: function(instance, helper) {
                    $.ApisHigh.tt_instance_detail = instance
                },
                functionAfter: function(instance, helper) {
                    $.ApisHigh.tt_instance_detail.content(html);
                },
                functionPosition: function(instance, helper, position){
                    position.size.height = 'auto';
                    return position
                }

        }).tooltipster('open');
	console.log($(this));
        event.stopPropagation();
    };

function unbind_ann_agreement_form() {
        $('#SelectAnnotatorAgreement').submit(function (event) {
            event.preventDefault();
            event.stopPropagation();
            var instance = $.ApisHigh.vars.instance_pk;
            var kind_instance = $.ApisHigh.vars.entity_type;
            var formData = $(this).serialize();
            formData += '&instance='+instance+'&kind_instance='+kind_instance;
            $.ajax({
                    type: 'GET',
                    url: $.ApisHigh.vars.urls.annotatoragreementview ,
                    data: formData,
                    success: function(data) {
                        for (var key in data.data[0]) {
                            $('#agrm_'+key).html('');
                            $('#agrm_'+key).append('<h3 class="agrm_title">'+$('#id_metrics option:selected').text()+'</h3>');
                            $('#agrm_'+key).append(data.data[0][key]);
                            if (data.data[1]) {
                                $('#agrm_'+key).append('<h3 class="agrm_title">Precision, Recall, F1</h3>');
                                $('#agrm_'+key).append(data.data[1][key]);
                            }
                        }
                    }
                })
        })

    };

function activate_context_menu_highlighter() {
  $("body").on("click", "a.con-menu-item", function(event){
          console.log('clicked');  
	  event.stopPropagation();
           var endpoint = $(this).data('endpoint');
           GetFormAjaxHighl(endpoint);
        });
        $('body').on('click','mark.hl_text_complex', function (event){
            var text_id = $(this).data('hl-text-id');
            var char_start = $(this).data('hl-start');
            var char_end = $(this).data('hl-end');
            var data = {'text_id': text_id, 'char_start': char_start, 'char_end': char_end};
            $(this).tooltipster({
                content: 'loading...',
                contentAsHTML: true,
                interactive: true,
                trigger: 'manual',
                multiple: true,
                zIndex: 999,
                theme: 'tooltipster-light',
                functionBefore: function(instance, helper) {

                $.get($.ApisHigh.vars.urls.showoverlappinghighlights, data, function(data) {
                    // call the 'content' method to update the content of our tooltip with the returned data.
                    // note: this content update will trigger an update animation (see the updateAnimation option)
                    instance.content(data.data);
                    $.ApisHigh.high_complex = instance;
                    })
                },
                functionPosition: function(instance, helper, position){
                    position.size.height = 'auto';
                    position.size.width = 'auto';
                    return position
                }

        });
        $(this).tooltipster('open');
        event.stopPropagation();
        });
        unbind_ann_agreement_form();
}

function find_related_object(elem, data) {
    for (i = 0; i < data.length; i++) {
        if (elem === data[i]['id']) {
            return data[i]
        }
    }
}

function get_menu_object(elem) {
    if (elem['kind'] == 'txt') {
    var res = '<a class="list-group-item">'+elem['name']+'</a>'}
    else if (elem['kind'] == 'frm') {
        var res = '<a class="list-group-item con-menu-item" data-endpoint="'+elem.api.api_endpoint+'">'+elem['name']+'</a>'
    } else if (elem['kind'] == 'fn') {
        var res = '<a class="list-group-item" onclick='+elem.api.api_endpoint+'>'+elem['name']+'</a>'
    }

    return res
}

function updateObject(object, newValue, path){

  var stack = path.split('>');

  while (stack.length>1) {
    object = object[stack.shift()];
  }

  object[stack.shift()] = newValue;

}

function create_nested_menu(data, data_list) {
    //console.log(data)
    var res = ''
    for (x in data) {

       // res += '<li class="list-group-item">'+data_list[x]['name']
        if (data[x] instanceof Object && Object.keys(data[x]).length > 0) {
            res += '<a href="#HighlighterMenu'+data_list[x]['id']+'" class="list-group-item" data-toggle="collapse" data-parent="#HighlighterMenu'+data_list[x]['id']+'">'+data_list[x]['name']+'<i class="fa fa-caret-down"></i></a>\
              <div class="collapse list-group-submenu list-group-submenu-1" id="HighlighterMenu'+data_list[x]['id']+'">'
            res += create_nested_menu(data[x], data_list)
            res += '</div>'
        } else {
            //console.log(data_list[x])
            res += get_menu_object(data_list[x])
        }
    }
    return res
}

function create_apis_menu(data) {
    var lst_m = []
    var len = 0
    for (i = 0; i < data['menuentry_set'].length; i++) {
        //console.log(data['menuentry_set'][i]);
        var lst = []
        var elem = data['menuentry_set'][i]
        lst.push(elem)
        while (elem.parent) {
            if (!(elem.parent instanceof Object)) {
            elem.parent = find_related_object(elem.parent, data['menuentry_set'])}
            lst.push(elem.parent)
            elem = elem.parent
        }
        lst_m.push(lst.reverse());
        if (lst.length > len) {
            len = lst.length
        }
    }
    var menu_2 = {}
    var menu_2_lst = {}
    for (x = 0; x < lst_m.length; x++) {
            var s_n = menu_2
        for (u = 0; u < lst_m[x].length; u++) {
            if (!(lst_m[x][u]['id'] in menu_2_lst)) {
            s_n[lst_m[x][u]['id']] = {}
            menu_2_lst[lst_m[x][u]['id']] = lst_m[x][u]
            }
            s_n = s_n[lst_m[x][u]['id']]}
    }
    var menu_html = create_nested_menu(menu_2, menu_2_lst)
        menu_html += '</div>'
        menu_html = '<div class="card list-group" id="accordion">' + menu_html
        return menu_html
}


function get_selected_text(txt_id) {
    var element = document.getElementById(txt_id);
    var start = 0, end = 0;
    var sel, range, priorRange;
    console.log("js fired")
    if (typeof window.getSelection != "undefined") {
        range = window.getSelection().getRangeAt(0);
        priorRange = range.cloneRange();
        priorRange.selectNodeContents(element);
        priorRange.setEnd(range.startContainer, range.startOffset);
        shadow_selection = priorRange.cloneContents()
        console.log(shadow_selection)
        const num_brs = shadow_selection.querySelectorAll("br").length
        start = priorRange.toString().length + num_brs*2;
        end = start + range.toString().length;
    } else if (typeof document.selection != "undefined" &&
            (sel = document.selection).type != "Control") {
        range = sel.createRange();
        priorRange = document.body.createTextRange();
        priorRange.moveToElementText(element);
        priorRange.setEndPoint("EndToStart", range);
        shadow_selection = priorRange.cloneContents()
        console.log(shadow_selection)
        console.log(shadow_selection.querySelectorAll("br").length)
        const num_brs = shadow_selection.querySelectorAll("br").length
        start = priorRange.text.length + num_brs*2;
        end = start + range.text.length;
    }
    return {
        start: start,
        end: end,
        rect: range.getBoundingClientRect()
    };
};


function init_apis_highlighter(project_id, entity_id) {
  if (typeof $.ApisHigh == 'undefined') {
      $.ApisHigh = {}; };
    return $.ajax({
        type: 'GET',
        url: "/apis/api/HLProjects/"+project_id.toString()+"/",
        success: function(data) {
            //menu = create_apis_menu(data.results[0])
        //$( "#test_menu" ).append(menu)
        //console.log(data)
        $.ApisHigh.entity_id = entity_id
        var lst_class = []
        for (i=0; i < data['texthigh_set'].length; i++) {
           lst_class.push('.'+data['texthigh_set'][i]['text_class'])
        }
        var cl_2 = lst_class.join(', ')
        $(cl_2).bind('mouseup',function() {
        $.ApisHigh.selected_text = get_selected_text($(this).attr('id'))
        $.ApisHigh.selected_text.id = $(this).attr('id')
        })
        $(cl_2).tooltipster({
            content: 'Loading...',
            contentAsHTML: true,
            interactive: true,
            zIndex: 999,
	    maxWidth: 600,
            trigger: 'click',
            theme: 'tooltipster-light',
            side: ['bottom'],

        functionPosition: function(instance, helper, position){
            position.coord.top = ($.ApisHigh.selected_text.rect.top + (position.distance + $.ApisHigh.selected_text.rect.height));
            position.coord.left = ($.ApisHigh.selected_text.rect.left - ((position.size.width/2)-($.ApisHigh.selected_text.rect.width/2)));
		console.log(helper)
		if (position.coord.left < 0) {position.coord.left = 10};
		let w_1 = helper.geo.origin.size.width;
		if (w_1 - (position.coord.left + position.size.width) - 10 < 0) { position.coord.left = w_1 - position.size.width +10 }
	    position.target = $.ApisHigh.selected_text.rect.left + ($.ApisHigh.selected_text.rect.width/2);
            position.size.height = 'auto';
            //console.log(position.target)
            return position;
    },
        // 'instance' is basically the tooltip. More details in the "Object-oriented Tooltipster" section.
        functionBefore: function(instance, helper) {
            if ($.ApisHigh.high_complex){
                $.ApisHigh.high_complex.close();
            };
            if ($.ApisHigh.selected_text.start == $.ApisHigh.selected_text.end) {
                return false
            }
            var $origin = $(helper.origin);
            // we set a variable so the data is only loaded once via Ajax, not every time the tooltip opens
            if ($origin.data('loaded') !== true) {

                menu = create_apis_menu(data)

                    // call the 'content' method to update the content of our tooltip with the returned data
                    instance.content(menu);


                    // to remember that the data has been loaded
                    $origin.data('loaded', true);
                    $.ApisHigh.data_original = menu;

            } else {//console.log('fired');

            instance.content($.ApisHigh.data_original);}
            $.ApisHigh.tt_instance = instance
        },

    });

        //$.ApisHigh.tt_instance = $(cl_2).tooltipster('instance');
        }
    })

}

