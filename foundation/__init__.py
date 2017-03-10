__version__ = '0.1.0a0.dev2'

default_app_config = 'foundation.config.FoundationConfig'


"""
Plan is to eventually actually allow for the declaration of per-Site Backends
and get them from a SiteBackend registry.  For now, using a singleton list.
"""

backends = []


def get_backend(site=None):
    global backends
    if not backends:
        from .backend import Backend
        backends.append(Backend())
    return backends[0]
