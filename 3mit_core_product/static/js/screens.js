odoo.define('3mit_core_product.editvariantes', function (require) {
"use strict";
var Dialog = require('web.Dialog');
var core = require('web.core');
var _t = core._t;
var qweb = core.qweb;
var fieldRegistry = require('web.field_registry');
require('account.section_and_note_backend');

var SectionAndNoteFieldOne2Many = fieldRegistry.get('section_and_note_one2many');
SectionAndNoteFieldOne2Many.include({
        custom_events: _.extend({}, SectionAndNoteFieldOne2Many.prototype.custom_events, {
        open_matrix: '_openMatrix',
    }),

    _applyGrid: function (changes, productTemplateId) {
        this.trigger_up('field_changed', {
            dataPointID: this.dataPointID,
            changes: {
                grid: JSON.stringify({changes: changes, product_template_id: productTemplateId}),
                grid_update: true // to say that the changes to grid have to be applied to the SO.
            },
            viewType: 'form',
        });
    },

    _openMatrix: function (ev) {
        ev.stopPropagation();
        var self = this;
        var dataPointId = ev.data.dataPointId;
        var productTemplateId = ev.data.product_template_id;
        var editedCellAttributes = ev.data.editedCellAttributes;
        if (!ev.data.edit) {
            // remove the line used to open the matrix
            this._setValue({operation: 'DELETE', ids: [dataPointId]});
        }

        this.trigger_up('field_changed', {
            dataPointID: this.dataPointID,
            changes: {
                grid_product_tmpl_id: {id: productTemplateId}
            },
            viewType: 'form',
            onSuccess: function (result) {
                // result = list of widgets
                // find one of the SO widget
                // (not so lines because the grid values are computed on the SO)
                // and get the grid information from its recordData.
                var gridInfo = result.find(r => r.recordData.grid).recordData.grid;
                self._openMatrixConfigurator(gridInfo, productTemplateId, editedCellAttributes);
            }
        });
    },
    _openMatrixConfigurator: function (jsonInfo, productTemplateId, editedCellAttributes) {
        var self = this;
        var infos = JSON.parse(jsonInfo);
        var MatrixDialog = new Dialog(this, {
            title: _t('Choose Product Variants'),
            size: 'extra-large', // adapt size depending on matrix size?
            $content: $(qweb.render(
                'product_matrix.matrix', {
                    header: infos.header,
                    rows: infos.matrix,
                }
            )),
            buttons: [
                {text: _t('Confirm'), classes: 'btn-primary', close: true, click: function (result) {
                    var $inputs = this.$('.o_matrix_input');

                    for (var i = 0; i < $inputs.length; i++) {
                        if ($inputs[i].value > 0){
                            var name_atr = $inputs[i].attributes.name_2.nodeValue
                            var value_v = $inputs[i].value
                            for (var p = 0; p < $inputs.length; p++) {
                                if ($inputs[p].attributes.name_2.nodeValue == 'C'+name_atr){
                                    $inputs[p].value = value_v
                                }
                            }
                        }
                    }

                    var matrixChanges = [];
                    _.each($inputs, function (matrixInput) {
                        if (matrixInput.value && matrixInput.value !== matrixInput.attributes.value.nodeValue) {
                            matrixChanges.push({
                                qty: parseFloat(matrixInput.value),
                                ptav_ids: matrixInput.attributes.ptav_ids.nodeValue.split(",").map(function (id) {
                                      return parseInt(id);
                                }),
                            });
                        }
                    });
                    if (matrixChanges.length > 0) {
                        self._applyGrid(matrixChanges, productTemplateId);
                    }
                }},
                {text: _t('Close'), close: true},
            ],
        }).open();

        MatrixDialog.opened(function () {
            if (editedCellAttributes.length > 0) {
                var str = editedCellAttributes.toString();
                MatrixDialog.$content.find('.o_matrix_input').filter((k, v) => v.attributes.ptav_ids.nodeValue === str)[0].focus();
            } else {
                MatrixDialog.$content.find('.o_matrix_input:first()').focus();
            }
        });
    },
});


});

