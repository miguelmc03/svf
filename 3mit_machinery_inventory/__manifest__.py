# -*- coding: utf-8 -*-
{
    'name': "Inventario de maquinaria",
    'summary': """
        Crea una vista formulario para registrar maquinaria y los servicios prestados.""",

    'description': """
        * Permite registrar nueva maquinaria en el inventario:\n
            * Fabricante.\n
            * Modelo.\n
            * Numero de serie.\n
            * Aplicación (Uso).\n
            * Fecha de fabricación.\n
            * Fecha de puesta en marcha.\n
            * Horas actuales.\n
            * Horas de trabajo promedio.\n\n
        * Permite añadir propietarios (registrados o no) a la maquinaria:\n
            * Selector para el propietario (Registrado o no registrado).\n
            * Propietario (o nuevo cliente).\n
            * Dirección de la maquinaria/propietario.\n
            * Manymany para elegir varias máquinas, dependiendo sea el caso.\n\n
        * Permite seleccionar en el Módulo de ventas si es un presupuesto para maquinaria o no.\n
        * Adición en el módulo de tareas para ver la maquinaria presupuestada.\n\n
        Elaborado por: Kleiver Pérez.
    """,

    'author': "3MIT",
    'website': "https://www.3mit.dev/",
    'category': 'Inventario',
    'version': '1.5.6',

    # Cualquier módulo necesario para que este funcione correctamente
    'depends': ['base', 'stock', 'contacts', 'sale_management', 'sale_timesheet'],

    'data': [
        'security/ir.model.access.csv',
        'data/aplicacion_machinery_data.xml',
        'data/fabricantes_machinery_data.xml',
        'data/serie_machinery_data.xml',
        'data/service_machinery_data.xml',
        'data/model_machinery_data.xml',
        'views/menu_machinery.xml',
        'views/menu_unregistered_clients.xml',
        'views/unregistered_clients_views.xml',
        'views/machinery_views.xml',
        'views/machinery_registry.xml',
        'views/sale_order_inherit.xml',
        'views/sale_timesheet_inherit.xml',
    ],
    'demo': [
    ],
    'application': False,
    'installable': True
}
