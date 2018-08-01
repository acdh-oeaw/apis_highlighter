function GetFormAjaxHighl(FormName, ObjectID, ButtonText) {
        function add_form_highl(data, ajax) {
            if (!ajax) {
                console.log('adding fields');
                var hidden_forms = '<input type=\"hidden\" name=\"HL_start\" id=\"id_HL_start\" /> <input type=\"hidden\" name=\"HL_end\" id=\"id_HL_end\" /> <input type=\"hidden\" name=\"HL_text_id\" id=\"id_HL_text_id\" />'
                data.form = data.form.replace('<div class=\"form-actions\">', hidden_forms+'<div class=\"form-actions\">')
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
                unbind_ajax_forms();

                $('#id_HL_start').val($.ApisHigh.selected_text.start);
                $('#id_HL_end').val($.ApisHigh.selected_text.end);
                $('#id_HL_text_id').val($.ApisHigh.selected_text.id);
                console.log('correct run');
        };
        if (ButtonText === undefined) {
        ButtonText = 'create/modify';
        };
        if (ObjectID === undefined) {
        ObjectID = false;
        var FormName2 = FormName.replace('HighlighterForm', 'Form');
        if ($.ApisForms[FormName2+'_'+$.ApisHigh.vars.entity_type]) {
          var new_data = $.extend(true, {}, $.ApisForms[FormName2+'_'+$.ApisHigh.vars.entity_type]);
          new_data.form = new_data.form
              .replace(new RegExp('##ENT_PK##', 'g'), $.ApisHigh.vars.instance_pk);
          new_data.form = new_data.form
              .replace(new RegExp(FormName2, 'g'), FormName);
          add_form_highl(new_data, false);
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

        if (entity_type == 'relations') {
            var entity_pk_lst = $(this).data('related-entity-pk').split(',')

        if(entity_pk_lst.length == 2) {
        var ind_entity_pk = $.inArray(String($.ApisHigh.vars.instance_pk), entity_pk_lst)
        entity_pk_lst.splice(ind_entity_pk, 1)
        var entity_pk = entity_pk_lst[0]}
        if(entity_pk_lst.length == 1) {
            var entity_p = entity_pk_lst[0]
        }}
        var html = '<div class="panel list-group" id="accordion2">'
        html += '<a class="list-group-item" onclick=DeleteTempEntity("'+ann_id+'","HLAnnotation")>Delete Annotation</a>'
        if (entity_type == 'relations') {
        html += '<a class="list-group-item" onclick=DeleteAnnTempEntity("'+ann_id+'","'+entity_class_rel+'","'+entity_pk_rel+'")>Delete Complete</a>'
        html += '<a class="list-group-item" href="/entities/entity/'+entity_class+'/'+entity_pk+'/edit">Goto entity</a>'
        if ($(this).data('entity-class')) {
        html += '<a class="list-group-item" onclick=GetFormAjaxHighl("'+$(this).data('entity-class')+'Form","'+entity_pk_rel+'")>Edit Entity</a>'}}
        if (entity_type == 'entities' && $(this).data('entity-class')){
            html += '<a class="list-group-item" onclick=GetFormAjaxHighl("'+$(this).data('entity-class')+'HighlighterForm","'+ann_id+'")>Edit Entity</a>'
        }
        html += '</div>'
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

        });
        $(this).tooltipster('open')
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
