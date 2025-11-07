from pathlib import Path
import sys
import subprocess
from typing import Optional, List, Callable, Tuple
import logging
import tempfile
import site

def _find_postgres_binaries() -> Tuple[Optional[Path], Optional[int]]:
    """Find PostgreSQL binaries installed by pgserver-postgres-* packages.

    Returns:
        Tuple of (bin_path, version_number) or (None, None) if not found
    """
    # Check all site-packages directories for pgserver_binaries
    for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
        if not site_dir:
            continue

        binaries_base = Path(site_dir) / "pgserver_binaries"
        if not binaries_base.exists():
            continue

        # Look for pg16, pg17, or pg18 directories
        for pg_dir in binaries_base.glob("pg*"):
            if not pg_dir.is_dir():
                continue

            bin_path = pg_dir / "bin"
            if not bin_path.exists():
                continue

            # Extract version number from directory name (e.g., "pg16" -> 16)
            try:
                version = int(pg_dir.name[2:])
                # Verify this is a valid PostgreSQL installation
                if (bin_path / "postgres").exists() or (bin_path / "postgres.exe").exists():
                    return (bin_path, version)
            except (ValueError, IndexError):
                continue

    return (None, None)

# Find installed PostgreSQL binaries
POSTGRES_BIN_PATH, INSTALLED_POSTGRES_VERSION = _find_postgres_binaries()

_logger = logging.getLogger('pgserver')

def create_command_function(pg_exe_name : str) -> Callable:
    def command(args : List[str], pgdata : Optional[Path] = None, **kwargs) -> str:
        """
            Run a command with the given command line arguments.
            Args:
                args: The command line arguments to pass to the command as a string,
                a list of options as would be passed to `subprocess.run`
                pgdata: The path to the data directory to use for the command.
                    If the command does not need a data directory, this should be None.
                kwargs: Additional keyword arguments to pass to `subprocess.run`, eg user, timeout.

            Returns:
                The stdout of the command as a string.
        """
        if pg_exe_name.strip('.exe') in ['initdb', 'pg_ctl', 'pg_dump']:
           assert pgdata is not None, "pgdata must be provided for initdb, pg_ctl, and pg_dump"

        if pgdata is not None:
            args = ["-D", str(pgdata)] + args

        full_command_line = [str(POSTGRES_BIN_PATH / pg_exe_name)] + args

        with tempfile.TemporaryFile('w+') as stdout, tempfile.TemporaryFile('w+') as stderr:
            try:
                _logger.info("Running commandline:\n%s\nwith kwargs: `%s`", full_command_line, kwargs)
                # NB: capture_output=True, as well as using stdout=subprocess.PIPE and stderr=subprocess.PIPE
                # can cause this call to hang, even with a time-out depending on the command, (pg_ctl)
                # so we use two temporary files instead
                result = subprocess.run(full_command_line, check=True, stdout=stdout, stderr=stderr, text=True,
                                        **kwargs)
                stdout.seek(0)
                stderr.seek(0)
                output = stdout.read()
                error = stderr.read()
                _logger.info("Successful postgres command %s with kwargs: `%s`\nstdout:\n%s\n---\nstderr:\n%s\n---\n",
                            result.args, kwargs, output, error)
            except subprocess.CalledProcessError as err:
                stdout.seek(0)
                stderr.seek(0)
                output = stdout.read()
                error = stderr.read()
                _logger.error("Failed postgres command %s with kwargs: `%s`:\nerror:\n%s\nstdout:\n%s\n---\nstderr:\n%s\n---\n",
                            err.args, kwargs, str(err), output,  error)
                raise err

        return output

    return command

__all__ = ['INSTALLED_POSTGRES_VERSION']

def _init():
    for path in POSTGRES_BIN_PATH.iterdir():
        exe_name = path.name
        prog = create_command_function(exe_name)
        # Strip .exe suffix for Windows compatibility
        function_name = exe_name.strip('.exe')
        setattr(sys.modules[__name__], function_name, prog)
        __all__.append(function_name)

_init()