# ------------------------------------------------------
# INJECTION
# ------------------------------------------------------
from http_server import InjectedServer
# ------------------------------------------------------
# END INJECTION
# ------------------------------------------------------


def build_interface(): 
    ...
    # ------------------------------------------------------
    # INJECTION
    # ------------------------------------------------------
    injected_server = InjectedServer(custom_hook)
    # ------------------------------------------------------
    # END OF INJECTION
    # ------------------------------------------------------

    return demo