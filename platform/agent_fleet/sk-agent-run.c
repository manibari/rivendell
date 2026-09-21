/*
 * sk-agent-run — tiny launcher for launchd agents.
 *
 * Usage: sk-agent-run <project_dir> <script> [args...]
 *
 * Sets REPO_DIR env var and chdir into <project_dir>, then execs bash.
 * Scripts should use $REPO_DIR instead of $(pwd) to avoid macOS TCC/getcwd failures.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: sk-agent-run <project_dir> <script> [args...]\n");
        return 1;
    }

    const char *project_dir = argv[1];

    /* Export REPO_DIR so scripts don't need pwd (which fails under TCC) */
    setenv("REPO_DIR", project_dir, 1);

    if (chdir(project_dir) != 0) {
        perror("chdir");
        return 1;
    }

    /* Build argv for exec: bash <script> [extra args...] */
    int new_argc = argc - 1;  /* bash + script + extra args */
    char **new_argv = malloc((new_argc + 1) * sizeof(char *));
    if (!new_argv) {
        perror("malloc");
        return 1;
    }

    new_argv[0] = "/bin/bash";
    for (int i = 2; i < argc; i++) {
        new_argv[i - 1] = argv[i];
    }
    new_argv[new_argc] = NULL;

    execv("/bin/bash", new_argv);
    perror("execv");
    return 1;
}
