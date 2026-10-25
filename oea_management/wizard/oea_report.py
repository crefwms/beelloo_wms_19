from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from collections import defaultdict


class OeaReportWizard(models.TransientModel):
    _name = 'oea.report.wizard'
    _description = 'Wizard de Relatórios OEA'

    report_type = fields.Selection([
        ('compliance', 'Conformidade por Requisito'),
        ('audit', 'Relatório de Auditoria'),
        ('consolidated', 'Consolidado Geral'),
        ('evolution', 'Evolução Temporal'),
        ('risk', 'Riscos e Incidentes'),
    ], string='Tipo de Relatório', required=True, default='compliance')

    requirement_ids = fields.Many2many(
        'oea.requirement',
        string='Requisitos',
        help='Deixe vazio para todos os requisitos'
    )

    audit_id = fields.Many2one(
        'oea.audit',
        string='Auditoria',
        help='Selecione uma auditoria específica'
    )

    date_from = fields.Date(string='Data Inicial')
    date_to = fields.Date(string='Data Final')

    modality = fields.Selection([
        ('compliance', 'OEA-Conformidade'),
        ('security', 'OEA-Segurança'),
        ('both', 'Ambas'),
    ], string='Modalidade')

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company
    )

    def action_generate_report(self):
        self.ensure_one()
        
        if self.report_type == 'compliance':
            return self._generate_compliance_report()
        elif self.report_type == 'audit':
            return self._generate_audit_report()
        elif self.report_type == 'consolidated':
            return self._generate_consolidated_report()
        elif self.report_type == 'evolution':
            return self._generate_evolution_report()
        elif self.report_type == 'risk':
            return self._generate_risk_report()
        
        return {'type': 'ir.actions.act_window_close'}

    def _get_requirement_domain(self):
        domain = [('active', '=', True)]
        if self.requirement_ids:
            domain.append(('id', 'in', self.requirement_ids.ids))
        if self.modality:
            domain.append(('modality', '=', self.modality))
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        return domain

    def _generate_compliance_report(self):
        requirements = self.env['oea.requirement'].search(self._get_requirement_domain())
        
        report_data = []
        for req in requirements:
            items = self.env['oea.requirement.item'].search([
                ('requirement_id', '=', req.id),
                ('active', '=', True),
            ])
            
            if self.date_from:
                items = items.filtered(lambda i: i.performed_date >= self.date_from if i.performed_date else False)
            if self.date_to:
                items = items.filtered(lambda i: i.performed_date <= self.date_to if i.performed_date else False)
            
            validated = items.filtered(lambda i: i.state == 'validated')
            in_progress = items.filtered(lambda i: i.state == 'in_progress')
            pending = items.filtered(lambda i: i.state == 'pending_review')
            draft = items.filtered(lambda i: i.state == 'draft')
            rejected = items.filtered(lambda i: i.state == 'rejected')
            na = items.filtered(lambda i: i.state == 'not_applicable')
            
            total = len(items)
            progress = (len(validated) / total * 100) if total > 0 else 0
            
            report_data.append({
                'requirement': req,
                'total_items': total,
                'validated': len(validated),
                'in_progress': len(in_progress),
                'pending': len(pending),
                'draft': len(draft),
                'rejected': len(rejected),
                'not_applicable': len(na),
                'progress': round(progress, 1),
            })
        
        return self._print_report('oea_management.oea_compliance_report', {
            'docs': report_data,
            'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else '',
            'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else '',
            'modality': self.modality or 'Todas',
        })

    def _generate_audit_report(self):
        if not self.audit_id:
            raise UserError('Selecione uma auditoria para gerar o relatório.')
        
        audit = self.audit_id
        lines = audit.line_ids
        
        report_data = [{
            'audit': audit,
            'total_lines': len(lines),
            'validated': len(lines.filtered(lambda l: l.action_item_id.state == 'validated')),
            'in_progress': len(lines.filtered(lambda l: l.action_item_id.state == 'in_progress')),
            'pending': len(lines.filtered(lambda l: l.action_item_id.state == 'pending_review')),
            'draft': len(lines.filtered(lambda l: l.action_item_id.state == 'draft')),
            'rejected': len(lines.filtered(lambda l: l.action_item_id.state == 'rejected')),
            'not_applicable': len(lines.filtered(lambda l: l.action_item_id.state == 'not_applicable')),
            'progress': round(audit.progress, 1),
        }]
        
        return self._print_report('oea_management.oea_audit_report', {
            'docs': report_data,
            'date': fields.Date.today().strftime('%d/%m/%Y'),
        })

    def _generate_consolidated_report(self):
        items = self.env['oea.requirement.item'].search([
            ('active', '=', True),
            ('company_id', '=', self.company_id.id),
        ])
        
        if self.date_from:
            items = items.filtered(lambda i: i.performed_date >= self.date_from if i.performed_date else False)
        if self.date_to:
            items = items.filtered(lambda i: i.performed_date <= self.date_to if i.performed_date else False)
        
        by_modality = defaultdict(lambda: {'total': 0, 'validated': 0})
        by_type = defaultdict(lambda: {'total': 0, 'validated': 0})
        by_requirement = defaultdict(lambda: {'total': 0, 'validated': 0})
        
        for item in items:
            mod = item.requirement_modality or 'both'
            typ = item.requirement_type or 'operational'
            req = item.requirement_id.name or 'Sem Requisito'
            
            by_modality[mod]['total'] += 1
            by_type[typ]['total'] += 1
            by_requirement[req]['total'] += 1
            
            if item.state == 'validated':
                by_modality[mod]['validated'] += 1
                by_type[typ]['validated'] += 1
                by_requirement[req]['validated'] += 1
        
        for key in by_modality:
            total = by_modality[key]['total']
            validated = by_modality[key]['validated']
            by_modality[key]['progress'] = round((validated / total * 100) if total > 0 else 0, 1)
        
        for key in by_type:
            total = by_type[key]['total']
            validated = by_type[key]['validated']
            by_type[key]['progress'] = round((validated / total * 100) if total > 0 else 0, 1)
        
        for key in by_requirement:
            total = by_requirement[key]['total']
            validated = by_requirement[key]['validated']
            by_requirement[key]['progress'] = round((validated / total * 100) if total > 0 else 0, 1)
        
        total_items = len(items)
        validated = len(items.filtered(lambda i: i.state == 'validated'))
        overall_progress = round((validated / total_items * 100) if total_items > 0 else 0, 1)
        
        return self._print_report('oea_management.oea_consolidated_report', {
            'total_items': total_items,
            'validated': validated,
            'overall_progress': overall_progress,
            'by_modality': dict(by_modality),
            'by_type': dict(by_type),
            'by_requirement': dict(by_requirement),
            'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else '',
            'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else '',
            'date': fields.Date.today().strftime('%d/%m/%Y'),
        })

    def _generate_evolution_report(self):
        Item = self.env['oea.requirement.item']
        
        if not self.date_from:
            self.date_from = fields.Date.today() - timedelta(days=90)
        if not self.date_to:
            self.date_to = fields.Date.today()
        
        items = Item.search([
            ('performed_date', '>=', self.date_from),
            ('performed_date', '<=', self.date_to),
            ('active', '=', True),
            ('company_id', '=', self.company_id.id),
        ])
        
        daily_data = defaultdict(lambda: {'validated': 0, 'total': 0})
        
        for item in items:
            if item.performed_date:
                date_key = item.performed_date.date()
                daily_data[date_key]['total'] += 1
                if item.state == 'validated':
                    daily_data[date_key]['validated'] += 1
        
        sorted_dates = sorted(daily_data.keys())
        cumulative = 0
        evolution = []
        
        for date in sorted_dates:
            cumulative += daily_data[date]['validated']
            evolution.append({
                'date': date.strftime('%d/%m/%Y'),
                'validated': daily_data[date]['validated'],
                'cumulative': cumulative,
            })
        
        return self._print_report('oea_management.oea_evolution_report', {
            'evolution': evolution,
            'date_from': self.date_from.strftime('%d/%m/%Y'),
            'date_to': self.date_to.strftime('%d/%m/%Y'),
            'date': fields.Date.today().strftime('%d/%m/%Y'),
        })

    def _generate_risk_report(self):
        risks = self.env['oea.risk'].search([
            ('company_id', '=', self.company_id.id),
        ])
        
        incidents = self.env['oea.security.incident'].search([
            ('company_id', '=', self.company_id.id),
        ])
        
        if self.date_from:
            risks = risks.filtered(lambda r: r.create_date.date() >= self.date_from if r.create_date else False)
            incidents = incidents.filtered(lambda i: i.incident_date.date() >= self.date_from if i.incident_date else False)
        
        if self.date_to:
            risks = risks.filtered(lambda r: r.create_date.date() <= self.date_to if r.create_date else False)
            incidents = incidents.filtered(lambda i: i.incident_date.date() <= self.date_to if i.incident_date else False)
        
        by_rating = defaultdict(int)
        by_state = defaultdict(int)
        by_severity = defaultdict(int)
        
        for risk in risks:
            by_rating[risk.risk_rating or 'low'] += 1
            by_state[risk.state or 'draft'] += 1
        
        for incident in incidents:
            by_severity[incident.severity or 'low'] += 1
        
        return self._print_report('oea_management.oea_risk_report', {
            'total_risks': len(risks),
            'total_incidents': len(incidents),
            'by_rating': dict(by_rating),
            'by_state': dict(by_state),
            'by_severity': dict(by_severity),
            'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else '',
            'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else '',
            'date': fields.Date.today().strftime('%d/%m/%Y'),
        })

    def _print_report(self, report_name, data):
        return self.env.ref(report_name).report_action(self, data=data)


