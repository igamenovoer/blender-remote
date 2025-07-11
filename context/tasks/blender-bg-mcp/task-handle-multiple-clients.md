`BLD_Remote_MCP` should be able to handle multiple clients connecting to it, in this way:
- all commands from different clients are queued, and the order of execution is unspecified
- each user can only has one command running or queued at a time, if the user tries to run another command while one is running, it will return as error, and give the user a rejection message
- the user can cancel the command by sending a `cancel_last` command, which will cancel the last command of the user, if there is one running or queued
- - for queued commands, it should be removed from the queue, if 