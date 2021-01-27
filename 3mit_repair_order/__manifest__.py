# -*- coding: utf-8 -*-
{
    'name': "Órdenes de reparación",

    'summary': """
        Modificaciones en las órdenes de reparación
        """,

    'description': """
        * Al seleccionar el tipo "Eliminar", no se borra el precio del total general.\n
        * Permite imprimir un presupuesto sin necesidad de que el mismo este confirmado/en reparación.\n\n
        Colaborador: Kleiver Pérez.
    """,

    'author': "3MIT",
    'website': "https://www.3mit.dev/",
    'category': 'Reparación',
    'version': '1.1.6',

    'depends': ['base', 'repair', 'project', 'helpdesk', 'helpdesk_repair'],
    'data': [
        'views/repair_order_inherit_view.xml',
        'report/inherit_repair_order.xml',
    ],
}
