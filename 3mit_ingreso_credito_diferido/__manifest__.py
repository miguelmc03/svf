# -*- coding: utf-8 -*-
{
    'name': "Ingreso y credito diferidos",
    'summary': "Ingreso y credito diferidos",
    'description': "Elaborado por: Ing Yorman Pineda",
    'version': '1.0',
    'author': '3mit',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', '3mit_pago_empleados_excel','web_tree_dynamic_colored_field'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tramite_diferidos_view.xml',
        'views/client.xml',
    ],
    'demo': [
    ],
    'application': True,
}
