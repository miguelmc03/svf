# coding: utf-8
##############################################################################
#
# Copyright (c) 2016 Tecnología y Servicios AMN C.A. (http://3MIT.com/) All Rights Reserved.
# <contacto@3MIT.com>
# <Teléfono: +58(212) 237.77.53>
# Caracas, Venezuela.
#
# Colaborador: <<Diego Marfil>> <diego@3mit.dev>
#
##############################################################################

{
    'name': 'Importar Excel para Líneas de Presupuesto',
    'version': '1.0',
    'summary': 'Permite importar data desde archivos de Excel para Líneas de Presupuesto. Modulo Contabilidad',
    'author': '3MIT',
    'depends': ['account_accountant'],
    'data': ["wizards/import_data.xml", "view/add_button_import.xml", 'security/ir.model.access.csv'],
    'installable': True,
}
