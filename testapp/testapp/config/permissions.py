from authkit.permissions import HasAuthKitRole, ValidAuthKitUser
from mapfish.controllers.security import Deny

permissions = {
    "application": ValidAuthKitUser(),
    "application.widgets.edit": HasAuthKitRole("editor"),
    "widgets.print.dpi.100": Deny()
}
