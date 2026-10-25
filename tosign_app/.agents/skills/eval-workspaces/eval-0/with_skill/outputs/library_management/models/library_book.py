from odoo import models, fields, api

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Gerenciamento de Livros da Biblioteca'
    _order = 'title asc'

    title = fields.Char(string='Título', required=True)
    author_id = fields.Many2one('res.partner', string='Autor')
    isbn = fields.Char(string='ISBN')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('available', 'Disponível'),
        ('borrowed', 'Emprestado'),
        ('lost', 'Perdido'),
    ], string='Status', default='draft', tracking=True)
