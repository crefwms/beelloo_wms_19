import json
import base64
import re
from odoo import models, fields, _
from odoo.exceptions import UserError

class OeaImportTrello(models.TransientModel):
    _name = 'oea.import.trello'
    _description = 'Import OEA Requirements from Trello JSON'

    json_file = fields.Binary(string='Trello JSON File', required=True)
    file_name = fields.Char(string='File Name')

    def action_import(self):
        if not self.json_file:
            raise UserError(_("Please upload a JSON file."))
        
        try:
            content = base64.b64decode(self.json_file)
            data = json.loads(content)
        except Exception as e:
            raise UserError(_("Invalid JSON file: %s") % str(e))
        
        cards = data.get('cards', [])
        lists = {l['id']: l['name'] for l in data.get('lists', [])}
        Requirement = self.env['oea.requirement']
        
        import_count = 0
        for card in cards:
            if card.get('closed'):
                continue
                
            name = card.get('name', '')
            trello_id = card.get('id')
            desc = card.get('desc', '')
            list_name = lists.get(card.get('idList'), '')
            
            # --- Advanced Parsing Logic ---
            
            # Detect if this card has sub-requirements (e.g., "5.1", "5.2" inside description)
            # We look for lines starting with digit.digit followed by some bold text or header
            sub_req_pattern = r'(\n\*\*(\d+\.\d+)\*\*[^\n]*|\n(\d+\.\d+)\s+)'
            sub_parts = re.split(sub_req_pattern, desc)
            
            # If no clear sub-reqs found, or it's just the main one repeating
            if len(sub_parts) <= 1:
                self._create_or_update_requirement(name, desc, list_name, trello_id)
                import_count += 1
                continue
            
            # If sub-reqs found, we need to process them
            # The split result with groups will be messy, let's use a better approach: find all occurrences and their text
            matches = list(re.finditer(sub_req_pattern, desc))
            
            # If matches found, iterate through them
            for idx, match in enumerate(matches):
                ref = match.group(2) or match.group(3)
                start = match.start()
                end = matches[idx+1].start() if idx + 1 < len(matches) else len(desc)
                sub_desc = desc[start:end].strip()
                
                # Derive a name for this sub-requirement
                sub_name = f"{ref} - {name.split('-', 1)[-1].strip()}" if '-' in name else f"{ref} - {name}"
                
                # Create/Update with a unique Trello ID for each sub-req to avoid collisions
                unique_trello_id = f"{trello_id}_{ref}"
                self._create_or_update_requirement(sub_name, sub_desc, list_name, unique_trello_id)
                import_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Complete'),
                'message': _('%s requirements/sub-items imported/updated.') % import_count,
                'sticky': False,
            }
        }

    def _create_or_update_requirement(self, name, desc, list_name, trello_id):
        Requirement = self.env['oea.requirement']
        
        # Extract Reference (Code) from name
        ref_match = re.search(r'^([\d\.]+)', name)
        reference = ref_match.group(1) if ref_match else ''
        
        # Split description based on typical OEA headers
        parts = re.split(r'(\*\*[^*]+:\*\*|ORIENTAÇÃO GENTIL:|GUIA DE IMPLEMENTAÇÃO|REQUISITOS:|OBJETIVO:)', desc)
        
        legal_desc = []
        orientation = []
        
        current_section = 'intro'
        for i in range(len(parts)):
            p = parts[i].strip()
            if not p: continue
            
            if '**OBJETIVO:**' in p or 'OBJETIVO:' in p or '**REQUISITOS:**' in p or 'REQUISITOS:' in p:
                current_section = 'legal'
                continue
            elif 'ORIENTAÇÃO GENTIL:' in p or 'GUIA DE IMPLEMENTAÇÃO' in p:
                current_section = 'orientation'
                continue
            elif p.startswith('**') and p.endswith(':**'):
                if any(x in p.upper() for x in ['ORIENTAÇÃO', 'GUIA', 'AÇÃO']):
                    current_section = 'orientation'
                else:
                    current_section = 'legal'
                continue
            
            if current_section == 'legal' or current_section == 'intro':
                legal_desc.append(p)
            else:
                orientation.append(p)

        def format_html(text_list):
            if not text_list: return ""
            raw = "\n".join(text_list).replace('\n', '<br/>')
            return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', raw)

        vals = {
            'name': name,
            'description': format_html(legal_desc),
            'orientation': format_html(orientation),
            'reference': reference,
            'category': list_name,
            'trello_card_id': trello_id,
        }
        
        if 'Baixa' in desc or '🟢' in desc: vals['complexity'] = 'low'
        elif 'Média' in desc or '🟡' in desc: vals['complexity'] = 'medium'
        elif 'Alta' in desc or '🔴' in desc: vals['complexity'] = 'high'
        
        if 'OEA-S' in name or 'Segurança' in list_name: vals['modality'] = 'security'
        elif 'OEA-C' in name or 'Conformidade' in list_name: vals['modality'] = 'compliance'

        existing = Requirement.search([('trello_card_id', '=', trello_id)], limit=1)
        if existing:
            existing.write(vals)
        else:
            Requirement.create(vals)
