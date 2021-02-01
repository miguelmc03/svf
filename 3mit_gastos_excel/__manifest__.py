# -*- coding: utf-8 -*-
{
    'name': "Menu para Cargas y ejecutar Gastos",
    'summary': "Menu Carga Gastos",
    'description': "Elaborado por: Ing Yorman Pineda",
    'version': '1.0',
    'author': '3mit',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_excel.xml',
        'views/marcas_herencias.xml',
    ],
    'demo': [
    ],
    'application': True,
}
