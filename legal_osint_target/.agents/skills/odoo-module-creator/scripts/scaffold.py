import os
import sys

def create_module(module_name, dest_path):
    # Ensure the destination path exists
    module_dir = os.path.join(dest_path, module_name)
    if os.path.exists(module_dir):
        print(f"Error: Module '{module_name}' already exists in '{dest_path}'")
        sys.exit(1)

    # Standard directory structure
    subdirs = [
        'controllers',
        'data',
        'models',
        'security',
        'static',
        'views',
        'wizard'
    ]

    # Create module root
    os.makedirs(module_dir)
    print(f"Created module root: {module_dir}")

    # Create subdirectories and __init__.py files
    for subdir in subdirs:
        subdir_path = os.path.join(module_dir, subdir)
        os.makedirs(subdir_path)
        print(f"Created subdirectory: {subdir_path}")

        # models, controllers, wizard need __init__.py
        if subdir in ['models', 'controllers', 'wizard']:
            with open(os.path.join(subdir_path, '__init__.py'), 'w') as f:
                f.write("# -*- coding: utf-8 -*-\n")
                
    # Create base __init__.py
    with open(os.path.join(module_dir, '__init__.py'), 'w') as f:
        f.write("# -*- coding: utf-8 -*-\n\nfrom . import models\n")
        
    # Create __manifest__.py
    manifest_content = f"""{{
    'name': '{module_name.replace("_", " ").title()}',
    'version': '18.0.1.0.0',
    'summary': 'Short summary of the module',
    'description': \"\"\"
        Detailed description of the module.
    \"\"\",
    'category': 'Uncategorized',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}}
"""
    with open(os.path.join(module_dir, '__manifest__.py'), 'w') as f:
        f.write(manifest_content)
        print(f"Created __manifest__.py")

    # Create empty security file
    with open(os.path.join(module_dir, 'security', 'ir.model.access.csv'), 'w') as f:
        f.write("id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n")
        print(f"Created empty ir.model.access.csv")

    # Create dummy views file
    views_content = """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Template views for the module -->
</odoo>
"""
    with open(os.path.join(module_dir, 'views', 'views.xml'), 'w') as f:
        f.write(views_content)
    
    with open(os.path.join(module_dir, 'views', 'menus.xml'), 'w') as f:
        f.write(views_content)
    print(f"Created views/views.xml and views/menus.xml")

    print(f"Module '{module_name}' created successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scaffold.py <module_name> <dest_path>")
        sys.exit(1)
    
    create_module(sys.argv[1], sys.argv[2])
