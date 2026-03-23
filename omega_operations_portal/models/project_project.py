from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # === TIPO DE OPERACIÓN ===
    operation_type = fields.Selection([
        ('export_flex', 'Exportación Flexitanque'),
        ('export_iso', 'Exportación Isotanque'),
        ('import', 'Importación'),
        ('physical_op', 'Operación Física'),
    ], string='Tipo de Operación', tracking=True)

    # === INFORMACIÓN DE BOOKING ===
    booking_number = fields.Char(
        string='Número de Booking',
        tracking=True,
        help='Número de reserva asignado por la naviera'
    )
    vessel_name = fields.Char(
        string='Motonave',
        tracking=True,
        help='Nombre del buque'
    )
    voyage_number = fields.Char(
        string='Viaje',
        help='Número de viaje de la motonave'
    )
    
    # === NAVIERA ===
    shipping_line = fields.Selection([
        ('maersk', 'Maersk'),
        ('msc', 'MSC'),
        ('cma_cgm', 'CMA-CGM'),
        ('hapag', 'Hapag-Lloyd'),
        ('cosco', 'COSCO'),
        ('one', 'ONE'),
        ('evergreen', 'Evergreen'),
        ('other', 'Otra'),
    ], string='Naviera', tracking=True)

    # === RUTA ===
    port_origin = fields.Char(string='Puerto Origen')
    port_destination = fields.Char(string='Puerto Destino')
    
    # === FECHAS CLAVE ===
    etd_date = fields.Date(
        string='ETD (Fecha Zarpe)',
        tracking=True,
        help='Estimated Time of Departure'
    )
    eta_date = fields.Date(
        string='ETA (Fecha Arribo)',
        tracking=True,
        help='Estimated Time of Arrival'
    )
    doc_cutoff_date = fields.Datetime(
        string='Cierre Documental',
        tracking=True
    )
    cargo_cutoff_date = fields.Datetime(
        string='Cierre de Carga',
        tracking=True
    )

    # === CONTENEDORES ===
    container_type = fields.Selection([
        ('20_st', '20 ST'),
        ('40_st', '40 ST'),
        ('40_hc', '40 HC'),
        ('20_tk', '20 TK (Isotanque)'),
        ('20_kt', '20 KT'),
    ], string='Tipo de Contenedor')
    container_numbers = fields.Text(
        string='Números de Contenedor',
        help='Lista de contenedores separados por coma o línea'
    )
    container_qty = fields.Integer(
        string='Cantidad de Contenedores',
        default=1
    )

    # === DOCUMENTOS ===
    bl_number = fields.Char(
        string='Número de BL',
        tracking=True,
        help='Bill of Lading Number'
    )
    bl_type = fields.Selection([
        ('original_origin', 'Original en Origen'),
        ('original_dest', 'Original en Destino'),
        ('seawaybill', 'Seawaybill'),
    ], string='Tipo de Emisión BL')

    # === CARGA ===
    commodity = fields.Char(
        string='Commodity',
        help='Tipo de mercancía'
    )
    is_dangerous_goods = fields.Boolean(
        string='Mercancía Peligrosa (IMO)',
        default=False
    )
    imo_class = fields.Char(string='Clase IMO')

    # === MÉTRICAS ===
    # NOTA: Usamos store=False para evitar problemas con @api.depends
    # Las métricas se calculan en tiempo real
    milestone_count = fields.Integer(
        string='Hitos Completados',
        compute='_compute_milestone_count',
        store=False
    )
    total_milestones = fields.Integer(
        string='Total Hitos',
        compute='_compute_milestone_count',
        store=False
    )
    progress_percentage = fields.Float(
        string='% Progreso',
        compute='_compute_milestone_count',
        store=False
    )
    has_alerts = fields.Boolean(
        string='Tiene Alertas',
        compute='_compute_has_alerts',
        store=False
    )

    def _is_task_done(self, task):
        """
        Verifica si una tarea está completada en Odoo 18.
        Verifica múltiples condiciones para máxima compatibilidad.
        """
        try:
            # Método 1: Verificar campo 'state' de Odoo 18
            if hasattr(task, 'state') and task.state:
                state = str(task.state).lower()
                if 'done' in state or 'cancel' in state:
                    return True
            
            # Método 2: Verificar etapa cerrada
            if task.stage_id:
                if hasattr(task.stage_id, 'is_closed') and task.stage_id.is_closed:
                    return True
                # Alternativa: verificar por nombre de etapa
                if task.stage_id.name:
                    stage_name = task.stage_id.name.upper()
                    if 'COMPLETADO' in stage_name or 'DONE' in stage_name or 'CERRADO' in stage_name:
                        return True
            
            return False
        except Exception as e:
            _logger.warning(f"Error checking task done status: {e}")
            return False

    @api.depends('task_ids')
    def _compute_milestone_count(self):
        """
        Calcula el conteo de hitos completados y el porcentaje de progreso.
        Solo cuenta tareas que son visibles para el cliente (is_client_visible=True).
        """
        for project in self:
            try:
                # Filtrar solo tareas que son hitos visibles al cliente
                all_tasks = project.task_ids or []
                milestone_tasks = [t for t in all_tasks if getattr(t, 'is_client_visible', False)]
                
                # Contar hitos completados
                completed = [t for t in milestone_tasks if self._is_task_done(t)]
                
                total = len(milestone_tasks)
                done = len(completed)
                
                project.total_milestones = total
                project.milestone_count = done
                project.progress_percentage = (done / total * 100) if total > 0 else 0.0
                
            except Exception as e:
                _logger.error(f"Error computing milestone count for project {project.id}: {e}")
                project.total_milestones = 0
                project.milestone_count = 0
                project.progress_percentage = 0.0

    @api.depends('task_ids')
    def _compute_has_alerts(self):
        """
        Verifica si el proyecto tiene alertas activas (no cerradas).
        """
        for project in self:
            try:
                all_tasks = project.task_ids or []
                # Buscar tareas que son alertas y NO están completadas
                alert_tasks = [
                    t for t in all_tasks 
                    if getattr(t, 'is_alert', False) and not self._is_task_done(t)
                ]
                project.has_alerts = bool(alert_tasks)
            except Exception as e:
                _logger.error(f"Error computing has_alerts for project {project.id}: {e}")
                project.has_alerts = False
