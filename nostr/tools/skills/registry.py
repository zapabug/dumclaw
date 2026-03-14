import os
import json

def discover_skills():
    """
    Discover all skills in the skills directory.
    Returns a dict mapping skill name to its metadata and entrypoint.
    """
    skills_dir = os.path.dirname(__file__)
    skill_dirs = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
    skills = {}
    for skill_name in skill_dirs:
        manifest_path = os.path.join(skills_dir, skill_name, 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            skills[skill_name] = {
                'manifest': manifest,
                'entrypoint': manifest.get('entrypoint'),
                'dir': os.path.join(skills_dir, skill_name)
            }
    return skills

def load_skill_entrypoint(skill_info):
    """
    Load the execute function from a skill's execute.py.
    """
    exec_path = os.path.join(skill_info['dir'], 'execute.py')
    if os.path.exists(exec_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location('execute', exec_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, 'execute', None)
    return None

if __name__ == '__main__':
    discovered = discover_skills()
    print('Discovered skills:', list(discovered.keys()))
    for name, info in discovered.items():
        func = load_skill_entrypoint(info)
        print(f'Skill {name} entrypoint: {func}')