class OeaComplianceReport(models.AbstractModel):
    _name = 'report.oea_management.oea_compliance_report'
    _description = 'Relatório de Conformidade OEA'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = data.get('docs', [])
        
        return {
            'doc_ids': docids,
            'doc_model': 'oea.requirement',
            'docs': docs,
            'date': fields.Date.today().strftime('%d/%m/%Y'),
            'date_from': data.get('date_from', ''),
            'date_to': data.get('date_to', ''),
            'modality': data.get('modality', 'Todas'),
        }


class OeaAuditReport(models.AbstractModel):
    _name = 'report.oea_management.oea_audit_report'
    _description = 'Relatório de Auditoria OEA'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = data.get('docs', [])
        
        return {
            'doc_ids': docids,
            'doc_model': 'oea.audit',
            'docs': docs,
            'date': fields.Date.today().strftime('%d/%m/%Y'),
        }


class OeaConsolidatedReport(models.AbstractModel):
    _name = 'report.oea_management.oea_consolidated_report'
    _description = 'Relatório Consolidado OEA'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'total_items': data.get('total_items', 0),
            'validated': data.get('validated', 0),
            'overall_progress': data.get('overall_progress', 0),
            'by_modality': data.get('by_modality', {}),
            'by_type': data.get('by_type', {}),
            'by_requirement': data.get('by_requirement', {}),
            'date_from': data.get('date_from', ''),
            'date_to': data.get('date_to', ''),
            'date': data.get('date', ''),
        }


class OeaEvolutionReport(models.AbstractModel):
    _name = 'report.oea_management.oea_evolution_report'
    _description = 'Relatório de Evolução OEA'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'evolution': data.get('evolution', []),
            'date_from': data.get('date_from', ''),
            'date_to': data.get('date_to', ''),
            'date': data.get('date', ''),
        }


class OeaRiskReport(models.AbstractModel):
    _name = 'report.oea_management.oea_risk_report'
    _description = 'Relatório de Riscos e Incidentes OEA'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'total_risks': data.get('total_risks', 0),
            'total_incidents': data.get('total_incidents', 0),
            'by_rating': data.get('by_rating', {}),
            'by_state': data.get('by_state', {}),
            'by_severity': data.get('by_severity', {}),
            'date_from': data.get('date_from', ''),
            'date_to': data.get('date_to', ''),
            'date': data.get('date', ''),
        }
