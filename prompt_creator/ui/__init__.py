"""Gradio UI for the Prompt Creator system."""

# Lazy imports to avoid circular dependencies and module issues
__all__ = [
    "create_app",
    "PromptCreatorUI",
    "create_workflow_creator_app",
]


def create_app(*args, **kwargs):
    """Create the basic Gradio app."""
    from .gradio_app import create_app as _create_app
    return _create_app(*args, **kwargs)


def create_workflow_creator_app(*args, **kwargs):
    """Create the workflow creator app."""
    from .workflow_creator_app import create_workflow_creator_app as _create
    return _create(*args, **kwargs)
