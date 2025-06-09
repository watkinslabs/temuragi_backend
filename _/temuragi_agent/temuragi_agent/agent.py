import os
import yaml
from ai_manager import AIManager
from wl_module_builder import ModuleBuilder
from version_manager import VersionManager
from .config import load_config

class TemuragiModuleAgent:
    def __init__(self, config_path=None):
        self.config = load_config(config_path)
        self.ai = AIManager(self.config)
        self.builder = ModuleBuilder()
        self.version = VersionManager()
        self.spec_file = "spec.yaml"
        self.registry_file = "registry.yaml"

    def discover(self):
        prompt = (
            "Determine module_name, context, models, services, "
            "routes, and hooks for a Temuragi module."
        )
        resp = self.ai.chat("discover", {})
        spec = yaml.safe_load(resp)
        with open(self.spec_file, "w") as f:
            yaml.safe_dump(spec, f)

    def confirm(self):
        with open(self.spec_file) as f:
            spec = yaml.safe_load(f)
        print(yaml.safe_dump(spec, sort_keys=False))
        ans = input("Looks good? [Y/n] ").strip().lower()
        if ans not in ("y","", "yes"):
            print("Edit spec.yaml and re-run confirm.")
            exit(1)

    def generate_step(self, step):
        spec = yaml.safe_load(open(self.spec_file))
        registry = {}
        if os.path.exists(self.registry_file):
            registry = yaml.safe_load(open(self.registry_file))
        fragment = spec.get(f"{step}s")  # e.g. spec["models"]
        payload = {"module": spec["module_name"], "context": spec["context"], step: fragment}
        resp = self.ai.chat(f"generate_{step}", payload)
        files = yaml.safe_load(resp)  # expect {"files": {path: content}, "signatures": {...}}
        for path, content in files["files"].items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        registry.setdefault(f"{step}s", []).append(files["signatures"])
        with open(self.registry_file, "w") as f:
            yaml.safe_dump(registry, f)

    def generate_all(self):
        for step in ["model","service","route","hook"]:
            self.generate_step(step)
            ans = input(f"{step} generated. Continue? [Y/n] ").strip().lower()
            if ans not in ("y","", "yes"):
                break
