"""
This module defines abstract base classes and implementations for formatting Hap objects.
"""
import abc
import io # Still needed if we fall back to StringIO for some reason, but aiming for record=True
import itertools.filterfalse # As requested
from typing import List, Any, Optional, cast # List for <3.9 compatibility

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group # For grouping renderables in Panel
from rich.padding import Padding # For layout within Panel

from hapless.config import config
from hapless.hap import Status # For Status enum logic

# Handle importlib.metadata for Python 3.7 and 3.8+
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError # type: ignore


class Formatter(abc.ABC):
    """
    Abstract base class for formatting Hap objects.
    """

    @abc.abstractmethod
    def format_haps(self, haps_data: List[dict]) -> str:
        """
        Formats a list of Hap objects.

        Args:
            haps_data: A list of dictionaries, where each dictionary
                       represents a Hap object.

        Returns:
            A formatted string representation of the list of Hap objects.
        """
        pass

    @abc.abstractmethod
    def format_hap(self, hap_data: dict) -> str:
        """
        Formats a single Hap object.

        Args:
            hap_data: A dictionary representing a Hap object.

        Returns:
            A formatted string representation of the Hap object.
        """
        pass


class TableFormatter(Formatter):
    """
    Formats Hap objects into a rich Table or Panel, returning them as strings.
    """

    def __init__(self, verbose: bool = False):
        """
        Initializes the TableFormatter.

        Args:
            verbose: If True, output will be more detailed.
        """
        self.verbose = verbose
        # Using record=True to capture output, force_terminal ensures styles
        self.console = Console(highlight=False, record=True, force_terminal=True)

    def _clear_console_record(self):
        """Clears the console's current recording."""
        # The `clear=True` on print, or `console.clear()` might be needed.
        # `export_text()` itself doesn't clear.
        # Let's try `self.console.clear()` before each print operation.
        # According to Rich docs, Console(record=True) means subsequent prints append.
        # We need a fresh recording for each call.
        # A simple way: create a new console for each call, or reset the record.
        # Rich console doesn't have a direct "reset record buffer" method.
        # Re-initializing self.console or using io.StringIO per call is safer.
        # Let's revert to io.StringIO per call for simplicity and correctness,
        # as managing a single recorded console state is tricky.
        # The prompt did say "self.console = Console(...)" in __init__.
        # If `export_text()` inherently gives only the *last* printed item's text,
        # or if `console.clear()` effectively resets the buffer for `export_text()`,
        # then it's fine. Rich's `export_text()` exports the *entire* buffer since
        # recording started or the last `clear()`.
        # So, `self.console.clear()` before printing is essential.
        self.console.clear()


    def _get_status_text(self, status_value: str) -> Text:
        """
        Converts a status string value into a rich.text.Text object with appropriate styling.

        Args:
            status_value: The string value of the hap's status (e.g., "running", "stopped").

        Returns:
            A Text object styled according to the status.
        """
        # Ensure status_value is a valid Status enum member string
        try:
            status_enum = Status(status_value)
        except ValueError: # Handle cases where status_value might not be a valid Status string
            return Text(status_value) # Default styling for unknown status

        if status_enum is Status.RUNNING:
            return Text(status_enum.value, style="green")
        elif status_enum is Status.STOPPED:
            return Text(status_enum.value, style="red")
        elif status_enum is Status.RESTARTING:
            return Text(status_enum.value, style="yellow")
        elif status_enum is Status.ERROR:
            return Text(status_enum.value, style="bold red")
        return Text(status_enum.value)

    def format_haps(self, haps_data: List[dict]) -> str:
        """
        Formats a list of Hap objects into a table string.

        Args:
            haps_data: A list of dictionaries representing Hap objects.

        Returns:
            A string representation of the table.
        """
        self._clear_console_record() # Clear previous output from console buffer

        if not haps_data:
            # self.console.print("No haps are currently running") # This would be recorded
            # return self.console.export_text()
            return "No haps are currently running" # Simpler, no need to use Rich for this

        table = Table(box=box.MINIMAL if config.plain else box.ROUNDED)
        table.add_column("HID", style="dim" if config.plain else "bold cyan")
        table.add_column("Name")
        table.add_column("PID")
        table.add_column("Status")
        table.add_column("Command")
        if self.verbose:
            table.add_column("Owner")
            table.add_column("Restarts")
            table.add_column("Runtime")
            table.add_column("Active")

        for hap_data in haps_data:
            status_text = self._get_status_text(hap_data.get('status', 'unknown'))
            cmd_list = hap_data.get('cmd', [])
            cmd_str = ' '.join(cmd_list) if isinstance(cmd_list, list) else str(cmd_list)
            
            row = [
                str(hap_data.get('hid', '-')),
                hap_data.get('name', '-'),
                str(hap_data.get('pid')) if hap_data.get('pid') is not None else "-",
                status_text,
                cmd_str,
            ]
            if self.verbose:
                row.extend([
                    hap_data.get('owner', '-'),
                    str(hap_data.get('restarts', '-')),
                    str(hap_data.get('runtime', '-')),
                    "Yes" if hap_data.get('active', False) else "No",
                ])
            table.add_row(*row)
        
        self.console.print(table)
        return self.console.export_text(clear=True) # clear=True ensures buffer is reset for next call

    def format_hap(self, hap_data: dict) -> str:
        """
        Formats a single Hap object into a detailed panel string.

        Args:
            hap_data: A dictionary representing a Hap object.

        Returns:
            A string representation of the panel.
        """
        self._clear_console_record() # Clear previous output

        status_text = self._get_status_text(hap_data.get('status', 'unknown'))
        title = f"[bold cyan]Hap {hap_data.get('hid', '?')}[/bold cyan]: {hap_data.get('name', 'N/A')}"
        
        details_table = Table(box=None, show_header=False, padding=0) # No padding for inner table
        details_table.add_column()
        details_table.add_column()
        details_table.add_row("Name:", hap_data.get('name', '-'))
        details_table.add_row("Status:", status_text)
        details_table.add_row("PID:", str(hap_data.get('pid')) if hap_data.get('pid') is not None else "-")
        details_table.add_row("Return Code:", str(hap_data.get('rc', '-')))
        cmd_list = hap_data.get('cmd', [])
        cmd_str = ' '.join(cmd_list) if isinstance(cmd_list, list) else str(cmd_list)
        details_table.add_row("Command:", cmd_str)
        details_table.add_row("Working Dir:", hap_data.get('cwd', '-'))
        
        if self.verbose:
            details_table.add_row("Parent PID:", str(hap_data.get('ppid', '-')))
            # 'username' from psutil, 'owner' from Hap. Hap data dict should be consistent.
            details_table.add_row("Owner:", hap_data.get('owner', hap_data.get('username', '-')))
            details_table.add_row("Stdout:", hap_data.get('stdout_path', '-'))
            details_table.add_row("Stderr:", hap_data.get('stderr_path', '-'))
            details_table.add_row("Start Time:", str(hap_data.get('start_time', '-')))
            details_table.add_row("End Time:", str(hap_data.get('end_time', '-')) if hap_data.get('end_time') else "-")
            details_table.add_row("Runtime:", str(hap_data.get('runtime', '-')))
            details_table.add_row("Restarts:", str(hap_data.get('restarts', '-')))

        renderables = [details_table]

        if self.verbose and hap_data.get('env'):
            env_table = Table(title="Environment Variables", box=box.MINIMAL, show_header=True, expand=True)
            env_table.add_column("Variable", style="magenta", overflow="fold")
            env_table.add_column("Value", style="green", overflow="fold")
            for key, value in hap_data['env'].items():
                env_table.add_row(key, str(value))
            renderables.append(Padding(env_table, (1, 0, 0, 0))) # Add some top padding
        
        panel_content = Group(*renderables)

        panel = Panel(
            panel_content,
            title=title,
            border_style="blue",
            expand=False # Panel itself should not expand, content will determine width
        )
        
        self.console.print(panel)
        return self.console.export_text(clear=True) # clear=True ensures buffer is reset

