from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # === VISIBILIDAD EN PORTAL ===
    is_client_visible = fields.Boolean(
        string='Visible en Portal',
        default=False,
        help='Si está marcado, el cliente podrá ver esta tarea como un hito en su portal'
    )
    is_alert = fields.Boolean(
        string='Es Alerta',
        compute='_compute_is_alert',
        store=True,
        help='Indica si esta tarea es una alerta/novedad para el cliente'
    )
    is_internal = fields.Boolean(
        string='Solo Interno',
        compute='_compute_is_internal',
        store=True
    )

    # === INFORMACIÓN ADICIONAL PARA HITOS ===
    milestone_description = fields.Text(
        string='Descripción para Cliente',
        help='Descripción simplificada que verá el cliente en el portal'
    )
    completion_date = fields.Datetime(
        string='Fecha de Completado',
        readonly=True
    )

    # === TIPO DE TAREA ===
    # IMPORTANTE: Esta lista debe coincidir EXACTAMENTE con los valores
    # usados en project_templates_data.xml
    task_category = fields.Selection([
        # Categorías principales usadas en las plantillas
        ('booking', 'Reserva/Booking'),
        ('documentation', 'Documentación'),
        ('physical_op', 'Operación Física'),
        ('customs', 'Aduanas'),
        ('transport', 'Transporte'),
        ('other', 'Otro'),
        # Categorías adicionales por si acaso
        ('alert', 'Alerta/Novedad'),
    ], string='Categoría', default='other')

    # === CAMPOS HEREDADOS DEL PROYECTO (para fácil acceso) ===
    booking_number = fields.Char(
        related='project_id.booking_number',
        string='Booking',
        store=True
    )
    vessel_name = fields.Char(
        related='project_id.vessel_name',
        string='Motonave',
        store=True
    )

    @api.depends('tag_ids', 'tag_ids.name')
    def _compute_is_alert(self):
        for task in self:
            task.is_alert = any(
                'ALERTA' in (tag.name or '').upper()
                for tag in task.tag_ids
            )

    @api.depends('tag_ids', 'tag_ids.name')
    def _compute_is_internal(self):
        for task in self:
            task.is_internal = any(
                'INTERNO' in (tag.name or '').upper()
                for tag in task.tag_ids
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-set is_client_visible based on tags"""
        tasks = super().create(vals_list)
        for task in tasks:
            if task.tag_ids:
                tag_names = [tag.name.upper() for tag in task.tag_ids if tag.name]
                if any('HITO' in name or 'MILESTONE' in name for name in tag_names):
                    task.is_client_visible = True
                if any('ALERTA' in name for name in tag_names):
                    task.is_client_visible = True
        return tasks

    def write(self, vals):
        """Registrar fecha de completado cuando se cierra la tarea"""
        res = super().write(vals)
        if 'stage_id' in vals:
            for task in self:
                if task.stage_id and self._is_stage_closed(task.stage_id):
                    task.completion_date = fields.Datetime.now()
        return res

    def _is_stage_closed(self, stage):
        """Check if a stage is considered closed (compatible with Odoo 18)"""
        if not stage:
            return False
        # Odoo 18: check fold or name
        if hasattr(stage, 'fold') and stage.fold:
            return True
        stage_name = (stage.name or '').upper()
        return any(word in stage_name for word in ['COMPLETADO', 'DONE', 'CANCELADO', 'CANCEL', 'CERRADO', 'CLOSED'])

    @api.model
    def _get_portal_tasks_domain(self, project_id):
        """Dominio para filtrar tareas visibles en portal"""
        return [
            ('project_id', '=', project_id),
            '|',
            ('is_client_visible', '=', True),
            ('is_alert', '=', True),
        ]