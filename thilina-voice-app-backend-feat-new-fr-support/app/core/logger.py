import logging
from rich.console import Console
from rich.logging import RichHandler
console = Console()

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
)],)

logger = logging.getLogger("Dispatch backend")