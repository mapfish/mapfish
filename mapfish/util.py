from paste.script import templates

class MapFishTemplate(templates.Template):
    egg_plugins = ['MapFish']
    summary = 'Template for creating a basic MapFish project'
    required_templates = ['pylons']
    _template_dir = 'templates/project'
    overwrite = True
