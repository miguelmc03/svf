# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MachineryInventory(models.Model):
    _name = 'machinery.inventory'
    _description = 'Agrega un menú y un formulario para el registro de maquinaria ' \
                   'y el registro de servicios a realizarle.'
    _rec_name = "inventory_name"

    _sql_constraints = [
        ('partner_unique', 'unique(partner_id)',
         "No pueden existir dos inventarios con un mismo propietario. Por favor, edite el existente."),
        ('ref_new_client_unique', 'unique(ref_new_client)',
         "No pueden existir dos inventarios con un mismo propietario. Por favor, edite el existente."),
    ]

    @api.model_create_multi
    def create(self, values):
        res = super(MachineryInventory, self).create(values)
        maquinaria = self.maquinaria.search([('status_id', '=', 'activo'), ('partner_ref', '=', False)])
        maquinaria_ids = [lines.id for lines in maquinaria]
        if res.registered_client == 'no registrado':
            new_client = self.env['unregistered.clients'].search([('id', '=', res.ref_new_client.id)])
            res.inventory_name = new_client.model_name
            res.registered = False
            for lines in res.maquinaria:
                if lines.id in maquinaria_ids:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                    maquinaria[0].partner_ref = True
                    maquinaria[0].new_client_belong_id = new_client.id
                    maquinaria[0].inventory_id = res.id
        else:
            res.inventory_name = res.partner_id.name
            res.registered = True
            for lines in res.maquinaria:
                if lines.id in maquinaria_ids:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                    maquinaria[0].partner_ref = True
                    maquinaria[0].partner_belong_id = res.partner_id.id
                    maquinaria[0].inventory_id = res.id
        return res

    def write(self, values):
        res = super(MachineryInventory, self).write(values)
        if self.registered_client == 'registrado':
            maquinaria_current_partner = self.env['machinery.registry'] \
                .search([('partner_belong_id', '=', self.partner_id.id), ('inventory_id', '=', self.id)])
            maquinaria_current_partner_ids = [line.ids for line in maquinaria_current_partner]

            maquinaria_ids_in_current_inventary = [lines.id for lines in self.maquinaria]

            for id_s in maquinaria_current_partner_ids:
                if id not in maquinaria_ids_in_current_inventary:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', id_s)])
                    maquinaria[0].partner_ref = False
                    maquinaria[0].partner_belong_id = None
                    maquinaria[0].inventory_id = None

            maquinaria = self.maquinaria.search([('status_id', '=', 'activo'), ('partner_ref', '=', False)])
            maquinaria_ids = [lines.id for lines in maquinaria]
            for lines in self.maquinaria:
                if lines.id in maquinaria_ids:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                    maquinaria[0].partner_ref = True
                    maquinaria[0].partner_belong_id = self.partner_id.id
                    maquinaria[0].inventory_id = self.id
        else:

            maquinaria_current_partner = self.env['machinery.registry'] \
                .search([('new_client_belong_id', '=', self.ref_new_client.id), ('inventory_id', '=', self.id)])
            maquinaria_current_partner_ids = [line.ids for line in maquinaria_current_partner]
            maquinaria_ids_in_current_inventary = [lines.id for lines in self.maquinaria]

            for id_s in maquinaria_current_partner_ids:
                if id not in maquinaria_ids_in_current_inventary:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', id_s)])
                    maquinaria[0].partner_ref = False
                    maquinaria[0].new_client_belong_id = None
                    maquinaria[0].inventory_id = None

            maquinaria = self.maquinaria.search([('status_id', '=', 'activo'), ('partner_ref', '=', False)])
            maquinaria_ids = [lines.id for lines in maquinaria]
            for lines in self.maquinaria:
                if lines.id in maquinaria_ids:
                    maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                    maquinaria[0].partner_ref = True
                    maquinaria[0].new_client_belong_id = self.ref_new_client.id
                    maquinaria[0].inventory_id = self.id
        return res

    def unlink(self):
        for rec in self:
            if rec.registered_client == 'no registrado':
                maquinaria = self.maquinaria.search([('status_id', '=', 'activo'), ('partner_ref', '=', True),
                                                     ('new_client_belong_id', '=', rec.ref_new_client.id)])
                maquinaria_ids = [lines.id for lines in maquinaria]
                for lines in rec.maquinaria:
                    if lines.id in maquinaria_ids:
                        maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                        maquinaria[0].partner_ref = False
                        maquinaria[0].new_client_belong_id = None
                        maquinaria[0].inventory_id = None
            else:
                maquinaria = self.maquinaria.search([('status_id', '=', 'activo'), ('partner_ref', '=', True),
                                                     ('partner_belong_id', '=', rec.partner_id.id)])
                maquinaria_ids = [lines.id for lines in maquinaria]
                for lines in rec.maquinaria:
                    if lines.id in maquinaria_ids:
                        maquinaria = self.env['machinery.registry'].search([('id', '=', lines.id)])
                        maquinaria[0].partner_ref = False
                        maquinaria[0].partner_belong_id = None
                        maquinaria[0].inventory_id = None
        return super(MachineryInventory, self).unlink()

    # Campo para el nombre del registro
    inventory_name = fields.Char(string="Nombre para el registro", store=True)

    # Selection para definir si el usuario se encuentra o no registrado
    registered_client = fields.Selection([
        ('registrado', 'Registrado'),
        ('no registrado', 'No registrado')
    ], string="¿Propietario registrado?", default="registrado", required=True, store=True)

    # En caso de que el cliente no se encuentre registrado
    ref_new_client = fields.Many2one('unregistered.clients', string="Nuevo cliente", store=True)

    # Para saber si pertenece a un cliente registrado
    registered = fields.Boolean(string="¿Cliente registrado?", store=True)

    partner_id = fields.Many2one('res.partner', string="Propietario")
    maquinaria = fields.Many2many("machinery.registry", string="Maquinaria", store=True, required=True)
    country_id = fields.Many2one('res.country', string="País", required=True)
    ciudad = fields.Char(string="Ciudad", required=True)
    calle = fields.Char(string="Calle ubicación de la maquinaria")
    calle2 = fields.Char(string="Calle aux. ubicación de la maquinaria")
    estado = fields.Many2one('res.country.state', string="Estado/provincia maquinaria", required=True)
    zip = fields.Char(string="Código postal")


