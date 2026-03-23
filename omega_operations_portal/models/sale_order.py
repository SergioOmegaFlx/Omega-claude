from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # === CAMPOS ADICIONALES ===
    operation_project_id = fields.Many2one(
        'project.project',
        string='Proyecto de Operación (DO)',
        readonly=True,
        copy=False
    )
    auto_create_project = fields.Boolean(
        string='Crear DO Automáticamente',
        default=True,
        help='Al confirmar la orden, se creará automáticamente el proyecto de operación'
    )

    def _get_operation_type_from_template(self):
        """
        Determina el tipo de operación basado en la plantilla de cotización.
        """
        self.ensure_one()
        
        template_name = ''
        if self.sale_order_template_id:
            template_name = (self.sale_order_template_id.name or '').upper()
        
        _logger.info(f"SO {self.name}: Template name = '{template_name}'")
        
        if 'FLEXITANQUE' in template_name or 'FLEXITANK' in template_name or 'FLX' in template_name:
            return 'export_flex'
        elif 'ISOTANQUE' in template_name or 'ISOTANK' in template_name:
            return 'export_iso'
        elif 'IMPO' in template_name or 'IMPORTA' in template_name:
            return 'import'
        elif 'CONT 20' in template_name or 'CONT 40' in template_name:
            return 'export_flex'
        else:
            return 'physical_op'

    def _get_project_template(self, operation_type):
        """
        Obtiene la plantilla de proyecto según el tipo de operación.
        Busca plantillas incluyendo archivadas.
        """
        template_mapping = {
            'export_flex': 'omega_operations_portal.project_template_export_flex',
            'export_iso': 'omega_operations_portal.project_template_export_iso',
            'import': 'omega_operations_portal.project_template_import',
            'physical_op': 'omega_operations_portal.project_template_physical_op',
        }
        
        xml_id = template_mapping.get(operation_type)
        _logger.info(f"Looking for project template: {xml_id}")
        
        if xml_id:
            try:
                # Buscar incluyendo archivados
                template = self.env.ref(xml_id, raise_if_not_found=False)
                if template:
                    _logger.info(f"Found template: {template.name} (ID: {template.id}, active: {template.active})")
                    return template
                else:
                    _logger.warning(f"Template {xml_id} not found in database")
            except Exception as e:
                _logger.error(f"Error getting template {xml_id}: {e}")
        
        return False

    def _prepare_operation_project_values(self, operation_type):
        """Prepara los valores para crear el proyecto de operación"""
        self.ensure_one()
        
        commodity = ''
        container_qty = 0
        port_origin = ''
        port_destination = ''
        
        # Verificar si hay campos Studio en la orden
        if hasattr(self, 'x_studio_commodity'):
            commodity = getattr(self, 'x_studio_commodity', '') or ''
        if hasattr(self, 'x_studio_origen'):
            port_origin = getattr(self, 'x_studio_origen', '') or ''
        if hasattr(self, 'x_studio_destino'):
            port_destination = getattr(self, 'x_studio_destino', '') or ''
        
        # Contar cantidad de líneas/contenedores
        for line in self.order_line:
            if line.product_id:
                container_qty += int(line.product_uom_qty or 0)
        
        values = {
            'name': f"DO-{self.name}",
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id if self.user_id else False,
            'operation_type': operation_type,
            'active': True,
        }
        
        if commodity:
            values['commodity'] = commodity
        if container_qty:
            values['container_qty'] = container_qty
        if port_origin:
            values['port_origin'] = port_origin
        if port_destination:
            values['port_destination'] = port_destination
            
        return values

    def _create_operation_project(self):
        """
        Crea el proyecto de operación con sus tareas.
        """
        self.ensure_one()
        _logger.info(f"{'='*50}")
        _logger.info(f"CREATING DO FOR SALE ORDER: {self.name}")
        _logger.info(f"{'='*50}")
        
        # 1. Detectar tipo de operación
        operation_type = self._get_operation_type_from_template()
        _logger.info(f"Operation type detected: {operation_type}")
        
        # 2. Preparar valores del proyecto
        project_values = self._prepare_operation_project_values(operation_type)
        _logger.info(f"Project values: {project_values}")
        
        # 3. Buscar plantilla de proyecto
        template = self._get_project_template(operation_type)
        
        project = None
        
        if template:
            try:
                _logger.info(f"Copying template {template.name}...")
                
                # Guardar información de las tareas originales
                template_tasks_data = {}
                for task in template.with_context(active_test=False).task_ids:
                    task_data = {
                        'tag_ids': task.tag_ids.ids if task.tag_ids else [],
                        'stage_id': task.stage_id.id if task.stage_id else False,
                        'sequence': task.sequence or 10,
                    }
                    # Campos opcionales del módulo
                    if hasattr(task, 'is_client_visible'):
                        task_data['is_client_visible'] = task.is_client_visible
                    if hasattr(task, 'task_category'):
                        task_data['task_category'] = task.task_category
                    if hasattr(task, 'milestone_description'):
                        task_data['milestone_description'] = task.milestone_description
                    if hasattr(task, 'user_ids'):
                        task_data['user_ids'] = task.user_ids.ids
                    
                    template_tasks_data[task.name] = task_data
                
                _logger.info(f"Saved {len(template_tasks_data)} task templates")
                
                # Guardar etapas vinculadas a la plantilla
                template_stage_ids = template.type_ids.ids if template.type_ids else []
                _logger.info(f"Template has {len(template_stage_ids)} stages")
                
                # Copiar plantilla como nuevo proyecto
                project = template.with_context(active_test=False).copy(project_values)
                _logger.info(f"Created project: {project.name} (ID: {project.id})")
                
                # Vincular las mismas etapas al nuevo proyecto
                if template_stage_ids:
                    for stage in self.env['project.task.type'].browse(template_stage_ids):
                        if project.id not in stage.project_ids.ids:
                            stage.sudo().write({
                                'project_ids': [(4, project.id)]
                            })
                    _logger.info(f"Linked {len(template_stage_ids)} stages to new project")
                
                # Restaurar datos en las tareas copiadas
                for task in project.task_ids:
                    if task.name in template_tasks_data:
                        original = template_tasks_data[task.name]
                        update_vals = {}
                        
                        if original.get('tag_ids'):
                            update_vals['tag_ids'] = [(6, 0, original['tag_ids'])]
                        if original.get('stage_id'):
                            update_vals['stage_id'] = original['stage_id']
                        if original.get('sequence'):
                            update_vals['sequence'] = original['sequence']
                        if 'is_client_visible' in original:
                            update_vals['is_client_visible'] = original['is_client_visible']
                        if original.get('task_category'):
                            update_vals['task_category'] = original['task_category']
                        if original.get('milestone_description'):
                            update_vals['milestone_description'] = original['milestone_description']
                        if original.get('user_ids'):
                            update_vals['user_ids'] = [(6, 0, original['user_ids'])]
                        
                        if update_vals:
                            task.sudo().write(update_vals)
                
                _logger.info(f"Restored task data for {len(project.task_ids)} tasks")
                
            except Exception as e:
                _logger.error(f"Error copying template: {e}", exc_info=True)
                # Si falla la copia, crear proyecto básico
                project = self.env['project.project'].create(project_values)
                _logger.info(f"Created basic project (fallback): {project.name}")
        else:
            # Crear proyecto básico sin plantilla
            _logger.warning(f"No template found, creating basic project")
            project = self.env['project.project'].create(project_values)
            _logger.info(f"Created basic project: {project.name} (ID: {project.id})")
        
        # Vincular proyecto a la orden
        self.operation_project_id = project.id
        _logger.info(f"Linked project {project.id} to SO {self.name}")
        
        # Notificar en el chatter del proyecto
        try:
            project.message_post(
                body=_(
                    "Proyecto de operación creado automáticamente desde la orden de venta %s",
                    self.name
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        except Exception as e:
            _logger.warning(f"Could not post message to project: {e}")
        
        _logger.info(f"DO Creation completed successfully!")
        return project

    def action_confirm(self):
        """Override para crear proyecto al confirmar la orden"""
        res = super().action_confirm()
        
        for order in self:
            _logger.info(f"SO {order.name}: auto_create={order.auto_create_project}, has_project={bool(order.operation_project_id)}")
            
            if order.auto_create_project and not order.operation_project_id:
                try:
                    order._create_operation_project()
                except Exception as e:
                    _logger.error(f"Error creating operation project for {order.name}: {e}", exc_info=True)
                    # No bloqueamos la confirmación
        
        return res

    def action_view_operation_project(self):
        """Acción para abrir el proyecto de operación desde la orden"""
        self.ensure_one()
        if not self.operation_project_id:
            raise UserError(_("No hay proyecto de operación vinculado a esta orden."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Proyecto de Operación'),
            'res_model': 'project.project',
            'res_id': self.operation_project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
