"""
Unit tests for hapless.formatters.
"""
import json
from datetime import datetime
# unittest.mock.patch might not be needed for direct formatter testing
# import unittest.mock.patch
# import pytest # Not strictly needed if using plain asserts and pytest test discovery

from hapless.formatters import TableFormatter, JSONFormatter
from hapless.hap import Status # For creating realistic mock status values
from hapless.config import config as hapless_config # For plain mode testing

# --- Mock Data ---

MOCK_DATETIME_STR = "2023-10-26T10:00:00"

# Base data for a single hap (fields always present from Hap.to_dict)
hap_data_base_fields = {
    'hid': '1',
    'name': 'test-hap',
    'raw_name': 'test-hap-raw', # raw_name is always included by current Hap.to_dict
    'pid': 123,
    'cmd': ['sleep', '100'],
    'status': Status.RUNNING.value,
    'rc': None,
    'runtime': '5 seconds',
    'restarts': 0, # restarts is always included
    'active': True,
    'owner': 'testuser', # owner is always included
    'start_time': MOCK_DATETIME_STR,
    'end_time': None,
    'stdout_path': '/tmp/hapless/1/stdout.log',
    'stderr_path': '/tmp/hapless/1/stderr.log',
    'path': '/tmp/hapless/1',
}

# Verbose-specific fields (added by Hap.to_dict when verbose=True)
hap_data_verbose_only_fields = {
    'cwd': '/home/testuser/project',
    'ppid': 1,
    'user': 'testuser', # psutil method is username(), Hap.to_dict uses 'user'
    'env': {'KEY1': 'VALUE1', 'TERM': 'xterm'}
}

# Single hap data, simple (simulates Hap.to_dict(verbose=False))
hap_data_single_simple = {**hap_data_base_fields}

# Single hap data, verbose (simulates Hap.to_dict(verbose=True))
hap_data_single_verbose = {**hap_data_base_fields, **hap_data_verbose_only_fields}


# List of haps data
# Second hap, simple
hap2_data_simple = {
    **hap_data_base_fields,
    'hid': '2',
    'name': 'another-hap',
    'raw_name': 'another-hap-raw',
    'pid': 124,
    'status': Status.STOPPED.value,
    'cmd': ['python', 'app.py'],
    'active': False,
    'rc': 0,
    'start_time': "2023-10-25T08:00:00",
    'end_time': "2023-10-25T09:00:00",
    'runtime': '1 hour',
    # No verbose fields for this simple version
}

# Second hap, verbose
hap2_data_verbose = {
    **hap2_data_simple, # Start with simple version of hap2
    **hap_data_verbose_only_fields, # Add generic verbose fields
    'env': {'KEY2': 'VALUE2'}, # Override env for this specific verbose hap
}

haps_data_list_simple = [hap_data_single_simple, hap2_data_simple]
haps_data_list_verbose = [hap_data_single_verbose, hap2_data_verbose]


# --- TestJSONFormatter Class ---

class TestJSONFormatter:
    def test_format_hap_simple(self):
        formatter = JSONFormatter() # Verbose flag on formatter is not used by JSONFormatter
        output_str = formatter.format_hap(hap_data_single_simple)
        data = json.loads(output_str)

        assert data['hid'] == hap_data_single_simple['hid']
        assert data['name'] == hap_data_single_simple['name']
        assert data['status'] == Status.RUNNING.value
        assert 'env' not in data # 'env' is a verbose-only field from Hap.to_dict

    def test_format_hap_verbose(self):
        formatter = JSONFormatter()
        output_str = formatter.format_hap(hap_data_single_verbose)
        data = json.loads(output_str)

        assert data['hid'] == hap_data_single_verbose['hid']
        assert data['name'] == hap_data_single_verbose['name']
        assert data['cwd'] == hap_data_single_verbose['cwd']
        assert 'env' in data
        assert data['env'] == hap_data_single_verbose['env']

    def test_format_haps_simple(self):
        formatter = JSONFormatter()
        output_str = formatter.format_haps(haps_data_list_simple)
        data_list = json.loads(output_str)

        assert isinstance(data_list, list)
        assert len(data_list) == 2
        assert data_list[0]['hid'] == hap_data_single_simple['hid']
        assert 'env' not in data_list[0]
        assert data_list[1]['hid'] == hap2_data_simple['hid']
        assert 'env' not in data_list[1]


    def test_format_haps_verbose(self):
        formatter = JSONFormatter()
        output_str = formatter.format_haps(haps_data_list_verbose)
        data_list = json.loads(output_str)

        assert isinstance(data_list, list)
        assert len(data_list) == 2
        assert data_list[0]['hid'] == haps_data_list_verbose[0]['hid']
        assert data_list[0]['env'] == haps_data_list_verbose[0]['env']
        assert data_list[1]['hid'] == haps_data_list_verbose[1]['hid']
        assert data_list[1]['env'] == haps_data_list_verbose[1]['env']


    def test_format_haps_empty(self):
        formatter = JSONFormatter()
        output_str = formatter.format_haps([])
        assert output_str == "[]"

    def test_json_converter_datetime(self):
        # Test the _json_converter directly for datetime objects
        dt_obj = datetime(2024, 1, 1, 12, 30, 0)
        data_with_dt = {"time_obj": dt_obj, "id": 1}
        formatter = JSONFormatter()
        output_str = formatter.format_hap(data_with_dt)
        parsed_data = json.loads(output_str)
        assert parsed_data["time_obj"] == "2024-01-01T12:30:00"


