import src.routers.start as start
import src.routers.admin as admin
import src.routers.add_user as add_user
import src.routers.custom as custom

bot_routers = [start.router, admin.router, add_user.router, custom.router]