class MachineryRegistry(models.Model):
    _name = 'machinery.registry'
    _description = 'Contiene todos los registros relacionados con la maquinaria: modelo, número de serial,' \
                   'entre otros atributos de la maquinaria.'
    _rec_name = "registry_name"

    _sql_constraints = [
        ('model_serie_unique', 'unique(modelo_maquinaria,n_serial)',
         "Un modelo no puede tener repetido un numero de serial. Por favor, añada otro numero de serie."),
    ]

    @api.model_create_multi
    def create(self, values):
        res = super(MachineryRegistry, self).create(values)
        aux = str(res.fecha_fab_aux).split('-')
        res.fecha_fab = aux[1] + '/' + aux[0]
        if res.edit_status == "edit":
            res.edit_status = "view"
        return res

    @api.depends('fabricantes', 'modelo_maquinaria')
    def compute_registry_name(self):
        for rec in self:
            rec.registry_name = rec.fabricantes.fabricantes + ' - ' + rec.modelo_maquinaria.modelo_maquinaria

    def action_active(self):
        for rec in self:
            rec.status_id = "activo"

    def action_inactive(self):
        for rec in self:
            rec.status_id = "inactivo"

    # Campo para el nombre del registro
    registry_name = fields.Char(string="Nombre del registro", compute="compute_registry_name")

    fabricantes = fields.Many2one('fabricantes.machinery', string="Fabricante de equipo original", store=True,
                                  required=True)
    # Para saber si tiene dueño y establecer el domain en el many2many
    partner_ref = fields.Boolean(string="¿Tiene dueño?", default=False, store=True)
    partner_belong_id = fields.Integer(string="Id del partner al cual pertenece la maquinaria", store=True)
    new_client_belong_id = fields.Integer(string="Id del nuevo partner al cual pertenece la maquinaria", store=True)
    inventory_id = fields.Integer(string="Id del inventario actual", store=True)

    n_serial = fields.Many2one('serie.machinery', string="Numero de serie o familia", store=True, required=True)
    modelo_maquinaria = fields.Many2one('model.machinery', string="Modelo", store=True,
                                        required=True)
    status_id = fields.Selection([
        ("activo", "Activo"),
        ("inactivo", "Inactivo")
    ], string="Estado de la maquinaria", readonly=True, default="activo")
    edit_status = fields.Selection([
        ('edit', 'Edit'),
        ('view', 'View')
    ], readonly=True, default="edit", store=True)
    aplicacion = fields.Many2one('aplicacion.machinery', store=True)

    fecha_fab_aux = fields.Date(string="Fecha de fabricación ", store=True, required=True,
                                help="Una vez guardado, no se puede cambiar")
    fecha_fab = fields.Char(string="Fecha de fabricación", compute="fecha_fab_aux", store=True)
    fecha_marcha = fields.Date(string="Fecha de puesta en marcha")

    horas_act = fields.Float(string="Horas actuales")
    horas_trabajo = fields.Float(string="Horas de trabajo promedio (Hrs/año)")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('un_client')
    def get_partner_domain(self):
        for rec in self:
            domain = []
            aux_id = []
            if rec.un_client:
                id_domain_inventory = self.env['machinery.inventory'].search([('registered', '!=', False)])
                for ids in id_domain_inventory.ids:
                    aux_id.append(ids)
                domain.append(('id', 'in', aux_id))
            else:
                id_domain_inventory = self.env['machinery.inventory'].search([('registered', '=', False)])
                for ids in id_domain_inventory.ids:
                    aux_id.append(ids)
                domain.append(('id', 'in', aux_id))
            return {
                'domain': {
                    'machinery_inventory': domain
                }
            }

    @api.onchange("machinery_inventory")
    def get_machinery_domain(self):
        for rec in self:
            domain = []
            aux_id = []
            if rec.un_client:
                id_domain = self.env['machinery.registry']\
                    .search([('partner_belong_id', '=', rec.machinery_inventory.partner_id.id)])
                for ids in id_domain.ids:
                    aux_id.append(ids)
                domain.append(('id', 'in', aux_id))
                domain.append(('status_id', '=', 'activo'))
            else:
                id_domain = self.env['machinery.registry'] \
                    .search([('new_client_belong_id', '=', rec.machinery_inventory.ref_new_client.id)])
                for ids in id_domain.ids:
                    aux_id.append(ids)
                domain.append(('id', 'in', aux_id))
                domain.append(('status_id', '=', 'activo'))
            return {
                    'domain': {
                        'machinery_to_maintenance': domain
                    }
                }

    # Para definir si es o no un presupuesto de maquinaria y si el cliente esta o no registrado
    _status_id = fields.Boolean(string="Presupuesto de servicio a equipos", default=False)
    un_client = fields.Boolean(string="¿Cliente registrado?", default=True)

    machinery_inventory = fields.Many2one('machinery.inventory', string="Propietario de la máquina")
    machinery_to_maintenance = fields.Many2one("machinery.registry", string="Maquinaria")
    tipo_servicio = fields.Many2many('service.machinery', string="Tipo de servicio")


class ProjectTask(models.Model):
    _inherit = "project.task"

    maquinaria_vista = fields.Many2one(related="sale_line_id.order_id.machinery_to_maintenance",
                                       string="Maquinaria a dar servicio", store=True)
