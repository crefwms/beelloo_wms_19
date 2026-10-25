from odoo import models, fields

class library_book(models.Model):
    _name = 'library.book'

    title = fields.Char('Title', required=True)
    author_id = fields.Many2one('res.partner')
    isbn = fields.Char('ISBN')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('avail', 'Available'),
    ], default='draft')
