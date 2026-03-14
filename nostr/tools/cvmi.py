# CVMI - Context Virtual Machine Interface
# Dynamically loads skills from the skills registry.

import os
import json
from .skills.registry import discover_skills

def get_available_skills():
    """Return a dict of skill names to their manifest and entrypoint."""
    return discover_skills()

def get_skill_entrypoint(skill_name):
    """Get the execute function for a given skill."""
    skills = discover_skills()
    skill_info = skills.get(skill_name)
    if skill_info:
        return skill_info['dir'], skill_info['entrypoint']
    return None, None

def load_skill(skill_name):
    """Load and return the execute function for a skill."""
    skills = discover_skills()
    skill_info = skills.get(skill_name)
    if not skill_info:
        return None
    exec_path = os.path.join(skill_info['dir'], 'execute.py')
    if os.path.exists(exec_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location('execute', exec_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, 'execute', None)
    return None

if __name__ == '__main__':
    skills = get_available_skills()
    print('Available skills:', list(skills.keys()))
    for name, info in skills.items():
        func = load_skill(name)
        print(f'Skill {name} entrypoint: {func}')