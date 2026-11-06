# Linux and Bash Interview Guide

[Home](../README.md) · Related: [memory and performance](../System_Design/Memory_Profiling_Performance.md), [observability](../System_Design/Observability.md), [networking](../System_Design/Networking.md), [Python subprocess](Python.md).

Focus: practical backend/support interviews involving Linux scripting and production troubleshooting. These are practice scenarios, not claims about a particular client's interview questions.

Examples target **Linux with Bash**, GNU utilities, procps, and systemd where shown. macOS/BSD flags differ; use a Linux VM/container for Linux-specific practice. `pidstat`, `iostat`, and `mpstat` come from sysstat; `lsof`, `strace`, and `curl` may need separate installation. Replace example names, PIDs, paths, and ports. Commands are examples, not executed against a server by this guide. Inspect before changing a running service; tracing adds overhead and may capture sensitive arguments/data.

## Contents

1. [A process is taking too long: investigation](#1-a-process-is-taking-too-long-investigation)
2. [Processes, threads, states, and signals](#2-processes-threads-states-and-signals)
3. [CPU, memory, disk, and load](#3-cpu-memory-disk-and-load)
4. [Files, permissions, and descriptors](#4-files-permissions-and-descriptors)
5. [Networking, services, and logs](#5-networking-services-and-logs)
6. [Pipes, redirection, and text processing](#6-pipes-redirection-and-text-processing)
7. [Bash scripting fundamentals](#7-bash-scripting-fundamentals)
8. [Practical scripts](#8-practical-scripts)
9. [Cron and background work](#9-cron-and-background-work)
10. [Interview scenarios and practice order](#10-interview-scenarios-and-practice-order)
11. [Primary references](#11-primary-references)

## 1. A process is taking too long: investigation

**Spoken answer:** “I first establish the normal runtime, when the slowdown started, and whether the job is making progress. I identify the process and its children, then sample CPU, memory, I/O, and thread activity. I distinguish time spent executing from time waiting on disk, network, locks, or dependencies. I use logs and targeted profiles/traces to test the likely cause, apply a measured fix, and compare the same workload afterward.”

### Step 1: identify the right workload

Ask: What normally takes 2 minutes and now takes 20? Same input size? New deployment? More concurrency? Is this queue wait or actual execution? Has an output counter, log timestamp, or checkpoint advanced?

```bash
pgrep -af 'report-worker'                  # Discover candidates; pattern may match others
pid=12345                                # Set after verifying identity
ps -p "$pid" -o pid,ppid,user,stat,etime,time,%cpu,%mem,rss,args
pstree -ap "$pid"                         # Children; pstree is commonly in psmisc
```

`etime` is elapsed wall time; `time` is accumulated CPU time. A process alive for 20 minutes may have used only 10 seconds of CPU. A wrapper script may be waiting for a busy child. `ps` CPU percentage is generally an average over process lifetime, so use interval samples for current behavior. [ps manual](https://man7.org/linux/man-pages/man1/ps.1.html).

### Step 2: sample, then choose a branch

```bash
top -H -p "$pid"                          # Live threads; q exits
pidstat -u -r -d -w -p "$pid" 1 5         # CPU, memory, I/O, context switches
ps -L -p "$pid" -o pid,tid,stat,pcpu,wchan:24,comm
free -h
vmstat 1 5
iostat -xz 1 5
```

Some first reports summarize activity since boot; use subsequent interval reports. Missing tool output or insufficient permissions is not evidence that the resource is healthy.

| Observation | Hypothesis | Next evidence |
|---|---|---|
| One thread near one CPU's capacity | Hot loop, parsing, serialization, computation | Runtime CPU profile; input-size comparison |
| Many busy threads and run queue grows | CPU contention or excessive parallelism | Per-core CPU, worker count, cgroup CPU quota/throttling |
| Low CPU, high elapsed time | Waiting, sleeping, dependency or queue delay | Thread stacks, request traces, connections, logs |
| Sustained I/O plus high device latency | Storage path bottleneck | Process I/O, device queue/latency, read/write pattern |
| Swap-in/out and memory pressure | Working set exceeds available memory | RSS trend, concurrency, container limits, allocations |
| Repeated lock waits | Contention; possibly deadlock | Multiple thread dumps and lock ownership |
| Application waits on DB/network | Remote latency or pool exhaustion | DB locks/query plan, pool metrics, downstream timing |

A waiting thread or `futex` call alone does not establish deadlock. Low host CPU does not rule out a container exhausting its CPU quota.

### Step 3: inspect the likely boundary

```bash
lsof -p "$pid"                            # Open files/sockets; potentially large
cat "/proc/$pid/status"                  # State, memory categories, threads
cat "/proc/$pid/io"                      # Compare counters over time; access restricted
ss -tpn                                  # TCP connections; ownership may need privilege
journalctl -u report-worker --since '15 minutes ago' --no-pager
# Targeted attach, if permitted; Ctrl-C detaches from the attached process:
strace -f -tt -T -p "$pid" -e trace=network,read,write,futex
```

`strace` shows system calls, not application function hotspots. `-tt` adds timestamps, `-T` reports call duration, and `-f` follows relevant threads/children. A long `read` may be a socket, pipe, or file: resolve its descriptor. A quiet trace can mean computation in user space. [strace manual](https://man7.org/linux/man-pages/man1/strace.1.html).

For Java, use thread dumps/JFR; for Python, use an appropriate sampling profiler or `cProfile` in a controlled run. See [runtime profiling](../System_Design/Memory_Profiling_Performance.md). Avoid restarting before collecting the evidence needed to explain the incident.

### Step 4: fix and verify

State a hypothesis: “Every record opens a new connection” or “Eight workers cause swapping.” Change one relevant factor. Compare input, concurrency, runtime, CPU, peak memory, I/O, errors, and downstream impact. A restart is mitigation; a shorter runtime after restart alone does not prove the cause.

## 2. Processes, threads, states, and signals

A process owns resources such as an address space and descriptors; threads in that process share many resources and have their own execution state/stacks. A PID identifies a process; Linux also exposes thread IDs. PPID identifies the parent. `fork` creates a child process; `exec` replaces the current process image; `wait` lets a parent collect child status.

| State | Meaning | Interview trap |
|---|---|---|
| `R` | Running or runnable | Does not mean continuously executing |
| `S` | Interruptible sleep | Normal for idle workers; not automatically stuck |
| `D` | Uninterruptible sleep, commonly I/O related | SIGKILL may remain pending until the wait ends |
| `T` | Stopped/traced | Check job control/debugging |
| `Z` | Exited zombie awaiting reaping | Already exited; killing it does not solve parent reaping |

[Process state definitions](https://man7.org/linux/man-pages/man1/ps.1.html). An orphan is a process whose parent exited; it may still run and is reparented to an appropriate reaper/subreaper. A zombie has exited.

```bash
ps -eo pid,ppid,stat,comm --sort=pid
kill -TERM "$pid"                         # Request graceful shutdown of verified PID
# If graceful shutdown fails and forced termination is justified:
kill -KILL "$pid"                         # Cannot be caught; no application cleanup
```

`kill` sends a signal. SIGTERM can be handled; SIGKILL cannot be caught or ignored. SIGINT commonly comes from Ctrl-C; SIGHUP behavior depends on the application. Prefer the service manager for a managed service. PIDs can be reused: reverify identity before sending a signal. `nice`/`renice` influence scheduling priority, not an enforced CPU percentage limit.

**Follow-up:** Why is a shell still running after its main work finished? It may be waiting for children, reading stdin, waiting on a lock, or running cleanup. Inspect its process tree and wait location.

## 3. CPU, memory, disk, and load

| Command | Read this | Avoid this conclusion |
|---|---|---|
| `uptime` | 1/5/15-minute load averages | Load is not CPU percentage; includes runnable and uninterruptible tasks |
| `mpstat -P ALL 1 5` | Per-core busy/idle, system time, steal | One idle average can hide a saturated core |
| `free -h` | Available memory and swap | Small “free” alone does not prove shortage; caches are useful |
| `vmstat 1 5` | Runnable `r`, blocked `b`, swap `si/so`, CPU | Allocated swap alone does not prove current thrashing |
| `iostat -xz 1 5` | Throughput, `await`, queue, `%util` | `%util` alone is not a universal saturation measure for parallel devices |
| `df -h /var` | Filesystem capacity | This does not identify the largest directories |
| `df -i /var` | Inode availability | Free bytes do not guarantee new files can be created |
| `du -xhd1 /var/log` | Directory usage on one filesystem | Scans can be costly; permissions affect visibility |

RSS is resident memory, not just live language objects; VSZ includes virtual mappings/reservations. Shared memory makes summing RSS misleading. Container memory limits can be reached while the host still has available RAM. `iowait` is CPU accounting, not a direct stopwatch for one process's disk wait. [sysstat tools and documentation](https://sysstat.github.io/).

**Question: disk is full but `du` looks small.** Check the same filesystem/mount, permissions, deleted files still open (`lsof +L1`), inodes, and filesystem reservations/snapshots. An unlinked file can occupy blocks while a process holds it open. Coordinate log reopen/rotation rather than deleting more files blindly.

**Question: load is high but CPU is low.** Check `D` tasks and storage/network-filesystem waits. Compare CPU count, per-core use, cgroup restrictions, and a sustained sampling window.

## 4. Files, permissions, and descriptors

```bash
pwd
ls -lah /var/log
stat /var/log/app.log
id
umask
find /var/log -type f -name '*.log' -mtime +7 -print
find /var/log -type f -name '*.log' -print0 | xargs -0 -r wc -l
```

Quote `*.log` so `find` receives the pattern. GNU `xargs -r` avoids execution on empty input; `-print0`/`-0` handle spaces/newlines in names. `-mtime +7` uses rounded 24-hour age buckets, not an exact seven-day timestamp cutoff. Preview matches before adding any deletion action.

- Permissions are owner/group/other read, write, execute. `chmod 640 report.txt` gives owner read/write and group read. Directory execute means traversal; directory permissions control creating/removing entries.
- A hard link is another directory entry for the same inode and cannot cross filesystems. A symlink stores a target path and can dangle or cross filesystems.
- Descriptors `0`, `1`, `2` are stdin, stdout, stderr. Descriptor leaks can cause “too many open files.” Inspect `ls /proc/12345/fd`, `cat /proc/12345/limits`, and `lsof -p 12345`; fix lifecycle leaks before merely raising limits.
- An environment variable is inherited by child processes if exported. A normal shell variable is not automatically exported. Avoid placing credentials in command arguments or diagnostic output.

## 5. Networking, services, and logs

```bash
ip addr
ip route
getent hosts api.example.com
ss -ltnp                                 # Listening TCP sockets
ss -tpn                                  # Established/other TCP sockets
curl --connect-timeout 3 --max-time 10 -sS -o /dev/null \
  -w 'status=%{http_code} dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} first_byte=%{time_starttransfer} total=%{time_total}\n' \
  https://api.example.com/health
systemctl status report-worker --no-pager
journalctl -u report-worker --since '30 minutes ago' --no-pager
tail -n 100 /var/log/app.log
tail -F /var/log/app.log                  # Follow name across common rotation cases
```

`curl` timings above are cumulative milestones from transfer start; subtract relevant milestones to estimate phases, accounting for reuse/redirects. By default, an HTTP 500 does not make curl fail; use `--fail` when appropriate. Ping only tests a particular ICMP path: it does not prove an application port/TLS/HTTP works, and blocked ICMP does not prove the server is down.

**Port is listening but clients fail:** verify bind address (`127.0.0.1` versus external interfaces), route, firewall/security group, DNS, TLS/SNI, proxy, and application response. A listening socket does not prove readiness.

**Service fails under systemd but runs in your terminal:** compare service user, working directory, PATH/environment, file permissions, resource limits, dependencies, and unit logs. `systemctl`/`journalctl` require a systemd environment; containers may log to stdout instead.

## 6. Pipes, redirection, and text processing

```bash
command > output.log 2>&1                # Both streams to file
command >> output.log 2>&1               # Append both streams
command 2>&1 > output.log                # Stderr keeps previous stdout destination
producer | consumer                     # Stdout only flows through the pipe
```

Redirections are processed left to right. `>` truncates an existing file. `2>` redirects stderr. `tee` displays and writes input, but pipeline status needs attention.

### Common log questions

```bash
grep -n -F 'ERROR' app.log                # Literal match with line numbers
grep -n -E 'ERROR|WARN' app.log           # Extended regex
grep -c -F 'ERROR' app.log                # Matching lines, not total occurrences
sed -n '100,130p' app.log                 # Print a line range
sort names.txt | uniq -c | sort -nr       # Counts; uniq needs adjacent duplicates
# Assumption: whitespace-delimited access log, client IP in field 1
awk '{count[$1]++} END {for (ip in count) print count[ip], ip}' access.log | sort -nr
# Assumption: status is field 9 in this particular access-log format
awk '$9 ~ /^5[0-9][0-9]$/ {print}' access.log
```

Explain the format before choosing fields. `awk -F,` is not a general CSV parser: quoted commas/newlines need a real CSV parser. Structured JSON logs need a JSON parser such as `jq`. Sorting large files uses memory and possibly temporary disk; account for both.

**Pipeline failure:** Bash normally returns the last command's status; `set -o pipefail` returns the rightmost nonzero status if any command failed. Capture `"${PIPESTATUS[@]}"` immediately to inspect individual statuses. `grep` returns 1 for no match, which may be an expected result. A producer can receive SIGPIPE when a consumer such as `head` exits early. [Bash pipeline semantics](https://www.gnu.org/software/bash/manual/html_node/Pipelines).

## 7. Bash scripting fundamentals

```bash
#!/usr/bin/env bash
name=${1:-world}                         # Default if unset or empty
printf 'Hello, %s\n' "$name"
```

Run `bash script.sh argument`, or make it executable and use `./script.sh argument`. `sh script.sh` does not promise Bash features even if the file has a Bash shebang.

| Syntax | Meaning / trap |
|---|---|
| `value='some text'` | No spaces around assignment `=` |
| `'$name'` / `"$name"` | Literal text / expansion preserved as one argument |
| `"$@"` | Each positional argument preserved separately |
| `$?`, `$$`, `$!` | Previous status, shell PID, last background PID |
| `$(command)` | Capture stdout; strips trailing newlines |
| `[[ -f "$path" ]]` | Bash regular-file test; quote paths consistently |
| `[[ "$a" == "$b" ]]` | String comparison; unquoted RHS can be a pattern |
| `(( count > 3 ))` | Arithmetic condition; shell arithmetic is integer |
| `export APP_MODE=test` | Export to children; does not change parent shell |
| `source ./settings.sh` | Execute in current shell; only source trusted code |

```bash
if [[ -r "$input" ]]; then
  printf 'Readable: %s\n' "$input"
else
  printf 'Cannot read: %s\n' "$input" >&2
  exit 1
fi

for item in "${items[@]}"; do
  printf '%s\n' "$item"
done

while IFS= read -r line || [[ -n "$line" ]]; do
  printf '%s\n' "$line"
done < "$input"
```

The loop variables above assume `input` and the Bash array `items` were initialized. Avoid `for f in $(ls ...)`: word splitting corrupts filenames. Use quoted globs with an empty-match strategy or NUL-delimited traversal. Pipeline loop bodies commonly run in a subshell, so variable changes may not survive outside them.

**What does `set -euo pipefail` do?** `-u` rejects many unset-variable expansions; `-e` exits on some unhandled failures with significant conditional/pipeline exceptions; `pipefail` changes pipeline status. This is not complete error handling. Use explicit checks for expected failures, validate inputs, and know commands' status contracts. `((count++))` can return status 1 when its expression evaluates to zero, which matters under `-e`. [Bash manual](https://www.gnu.org/s/bash/manual/bash.html).

Use `bash -n script.sh` for syntax and ShellCheck, when available, for common mistakes. `bash -x` traces expansions and can expose secrets.

## 8. Practical scripts

### A. Summarize ERROR lines without treating “no errors” as a failure

```bash
#!/usr/bin/env bash
set -u
if (( $# != 1 )); then
  printf 'Usage: %s LOG_FILE\n' "$0" >&2
  exit 2
fi
log_file=$1
if [[ ! -f "$log_file" || ! -r "$log_file" ]]; then
  printf 'Not a readable regular file: %s\n' "$log_file" >&2
  exit 1
fi
# Assumption: each matching line counts as one error, literal uppercase ERROR.
if count=$(grep -c -F -- 'ERROR' "$log_file"); then
  printf 'ERROR lines: %s\n' "$count"
else
  status=$?
  if (( status == 1 )); then
    printf 'ERROR lines: 0\n'
  else
    printf 'Log scan failed (status %s)\n' "$status" >&2
    exit "$status"
  fi
fi
```

**Follow-ups:** What if the file rotates during the scan? What if error text is JSON or multiline? What if you only want the last ten minutes? Define the timestamp/record format and timezone first.

### B. Monitor a verified PID for a bounded number of samples

```bash
#!/usr/bin/env bash
set -u
if (( $# != 1 )) || [[ ! $1 =~ ^[1-9][0-9]*$ ]]; then
  printf 'Usage: %s POSITIVE_PID\n' "$0" >&2
  exit 2
fi
pid=$1
for ((sample=1; sample<=5; sample++)); do
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  if ! ps -p "$pid" -o pid,ppid,stat,etime,time,%cpu,%mem,rss,args; then
    printf 'Process unavailable; stopping\n' >&2
    exit 1
  fi
  if (( sample < 5 )); then sleep 2; fi
done
```

This records snapshots, not interval CPU utilization. It can expose command arguments, cannot prevent PID reuse, and does not follow children. For an incident, supplement it with interval tools and workload identity. Practice against a process you own.

### C. Prevent overlapping local scheduled jobs

```bash
#!/usr/bin/env bash
set -u
# Provision /var/lock/myapp with ownership suitable for the service user.
exec 9>/var/lock/myapp/report.lock || exit 1
if flock -n -E 75 9; then
  /opt/myapp/run-report
  status=$?
  exit "$status"
else
  status=$?
  if (( status == 75 )); then
    printf 'Another report holds the lock; skipping\n' >&2
    exit 0
  fi
  printf 'Lock acquisition failed (status %s)\n' "$status" >&2
  exit "$status"
fi
```

The lock is held through the open descriptor; do not remove/replace its file while jobs use it. This assumes a local filesystem with suitable `flock` semantics. It is not a distributed coordination mechanism. The job must finish its relevant work before returning; background children complicate descriptor inheritance and completion.

## 9. Cron and background work

User crontab example (host scheduler timezone unless configured otherwise):

```cron
# Run daily at 02:00; ensure output directory exists and is writable.
0 2 * * * /usr/bin/bash /opt/myapp/report.sh >> /var/log/myapp/report.log 2>&1
```

Fields: minute, hour, day of month, month, day of week. User crontabs have no username field; system crontabs commonly do. In common cron implementations, restricted day-of-month and day-of-week fields are matched with OR semantics. Confirm the implementation and timezone, especially across DST.

**Runs manually but fails in cron:** check minimal environment/PATH, working directory, interpreter, user, permissions, credentials, and output. Use absolute paths, initialize required environment deliberately, and record exit status. `%` has special meaning in many crontabs and must be escaped when intended literally. Add overlap control and a runtime bound when appropriate; retries require idempotency.

```bash
./job.sh > job.log 2>&1 &
job_pid=$!
if wait "$job_pid"; then
  printf 'Job succeeded\n'
else
  status=$?
  printf 'Job failed: %s\n' "$status" >&2
fi
```

`&` starts background work; it does not make it reliable. `wait` collects child completion. `nohup` changes hangup handling and may redirect terminal streams; it does not provide restart policy or supervision. Use a service manager for ongoing services. GNU `timeout --kill-after=5s 60s command` requests termination at 60 seconds and escalates after another 5 seconds if necessary; it is not a guaranteed completion deadline for uninterruptible kernel waits.

## 10. Interview scenarios and practice order

| Question | Strong starting point | Deeper follow-up |
|---|---|---|
| Batch job now takes 40 minutes | Baseline, progress, process tree, interval resource samples | CPU time vs. elapsed time; input size and child processes |
| CPU is 100% | Which tool/core/thread convention? Profile busy execution | CPU quotas, allocation/GC, useful work vs. spin |
| API slow but CPU idle | Waiting: DB, network, locks, queues, pools | Trace critical path; don't just increase threads |
| “No space left on device” | Filesystem bytes and inodes | Deleted-open files; correct mount and permissions |
| Process disappeared | Exit status, service logs, kernel/container events | OOM kill versus application crash versus operator action |
| “Too many open files” | Descriptor counts/types and process limits | Resource leak, concurrency, system-wide limits |
| Script succeeds despite failed command | Pipeline/exit-status handling | `pipefail`, expected grep status, conditional exceptions |
| Script breaks on filenames with spaces | Quoting and argument boundaries | Newlines in names; NUL-delimited processing |
| Two scheduled reports overlap | Runtime versus schedule; local lock | Multi-host coordination and idempotent outputs |
| Worker is a zombie | Parent has not reaped an exited child | Fix parent/reaper behavior; SIGKILL is ineffective |

### Five study sessions

1. **Process diagnosis:** explain the investigation in section 1 aloud; compare a sleeping process with a CPU-heavy workload in an isolated Linux environment.
2. **Resources:** interpret CPU/load/memory/disk outputs; explain why one snapshot can mislead.
3. **Logs:** count errors, group IPs, filter status codes, and explain assumptions and pipeline failures.
4. **Bash:** write an argument-validated script; handle missing, empty, spaced-path, and no-match inputs.
5. **Operations:** diagnose a failed service/cron job; explain locks, signals, timeouts, and verification.

For every answer use **symptom → evidence → hypothesis → targeted check → fix → verification**. Say what each command would establish; listing commands alone is not a diagnosis.

## 11. Primary references

- [Bash reference manual](https://www.gnu.org/s/bash/manual/bash.html): quoting, expansion, tests, arrays, redirection, traps, and exit behavior.
- [Linux ps manual](https://man7.org/linux/man-pages/man1/ps.1.html): process fields, CPU accounting, and state codes.
- [Linux strace manual](https://man7.org/linux/man-pages/man1/strace.1.html): syscall tracing, attachment, timing, and limitations.
- [sysstat](https://sysstat.github.io/): pidstat, iostat, mpstat, and sar documentation.
- [Linux /proc documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html): process and kernel interfaces.
- [GNU Coreutils manual](https://www.gnu.org/software/coreutils/manual/coreutils.html): file/text utilities, sort, timeout, and related command semantics.
- [util-linux flock manual](https://man7.org/linux/man-pages/man1/flock.1.html): advisory locking, descriptors, and filesystem caveats.
- [crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html): schedule fields and environment behavior; check local implementation.
- [curl manual](https://curl.se/docs/manpage.html): failure handling, timeouts, and timing fields.
