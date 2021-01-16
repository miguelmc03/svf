# -*- coding: utf-8 -*-
{
    'name': "3mit_changes_crm",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale_crm', 'sales_team', 'payment', 'portal', 'utm'],

    # always loaded
    'data': [
        'wizard/wizard_customer_request.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/quotation.xml',
        'report/presupuesto.xml',
        'views/mail_template.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
