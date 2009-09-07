from paste.script.templates import Template, var
from tempita import paste_script_template_renderer

class MapFishTemplate(Template):
    egg_plugins = ['MapFish']
    summary = 'MapFish application template'
    template_renderer=staticmethod(paste_script_template_renderer)
    required_templates = ['pylons']
    _template_dir = 'templates/project'
    overwrite = True
