# -*- coding: utf-8 -*-
{
    'name': "Menu para Cargas y ejecutar Pagos a empleado",
    'summary': "Menu pago empleados",
    'description': "Elaborado por: Ing Yorman Pineda",
    'version': '1.0',
    'author': '3mit',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr_expense', 'sale', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_excel.xml',
        'views/pagos_empleados_view.xml',
        'views/pagos_posventas_marcas_view.xml',
        #'views/hr_datos_rrhh_view.xml',
    ],
    'demo': [
    ],
    'application': True,
}
