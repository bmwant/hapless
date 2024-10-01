## Usage

`Hap` is a tiny wrapper around the process allowing to track its status during execution and upon completion. Unlike other managers it does not run any daemon process and does not require any configuration files to get started.

`hap-alias` is either a hap id (integer identificator) or hap name (string identificator). Note that you need to replace this placeholder in commands below with an actual value.

### ✏️ Running scripts

➡️ Run a simple script

```bash
hap run ./examples/script.sh
hap run python ./examples/fast.py
```

➡️ Run script accepting arguments

```bash
hap run -- python ./examples/show_details.py -v --name details --count=5
```

Use `--` delimiter in order to separate target script and its arguments. Otherwise arguments will be interpreted as a keys for `hap` executable.

> NOTE: as of version `0.4.0` specifying double dash is optional and required only if parameters for your target command match parameters of `hap run` command itself

```bash
# wouldn't work, as run has its own `--help` option
hap run python --help

# will work as expected without `--` delimiter
hap run ./examples/show_details.py --flag --param=value
```

➡️ Check script for early failures right after launch

```bash
hap run --check python ./examples/fail_fast.py
```

### ✏️ Checking status

➡️ Show summary for all haps

```bash
hap
# or
hap status  # equivalent
hap show  # same as above
```

➡️ Check status of the specific hap

```bash
hap show [hap-alias]
# or
hap status [hap-alias]
```

➡️ Show detailed status for the hap (including environment variables)

```bash
hap show -v [hap-alias]
hap show --verbose [hap-alias]  # same as above
# or
hap status -v [hap-alias]
hap status --verbose [hap-alias]  # same as above
```

### ✏️ Checking logs

➡️ Print process logs to the console

```bash
hap logs [hap-alias]
```

➡️ Stream logs continuously to the console

```bash
hap logs -f [hap-alias]
# or
hap logs --follow [hap-alias]
```

### ✏️ Other commands

➡️ Suspend (pause) a hap. Sends `SIGSTOP` signal to the process

```bash
hap pause [hap-alias]
# or
hap suspend [hap-alias]
```

➡️ Resume paused hap. Sends `SIGCONT` signal to the suspended process

```bash
hap resume [hap-alias]
```

➡️ Send specific signal to the process by its code

```bash
hap signal [hap-alias] 9  # sends SIGKILL
hap signal [hap-alias] 15  # sends SIGTERM
```

➡️ Remove haps from the list.

- Without any parameters removes only successfully finished haps (with `0` return code). Provide `--all` flag to remove failed haps as well. Used to make list more concise in case you have a lot of things running at once and you are not interested in results/error logs of completed ones.

```bash
hap clean

# Remove all finished haps (both successful and failed)
hap clean --all
# Same as above
hap cleanall
```
➡️ Restart a hap.

- When restart command is called, hap will stop the process and start it again. The command is rerun from the current working directory.

```bash
hap restart [hap-alias]
```
