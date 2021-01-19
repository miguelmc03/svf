# -*- coding: utf-8 -*-

from odoo import models, fields


class FabricantesMachinery(models.Model):
    _name = "fabricantes.machinery"
    _description = "Guarda la información relacionada con la maquinaria"
    _rec_name = "fabricantes"

    fabricantes = fields.Char(string="Fabricante de equipo original", store=True)


class SerieMachinery(models.Model):
    _name = "serie.machinery"
    _description = "Almacena información relacionada con el numero de serie de la maquinaria"
    _rec_name = "n_serial"

    _sql_constraints = [
        ('n_serial_unique', 'unique(n_serial)', "No pueden existir dos números de serie idénticos."),
    ]

    n_serial = fields.Char(string="Numero de serie o familia", store=True, required=True)


class ModelMachinery(models.Model):
    _name = "model.machinery"
    _description = "Almacena información relacionada con el modelo de la maquinaria"
    _rec_name = "modelo_maquinaria"

    modelo_maquinaria = fields.Char(string="Modelo", store=True)


class AplicacionMachinery(models.Model):
    _name = "aplicacion.machinery"
    _description = "Almacena información acerca del uso de la maquinaria"
    _rec_name = "aplicacion"

    aplicacion = fields.Char(string="Aplicación", store=True)


class ServiceMachinery(models.Model):
    _name = "service.machinery"
    _description = "Almacena información acerca del tipo de mantenimiento a aplicar en la maquinaria"
    _rec_name = "tipo_servicio"

    tipo_servicio = fields.Char(string="Aplicación", store=True)
