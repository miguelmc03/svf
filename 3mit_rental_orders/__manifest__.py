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
    'name': 'Contabilidad para Alquileres',
    'version': '1.0',
    'summary': 'Permite identificar los productos en alquiler para hacer adecuaciones en la contabilidad',
    'author': '3MIT',
    'depends': ['sale_renting'],
    'data': ["view/add_accounts_field.xml", "security/ir.model.access.csv"],
    'installable': True,
}
