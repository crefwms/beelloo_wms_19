from fastapi import FastAPI, UploadFile, File, Form
from typing import List
import xmlrpc.client

app = FastAPI(title="Beeloo Driver Portal")

# Odoo Integration Config (To be moved to env vars later)
ODOO_URL = "http://localhost:8069"
ODOO_DB = "medoo"
ODOO_USER = "admin"
ODOO_PWD = "admin"

def get_odoo_client():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PWD, {})
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return models, uid

@app.get("/")
async def root():
    return {"message": "Beeloo Driver Portal API"}

@app.get("/rma/{tracking_ref}")
async def get_rma(tracking_ref: str):
    models, uid = get_odoo_client()
    rma_ids = models.execute_kw(ODOO_DB, uid, ODOO_PWD, 'reverse.logistics.rma', 'search', [[['carrier_tracking_ref', '=', tracking_ref]]])
    if not rma_ids:
        return {"error": "RMA not found"}
    rma = models.execute_kw(ODOO_DB, uid, ODOO_PWD, 'reverse.logistics.rma', 'read', [rma_ids[0]], {'fields': ['name', 'partner_id', 'weight_declared', 'state']})
    return rma[0]

@app.post("/rma/{rma_id}/collect")
async def collect_rma(
    rma_id: int, 
    received_weight: float = Form(...), 
    files: List[UploadFile] = File(...)
):
    models, uid = get_odoo_client()
    
    # Update RMA with weight and move state
    models.execute_kw(ODOO_DB, uid, ODOO_PWD, 'reverse.logistics.rma', 'write', [[rma_id], {
        'weight_received': received_weight,
        'state': 'collected'
    }])
    
    # Note: Photo upload logic would involve creating ir.attachment in Odoo
    return {"status": "success", "rma_id": rma_id}