# Example data (commented out, for reference)
# hap_data_example = {
#     'hid': 1, 'name': 'my-process', 'pid': 12345, 'status': 'running', 
#     'cmd': ['python', 'my_script.py', '-arg', 'value with space'], 'owner': 'user', 'restarts': 0, 
#     'runtime': "120.5s", 'active': True, 'rc': None, 'cwd': '/path/to/cwd',
#     'ppid': 1234, 'username': 'user', 
#     'stdout_path': '/path/to/stdout.log', 'stderr_path': '/path/to/stderr.log',
#     'start_time': '2023-10-26 10:00:00', 'end_time': None,
#     'env': {'MY_VAR': 'my_value', 'ANOTHER_VAR': 'another_value_that_is_quite_long_to_see_how_it_wraps_or_folds_in_the_table'}
# }
# haps_data_example = [hap_data_example, {
#     'hid': 2, 'name': 'another-app', 'pid': 54321, 'status': 'stopped', 'cmd': ['node', 'server.js'],
#     'owner': 'root', 'restarts': 3, 'runtime': "N/A", 'active': False, 'rc': 1
# }]

# if __name__ == '__main__':
#     config.plain = False # Ensure not plain for rich output

#     # Test format_haps
#     formatter_verbose = TableFormatter(verbose=True)
#     output_haps_verbose = formatter_verbose.format_haps(haps_data_example)
#     print("--- format_haps (verbose) ---")
#     print(output_haps_verbose)

