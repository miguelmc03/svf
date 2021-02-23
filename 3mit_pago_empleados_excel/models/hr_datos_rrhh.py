# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from datetime import (datetime)
from dateutil import (relativedelta)
import re


class Employee(models.Model):
    _inherit = 'hr.employee'
    coste_hora = fields.Float()
