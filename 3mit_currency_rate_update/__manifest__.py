# -*- coding: utf-8 -*-
{
    'name': "Currency Rate Update",
    'summary': """
        Currency Rate Update""",
    'description': """
        Tipo de cambio para solventar obligaciones denominadas en dólares de los EE.UU.A., pagaderas en la República Mexicana.
    """,
    'author': "OpenBIAS S.A.",
    'website': "https://www.bias.com.mx",
    'category': 'Financial Management/Configuration',
    'version': '0.1',
    'depends': ['base', 'account'],
    'data': [
        "data/action_server_data.xml",
    ],
    "post_init_hook": "post_init_hook",
}
# pip install suds-community