from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging

_logger = logging.getLogger(__name__)


class OmegaOperationsPortal(CustomerPortal):
    """
    Controlador del portal de operaciones para clientes OMEGA.
    Maneja la visualización de operaciones (DO) y sus hitos.
    """

    def _prepare_home_portal_values(self, counters):
        """Agregar contador de operaciones al home del portal"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'operation_count' in counters:
            try:
                partner = request.env.user.partner_id
                operation_count = request.env['project.project'].sudo().search_count([
                    ('partner_id', 'child_of', partner.commercial_partner_id.id),
                    ('operation_type', '!=', False),
                ])
                values['operation_count'] = operation_count
            except Exception as e:
                _logger.error(f"Error counting operations: {e}")
                values['operation_count'] = 0
        
        return values

    def _get_operation_domain(self, partner):
        """Dominio base para filtrar operaciones del cliente"""
        return [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('operation_type', '!=', False),
        ]

    def _safe_get_selection_label(self, record, field_name):
        """
        Obtiene el label de un campo selection de forma segura.
        Retorna string vacío si hay cualquier error.
        """
        try:
            if not record:
                return ''
            value = getattr(record, field_name, False)
            if not value:
                return ''
            field = record._fields.get(field_name)
            if not field or not hasattr(field, 'selection'):
                return str(value)
            selection = dict(field.selection)
            return selection.get(value, str(value))
        except Exception as e:
            _logger.warning(f"Error getting selection label for {field_name}: {e}")
            return ''

    def _is_task_completed(self, task):
        """
        Verifica si una tarea está completada (Odoo 18 compatible).
        """
        try:
            # Verificar estado nativo de Odoo 18
            if hasattr(task, 'state') and task.state:
                state = str(task.state).lower()
                if 'done' in state or 'cancel' in state:
                    return True
            
            # Verificar etapa cerrada
            if task.stage_id and task.stage_id.is_closed:
                return True
                
            return False
        except Exception:
            return False

    def _prepare_milestone_data(self, milestone):
        """
        Prepara los datos de un hito de forma segura para el template.
        """
        try:
            is_completed = self._is_task_completed(milestone)
            stage_name = milestone.stage_id.name if milestone.stage_id else 'Sin etapa'
            
            return {
                'id': milestone.id,
                'name': milestone.name or 'Sin nombre',
                'is_completed': is_completed,
                'is_alert': getattr(milestone, 'is_alert', False),
                'stage_name': stage_name,
                'stage_is_closed': milestone.stage_id.is_closed if milestone.stage_id else False,
                'description': getattr(milestone, 'milestone_description', '') or '',
                'completion_date': getattr(milestone, 'completion_date', False),
                'task_category': self._safe_get_selection_label(milestone, 'task_category'),
            }
        except Exception as e:
            _logger.error(f"Error preparing milestone data: {e}")
            return {
                'id': getattr(milestone, 'id', 0),
                'name': 'Error al cargar',
                'is_completed': False,
                'is_alert': False,
                'stage_name': '-',
                'stage_is_closed': False,
                'description': '',
                'completion_date': False,
                'task_category': '',
            }

    def _prepare_operation_values(self, operation, milestones):
        """
        Prepara todos los valores para el template de detalle de operación.
        Todos los valores son sanitizados para evitar errores de renderizado.
        """
        try:
            # Preparar datos de hitos
            milestones_data = [self._prepare_milestone_data(m) for m in milestones]
            
            # Contar alertas activas
            active_alerts = [m for m in milestones_data if m['is_alert'] and not m['is_completed']]
            
            # Contar completados
            completed_milestones = [m for m in milestones_data if m['is_completed']]
            
            return {
                'operation': operation,
                'milestones': milestones,
                'milestones_data': milestones_data,
                'page_name': 'operation_detail',
                
                # Labels de selections pre-calculados
                'operation_type_label': self._safe_get_selection_label(operation, 'operation_type'),
                'container_type_label': self._safe_get_selection_label(operation, 'container_type'),
                'bl_type_label': self._safe_get_selection_label(operation, 'bl_type'),
                'shipping_line_label': self._safe_get_selection_label(operation, 'shipping_line'),
                
                # Valores seguros (nunca None)
                'booking_number': operation.booking_number or '',
                'vessel_name': operation.vessel_name or '',
                'voyage_number': operation.voyage_number or '',
                'port_origin': operation.port_origin or '',
                'port_destination': operation.port_destination or '',
                'commodity': operation.commodity or '',
                'bl_number': operation.bl_number or '',
                'container_numbers': operation.container_numbers or '',
                'container_qty': operation.container_qty or 0,
                'imo_class': operation.imo_class or '',
                'is_dangerous_goods': operation.is_dangerous_goods or False,
                
                # Métricas
                'progress_percentage': operation.progress_percentage or 0,
                'milestone_count': operation.milestone_count or 0,
                'total_milestones': operation.total_milestones or 0,
                'has_alerts': operation.has_alerts or False,
                'active_alerts_count': len(active_alerts),
                'completed_count': len(completed_milestones),
                
                # Fechas (pueden ser False, el template las manejará)
                'etd_date': operation.etd_date,
                'eta_date': operation.eta_date,
                'doc_cutoff_date': operation.doc_cutoff_date,
                'cargo_cutoff_date': operation.cargo_cutoff_date,
                
                # Booleanos para mostrar/ocultar secciones
                'show_booking_info': bool(operation.booking_number or operation.vessel_name),
                'show_route_info': bool(operation.port_origin or operation.port_destination),
                'show_container_info': bool(operation.container_numbers or operation.container_type),
                'show_bl_info': bool(operation.bl_number),
                'show_dates_info': bool(operation.etd_date or operation.eta_date),
            }
        except Exception as e:
            _logger.error(f"Error preparing operation values: {e}", exc_info=True)
            # Retornar valores mínimos seguros
            return {
                'operation': operation,
                'milestones': milestones,
                'milestones_data': [],
                'page_name': 'operation_detail',
                'operation_type_label': '',
                'container_type_label': '',
                'bl_type_label': '',
                'shipping_line_label': '',
                'booking_number': '',
                'vessel_name': '',
                'voyage_number': '',
                'port_origin': '',
                'port_destination': '',
                'commodity': '',
                'bl_number': '',
                'container_numbers': '',
                'container_qty': 0,
                'imo_class': '',
                'is_dangerous_goods': False,
                'progress_percentage': 0,
                'milestone_count': 0,
                'total_milestones': 0,
                'has_alerts': False,
                'active_alerts_count': 0,
                'completed_count': 0,
                'etd_date': False,
                'eta_date': False,
                'doc_cutoff_date': False,
                'cargo_cutoff_date': False,
                'show_booking_info': False,
                'show_route_info': False,
                'show_container_info': False,
                'show_bl_info': False,
                'show_dates_info': False,
            }

    @http.route(['/my/operations', '/my/operations/page/<int:page>'], 
                type='http', auth='user', website=True)
    def portal_my_operations(self, page=1, sortby=None, **kw):
        """Lista de operaciones del cliente"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        Project = request.env['project.project'].sudo()
        
        domain = self._get_operation_domain(partner)
        
        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Fecha', 'order': 'create_date desc'},
            'name': {'label': 'Nombre', 'order': 'name'},
            'etd': {'label': 'ETD', 'order': 'etd_date desc'},
            'eta': {'label': 'ETA', 'order': 'eta_date desc'},
        }
        
        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Count
        operation_count = Project.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/operations",
            total=operation_count,
            page=page,
            step=10,
        )
        
        # Content
        operations = Project.search(
            domain,
            order=order,
            limit=10,
            offset=pager['offset']
        )
        
        values.update({
            'operations': operations,
            'page_name': 'operations',
            'pager': pager,
            'default_url': '/my/operations',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render(
            'omega_operations_portal.portal_my_operations', 
            values
        )

    @http.route(['/my/operation/<int:operation_id>'], 
                type='http', auth='user', website=True)
    def portal_operation_detail(self, operation_id, **kw):
        """Detalle de una operación específica"""
        try:
            partner = request.env.user.partner_id
            
            # Buscar operación con verificación de acceso
            operation = request.env['project.project'].sudo().search([
                ('id', '=', operation_id),
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ], limit=1)
            
            if not operation:
                _logger.warning(f"Operation {operation_id} not found for partner {partner.id}")
                return request.redirect('/my/operations')
            
            # Forzar recálculo de métricas
            operation._compute_milestone_count()
            operation._compute_has_alerts()
            
            # Obtener hitos/tareas visibles
            Task = request.env['project.task'].sudo()
            milestones = Task.search([
                ('project_id', '=', operation.id),
                '|',
                ('is_client_visible', '=', True),
                ('is_alert', '=', True),
            ], order='sequence, id')
            
            # Preparar valores con sanitización completa
            values = self._prepare_operation_values(operation, milestones)
            
            return request.render(
                'omega_operations_portal.portal_operation_detail',
                values
            )
            
        except Exception as e:
            _logger.error(f"Error loading operation detail {operation_id}: {e}", exc_info=True)
            return request.redirect('/my/operations')

    @http.route(['/my/operation/<int:operation_id>/task/<int:task_id>'], 
                type='http', auth='user', website=True)
    def portal_task_detail(self, operation_id, task_id, **kw):
        """Detalle de una tarea/hito específico"""
        try:
            partner = request.env.user.partner_id
            
            # Verificar acceso a la operación
            operation = request.env['project.project'].sudo().search([
                ('id', '=', operation_id),
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ], limit=1)
            
            if not operation:
                return request.redirect('/my/operations')
            
            # Obtener tarea
            task = request.env['project.task'].sudo().search([
                ('id', '=', task_id),
                ('project_id', '=', operation.id),
                '|',
                ('is_client_visible', '=', True),
                ('is_alert', '=', True),
            ], limit=1)
            
            if not task:
                return request.redirect(f'/my/operation/{operation_id}')
            
            # Preparar datos del hito
            milestone_data = self._prepare_milestone_data(task)
            
            values = {
                'operation': operation,
                'task': task,
                'milestone_data': milestone_data,
                'page_name': 'task_detail',
            }
            
            return request.render(
                'omega_operations_portal.portal_task_detail',
                values
            )
            
        except Exception as e:
            _logger.error(f"Error loading task detail: {e}", exc_info=True)
            return request.redirect(f'/my/operation/{operation_id}')
