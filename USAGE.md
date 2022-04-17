## Usage

`Hap` is a tiny wrapper around the process allowing to track its status during execution and upon completion.

`hap-alias` is either a hap id (integer identificator) or hap name (string identificator). Note that you need to replace this placeholder in commands below with an actual value.

### Running scripts

* Run simple script

```bash
$ hap run ./examples/script.sh
$ hap run python ./examples/fast.py
```

### Checking status

* Check status of the specific hap

```bash
$ hap show [hap-alias]
# or
$ hap status [hap-alias]
```

* Show detailed status for the hap (including environment variables)

```bash
$ hap show -v [hap-alias]
$ hap show --verbose [hap-alias]  # same as above
# or
$ hap status -v [hap-alias]
$ hap status --verbose [hap-alias]  # same as above
```

### Checking logs

* Print process logs to the console

```bash
$ hap logs [hap-alias]
```

* Stream logs continuously to the console

```bash
$ hap logs -f [hap-alias]
# or
$ hap logs --follow [hap-alias]
```