# --- TestTableFormatter Class ---

class TestTableFormatter:
    # Test format_hap (Panel view)
    def test_format_hap_simple(self):
        formatter = TableFormatter(verbose=False)
        # Pass the 'simple' version of data, which lacks verbose-only fields like 'cwd', 'env'
        output_str = formatter.format_hap(hap_data_single_simple)

        assert output_str
        assert hap_data_single_simple['name'] in output_str
        assert "Status:" in output_str
        assert hap_data_single_simple['status'] in output_str
        assert "Command:" in output_str
        assert ' '.join(hap_data_single_simple['cmd']) in output_str

        # Verbose-only fields (which are not in hap_data_single_simple)
        # and should not be rendered by TableFormatter(verbose=False) anyway
        assert "Working Dir:" not in output_str
        assert "Parent PID:" not in output_str
        assert "Owner:" not in output_str # Owner is verbose in panel view of TableFormatter
        assert "Environment Variables" not in output_str
        assert "KEY1" not in output_str


    def test_format_hap_verbose(self):
        formatter = TableFormatter(verbose=True)
        output_str = formatter.format_hap(hap_data_single_verbose)

        assert output_str
        assert hap_data_single_verbose['name'] in output_str
        assert "Status:" in output_str
        assert hap_data_single_verbose['status'] in output_str
        assert "Command:" in output_str
        assert ' '.join(hap_data_single_verbose['cmd']) in output_str

        # Verbose-only fields that should now be present
        assert "Working Dir:" in output_str
        assert hap_data_single_verbose['cwd'] in output_str
        assert "Parent PID:" in output_str
        assert "Owner:" in output_str # Owner is verbose in panel view
        assert hap_data_single_verbose['owner'] in output_str
        assert "Environment Variables" in output_str # Title of env table
        assert "KEY1" in output_str
        assert hap_data_single_verbose['env']['KEY1'] in output_str


    # Test format_haps (Table view)
    def test_format_haps_simple(self):
        formatter = TableFormatter(verbose=False)
        output_str = formatter.format_haps(haps_data_list_simple)
        
        assert output_str
        assert hap_data_single_simple['name'] in output_str
        assert hap2_data_simple['name'] in output_str
        assert hap_data_single_simple['status'] in output_str # e.g. "running"
        assert hap2_data_simple['status'] in output_str # e.g. "stopped"
        
        # Check for presence of standard column headers
        assert "HID" in output_str
        assert "Name" in output_str # Column header
        assert "PID" in output_str
        assert "Status" in output_str # Column header
        assert "Command" in output_str # Column header

        # Verbose column headers that should NOT be present
        # TableFormatter.format_haps verbose columns: Owner, Restarts, Runtime, Active
        assert "Owner" not in output_str # Column header
        assert "Restarts" not in output_str # Column header
        assert "Runtime" not in output_str # Column header for the 'Runtime' string
        assert "Active" not in output_str # Column header for 'Yes'/'No'

    def test_format_haps_verbose(self):
        formatter = TableFormatter(verbose=True)
        output_str = formatter.format_haps(haps_data_list_verbose)

        assert output_str
        assert hap_data_single_verbose['name'] in output_str
        assert hap2_data_verbose['name'] in output_str
        assert hap_data_single_verbose['status'] in output_str
        assert hap2_data_verbose['status'] in output_str
        
        # Check for presence of standard AND verbose column headers
        assert "HID" in output_str
        assert "Name" in output_str
        assert "PID" in output_str
        assert "Status" in output_str
        assert "Command" in output_str
        assert "Owner" in output_str # Verbose Column header
        assert "Restarts" in output_str # Verbose Column header
        assert "Runtime" in output_str # Verbose Column header
        assert "Active" in output_str # Verbose Column header

        # Check some verbose data
        assert hap_data_single_verbose['owner'] in output_str
        assert str(hap_data_single_verbose['restarts']) in output_str
        assert hap_data_single_verbose['runtime'] in output_str # The actual runtime string
        assert ("Yes" if hap_data_single_verbose['active'] else "No") in output_str


    def test_format_haps_empty(self):
        formatter = TableFormatter() # verbose doesn't matter here
        output_str = formatter.format_haps([])
        assert output_str == "No haps are currently running"

    def test_table_formatter_plain_mode(self):
        # Test that plain mode (config.plain=True) changes output for table
        original_plain_mode = hapless_config.plain
        hapless_config.plain = True
        
        formatter_simple = TableFormatter(verbose=False)
        output_simple_plain = formatter_simple.format_haps(haps_data_list_simple)
        # Rich's box.MINIMAL doesn't use rounded characters or heavy lines
        # Check for a character that is part of rounded box but not minimal
        assert "╭" not in output_simple_plain # Top-left of rounded box
        assert "│" not in output_simple_plain # Vertical line of rounded/heavy box

        formatter_verbose = TableFormatter(verbose=True)
        output_verbose_plain = formatter_verbose.format_hap(hap_data_single_verbose)
        assert "╭" not in output_verbose_plain
        assert "│" not in output_verbose_plain
        
        hapless_config.plain = original_plain_mode # Reset config

```
