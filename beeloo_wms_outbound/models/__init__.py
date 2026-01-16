from . import beeloo_shelf_life_mixin # (Mixin não depende de ninguém)
from . import res_partner           # <-- Carrega o campo do cliente PRIMEIRO
from . import stock_move            # (Depende do res_partner)
from . import beeloo_shelf_life_flow  # (Modelo de Flow)
from . import beeloo_shelf_life_wizard
from . import stock_picking