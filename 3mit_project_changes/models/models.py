# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class AnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    ACCOUNT_STATES = [('done', 'Disponible'),
                      ('blocked', 'Cerrado')]

    state = fields.Selection(ACCOUNT_STATES, string='Estado', copy=False, default='done')

    def write(self, vals):
        if self.state == 'blocked' and not vals.get('state'):
            raise Warning(_('No puede editar la cuenta de un proyecto cerrado'))
        super(AnalyticAccountInherit, self).write(vals)

class ProjectChanges(models.Model):
    _inherit = 'project.project'

    PROJECT_STATES = [('done', 'Disponible'),
                     ('blocked', 'Cerrado')]

    state = fields.Selection(PROJECT_STATES,string='Estado', copy=False, default='done')
    close = fields.Boolean(string='Cerrar', default=False)
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')], string='Kanban State',
        copy=False, default='normal', required=True)

    @api.onchange("state")
    def change_state_account(self):
        self.analytic_account_id.state = self.state

    def action_close(self):
        self.write({'state': 'blocked'})

    def set_to_done(self):
        self.write({'state': 'done'})

    def write(self, vals):
        if self.state == 'blocked' and not vals.get('state'):
            raise Warning(_('No puede editar un proyecto cerrado'))
        super(ProjectChanges, self).write(vals)

class TaskInherit(models.Model):
    _inherit = "project.task"

    @api.model
    def create(self, vals):
        project = self.env['project.project'].browse(self._context['active_id'])
        if project.state == 'blocked':
            raise Warning(_('No se pueden crear tareas en estado cerrado'))
        else:
            res = super(TaskInherit, self).create(vals)
            return res

class ProjectCreateSalesOrder(models.TransientModel):
    _inherit = 'project.create.sale.order'

    state = fields.Selection(related="project_id.state")
    
class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def create(self, values):
        if values.get('project_id'):
            project_id = self.env['project.project'].browse(values.get('project_id'))
            if project_id.state == 'blocked':
                raise Warning(_('Proyecto cerrado'))
        if values.get('account_id'):
            account_id = self.env['account.analytic.account'].browse(values.get('project_id'))
            if account_id.state == 'blocked':
                raise Warning(_('Asegurese de usar una cuenta de un proyecto que este abierto'))
        super(AccountAnalyticLineInherit, self).create(values)