"""Centralized prompt template registry."""

from typing import Dict


class PromptRegistry:
    """Manage all prompt templates across the platform."""

    _templates: Dict[str, Dict[str, str]] = {}

    @classmethod
    def register(cls, name: str, version: str, template: str) -> None:
        """Register a new version of a prompt template."""
        if name not in cls._templates:
            cls._templates[name] = {}
        cls._templates[name][version] = template

    @classmethod
    def get(cls, name: str, version: str = "latest") -> str:
        """Get a specific prompt template by name and version."""
        if name not in cls._templates:
            raise ValueError(f"Unknown prompt template: {name}")

        templates = cls._templates[name]

        if version == "latest":
            # Get the highest version string automatically
            version = max(templates.keys())

        if version not in templates:
            raise ValueError(f"Version {version} not found for {name}")

        return templates[version]

    @classmethod
    def list_versions(cls, name: str) -> list[str]:
        """List all registered versions of a specific template."""
        return list(cls._templates.get(name, {}).keys())


def get_prompt(name: str, version: str = "latest") -> str:
    """Convenience function to get a prompt template."""
    return PromptRegistry.get(name, version)
