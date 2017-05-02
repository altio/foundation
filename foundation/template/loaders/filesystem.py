from django.template.loaders import filesystem
from .base import FoundationMixin


class Loader(FoundationMixin, filesystem.Loader):

    def get_dirs(self, app_label=None, model_name=None):
        """ Hard override accepts app_label and model_name """
        return self.engine.dirs
