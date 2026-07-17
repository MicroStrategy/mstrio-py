import html
from functools import cache
from pathlib import Path

TEMPLATES_FOLDER = Path(__file__).parent / "templates"


class Raw(str):
    """Marker for raw, already-safe HTML content."""


class Template:
    """Class to handle HTML templates for SQL diff generation.

    This class reads a template file and provides methods to fill it with
    data. It uses Python's string formatting to replace placeholders in the
    template with actual values."""

    _content: str
    TEMPLATE_FILE_SUFFIX = ".html"

    def __init__(
        self,
        template_name: str | Path,
        /,
        **context: "str | Template | Raw | list[str | Template | Raw]",
    ) -> None:
        """Initialize the Template object.

        Args:
            template_name (str | Path): Name of the template
                (without the suffix)
            **context: Additional context variables to be used in the template.
                Each context variable can be a:
                - literal
                - Template object
                - list of any of the above
        """
        self._content = Template._get_file_data(
            TEMPLATES_FOLDER / f"{template_name}{self.TEMPLATE_FILE_SUFFIX}"
        )
        self.context = context

    def __str__(self) -> str:
        """Return the rendered template as a string."""
        return self.render()

    def get_raw(self) -> str:
        """Get the raw content of the template.

        _For templates without any values to fill in dynamically._"""
        return self._content

    def render(self) -> str:
        """Render the template with the context
        provided during initialization."""
        resolved = {}
        for key, value in self.context.items():
            if isinstance(value, (Template, Raw)):
                resolved[key] = str(value)
            elif isinstance(value, list):
                resolved[key] = "".join(str(v) for v in value)
            else:
                resolved[key] = html.escape(str(value))
        return self._content.format(**resolved)

    @staticmethod
    @cache
    def _get_file_data(path: str | Path) -> str:
        """Read the content of a file and return it as a string.

        Caches the output based on a path to avoid re-reading the file
            multiple times.

        Args:
            path (str | Path): The path to the file.

        Returns:
            str: The content of the file.
        """
        with open(path, encoding="utf-8") as file:
            return file.read()


class CssTemplate(Template):
    TEMPLATE_FILE_SUFFIX = ".css"

    def render(self) -> str:
        return self._content
