# -*- coding: utf-8 -*-

from odoo import models, fields, api


class UnregisteredClients(models.Model):
    _name = 'unregistered.clients'
    _description = 'Modelo para registar clientes fuera de Odoo'
    _rec_name = 'model_name'

    _sql_constraints = [
        ('vat_unique', 'unique(vat_new_client)',
         "Ese NIF ya se encuentra asociado a otra persona. Por favor, verifique e intente nuevamente."),
    ]

    @api.depends('name_new_client', 'surname_new_client')
    def compute_registry_name(self):
        for rec in self:
            rec.model_name = rec.name_new_client + ' ' + rec.surname_new_client

    model_name = fields.Char(string="Nombre del registro", compute="compute_registry_name")
    name_new_client = fields.Char(string="Nombre", store=True, required=True)
    surname_new_client = fields.Char(string="Apellido", store=True, required=True)
    vat_new_client = fields.Char(string="Nº identif. fiscal (NIF)", store=True, required=True)