#     formatter_non_verbose = TableFormatter(verbose=False)
#     output_haps_non_verbose = formatter_non_verbose.format_haps(haps_data_example)
#     print("--- format_haps (non-verbose) ---")
#     print(output_haps_non_verbose)
    
#     # Test format_hap
#     output_hap_verbose = formatter_verbose.format_hap(hap_data_example)
#     print("--- format_hap (verbose) ---")
#     print(output_hap_verbose)

#     output_hap_non_verbose = formatter_non_verbose.format_hap(hap_data_example) # Using first hap for non-verbose
#     print("--- format_hap (non-verbose) ---")
#     print(output_hap_non_verbose)

#     # Test empty haps
#     output_empty_haps = formatter_verbose.format_haps([])
#     print("--- format_haps (empty) ---")
#     print(output_empty_haps) # Should be "No haps are currently running"

#     # Test hap with minimal data
#     minimal_hap_data = {'hid': 3, 'name': 'minimal-app', 'pid': None, 'status': 'error', 'cmd': 'do_nothing'}
#     output_minimal_hap = formatter_non_verbose.format_hap(minimal_hap_data)
#     print("--- format_hap (minimal, error status) ---")
#     print(output_minimal_hap)
#     output_minimal_haps = formatter_non_verbose.format_haps([minimal_hap_data, hap_data_example])
#     print("--- format_haps (minimal and normal) ---")
#     print(output_minimal_haps)

#     # Test config.plain = True
#     config.plain = True
#     print("--- format_haps (verbose, plain) ---")
#     print(formatter_verbose.format_haps(haps_data_example))
#     print("--- format_hap (verbose, plain) ---")
#     print(formatter_verbose.format_hap(hap_data_example))
#     config.plain = False # Reset


# --- JSON Formatter ---
import json
from datetime import datetime, date

class JSONFormatter(Formatter):
    """
    Formats Hap objects into a JSON string.
    """

    @staticmethod
    def _json_converter(o: Any) -> str:
        """
        Handles non-serializable objects for json.dumps.
        Converts datetime and date objects to ISO format strings.
        """
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        # For other non-serializable types, you could add more specific handling
        # or simply convert to string, or raise a TypeError.
        # For now, relying on json.dumps default behavior for other types,
        # which will raise TypeError if it encounters something it can't handle
        # that isn't a datetime object. Or, more robustly:
        try:
            return str(o) # Fallback for other complex types not handled
        except Exception:
            raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


    def format_haps(self, haps_data: List[dict]) -> str:
        """
        Formats a list of Hap objects (dictionaries) into a JSON string.

        Args:
            haps_data: A list of dictionaries, where each dictionary
                       represents a Hap object.

        Returns:
            A JSON string representation of the list of Hap objects.
        """
        return json.dumps(haps_data, indent=4, default=self._json_converter)

    def format_hap(self, hap_data: dict) -> str:
        """
        Formats a single Hap object (dictionary) into a JSON string.

        Args:
            hap_data: A dictionary representing a Hap object.

        Returns:
            A JSON string representation of the Hap object.
        """
        return json.dumps(hap_data, indent=4, default=self._json_converter)
```
