---
name: odoo-module-creator
description: Create and manage Odoo 18 modules following technical best practices for Python, XML, and security. Use this skill when the user wants to start a new Odoo project, add models/views to an existing one, or refactor Odoo code to align with best practices (v18).
---

# Odoo Module Creator

This skill provides a structured workflow and best practices for developing Odoo 18 modules. It ensures code quality, maintainability, and compatibility with Odoo's architectural patterns.

## 1. Module Structure
Always follow the standard Odoo directory structure:
```
module_name/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── data/           # XML files for non-view data (e.g., cron, sequences)
├── models/         # Python models
│   ├── __init__.py
│   └── example_model.py
├── security/       # access rights and record rules
│   └── ir.model.access.csv
├── static/         # assets (css, js, img)
├── views/          # XML views
│   ├── example_views.xml
│   └── menu_views.xml
└── wizard/         # transient models and wizards
```

## 2. Manifest (`__manifest__.py`)
- **Version**: Always use `18.0.x.y.z` format.
- **License**: Default to `LGPL-3`.
- **Dependencies**: Explicitly list all required Odoo modules (e.g., `base`, `mail`, `web`).
- **Data**: Organize files logically - security first, then data, then views.

## 3. Python Best Practices
- **Naming**: Class names in CamelCase, `_name` and `_inherit` using dots (`module.model`).
- **Field Definitions**: 
    - Always include a `string` parameter.
    - Use `required=True` only when strictly necessary.
    - Use `tracking=True` for important fields (requires `mail` dependency).
- **API Decorators**: 
    - Use `@api.depends` for computed fields.
    - Use `@api.constrains` for validation.
    - Use `@api.onchange` sparingly (prefer `@api.depends` if possible).
- **Docstrings**: Provide a brief `_description` for every model.

## 4. XML Best Practices
- **View IDs**: Follow pattern `view_model_name_type` (e.g., `view_tosign_document_form`).
- **Indentation**: 4 spaces.
- **Header/Sheet**: In form views, use `<header>` for buttons and status bars, and `<sheet>` for the main content.
- **Priority**: Use `<field name="priority" eval="X"/>` if multiple views exist for the same model.
- **List Views (Odoo 18)**: In Odoo 18, use the `<list>` tag instead of `<tree>` for defining list views. While `<tree>` still works for backward compatibility, `<list>` is the standard.
    ```xml
    <record id="view_model_list" model="ir.ui.view">
        <field name="name">model.list</field>
        <field name="model">model.name</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
            </list>
        </field>
    </record>
    ```

## 5. Security
- **Access Rights**: Every new model MUST have an entry in `ir.model.access.csv`.
- **Record Rules**: Use XML files in `security/` for row-level access control.

## 6. Helper Script
You can use the `scaffold.py` script to quickly generate a module skeleton.
`python .agents/skills/odoo-module-creator/scripts/scaffold.py <module_name> <dest_path>`
