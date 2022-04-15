import asyncio
import tempfile
from pathlib import Path


async def run(
    cmd,
    stdout_path: Path,
    stderr_path: Path,
    pid_path: Path,
    rc_path: Path,
):
    with (
        open(stdout_path, 'w') as stdout_pipe,
        open(stderr_path, 'w') as stderr_pipe,
        open(pid_path, 'w') as pid_file,
        open(rc_path, 'w') as rc_file,
    ):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
        )
        pid_file.write(f'{proc.pid}')
        _ = await proc.communicate()
        rc = proc.returncode
        rc_file.write(f'{rc}')


async def _run(cmd, hap_id: int):
    tmp_dir = Path(tempfile.gettempdir())
    hap_dir = tmp_dir / 'hapless' / f'{hap_id}'
    hap_dir.mkdir(parents=True, exist_ok=True)
    hap_stdout = hap_dir / 'stdout.log'
    hap_stderr = hap_dir / 'stderr.log'
    rc_file = hap_dir / 'rc'
    pid_file = hap_dir / 'pid'
    hap_stdout.touch()
    hap_stderr.touch()
    stdout_pipe = open(hap_stdout, 'w')
    stderr_pipe = open(hap_stderr, 'w')
    # cmd = f'{cmd}; echo $? > {rc_file}'
    # print(f'Command is: {cmd}')
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=stdout_pipe,
        stderr=stderr_pipe,
    )

    with open(pid_file, 'w') as pf:
        pf.write(f'{proc.pid}')
        print(f'This is pid {proc.pid}')

    _ = await proc.communicate()
    rc = proc.returncode
    with open(rc_file, 'w') as rf:
        rf.write(f'{rc}')
        print(f'This is return code {rc}')

    stdout_pipe.close()
    stderr_pipe.close()


if __name__ == '__main__':
    # asyncio.run(run('python fast.py', 5))
    asyncio.run(run('python long_running.py', 6))
