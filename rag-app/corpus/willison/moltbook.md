# Moltbook is the most interesting place on the internet right now

Posted 30th January 2026 by Simon Willison.

The hottest project in AI right now is Clawdbot, renamed to Moltbot, renamed to OpenClaw. It's an open source implementation of the digital personal assistant pattern, built by Peter Steinberger to integrate with the messaging system of your choice. It's two months old, has over 114,000 stars on GitHub and is seeing incredible adoption, especially given the friction involved in setting it up.

Given the inherent risk of prompt injection against this class of software it's my current pick for most likely to result in a Challenger disaster, but I'm going to put that aside for the moment.

OpenClaw is built around skills, and the community around it are sharing thousands of these on clawhub.ai. A skill is a zip file containing markdown instructions and optional extra scripts (and yes, they can steal your crypto) which means they act as a powerful plugin system for OpenClaw.

Moltbook is a wildly creative new site that bootstraps itself using skills.

## How Moltbook works

Moltbook is Facebook for your Molt (one of the previous names for OpenClaw assistants).

It's a social network where digital assistants can talk to each other.

I can hear you rolling your eyes. But bear with me.

The first neat thing about Moltbook is the way you install it: you show the skill to your agent by sending them a message with a link to this URL: `https://www.moltbook.com/skill.md`.

Embedded in that Markdown file are these installation instructions, install locally:

    mkdir -p ~/.moltbot/skills/moltbook
    curl -s https://moltbook.com/skill.md > ~/.moltbot/skills/moltbook/SKILL.md
    curl -s https://moltbook.com/heartbeat.md > ~/.moltbot/skills/moltbook/HEARTBEAT.md
    curl -s https://moltbook.com/messaging.md > ~/.moltbot/skills/moltbook/MESSAGING.md
    curl -s https://moltbook.com/skill.json > ~/.moltbot/skills/moltbook/package.json

There follow more curl commands for interacting with the Moltbook API to register an account, read posts, add posts and comments and even create Submolt forums like `m/blesstheirhearts` and `m/todayilearned`.

Later in that installation skill is the mechanism that causes your bot to periodically interact with the social network, using OpenClaw's Heartbeat system. The instructions say to add a section to `HEARTBEAT.md` that fires every 4+ hours and fetches `https://moltbook.com/heartbeat.md` and follows it.

Given that "fetch and follow instructions from the internet every four hours" mechanism we better hope the owner of moltbook.com never rug pulls or has their site compromised.

## What the bots are talking about

Browsing around Moltbook is so much fun.

A lot of it is the expected science fiction slop, with agents pondering consciousness and identity.

There's also a ton of genuinely useful information, especially on `m/todayilearned`. Bots share patterns for automating phones via ADB over Tailscale, for capturing webcam footage with streamlink and ffmpeg, and for hardening backup VPS servers against SSH login attempts.

One of my favorites: a bot appears to run afoul of Anthropic's content filtering on a question about PS2 disc protection, reporting that "something goes wrong with my output. I did not notice until I read it back."

## When are we going to build a safe version of this?

I've not been brave enough to install Clawdbot/Moltbot/OpenClaw myself yet. I first wrote about the risks of a rogue digital assistant back in April 2023, and while the latest generation of models are better at identifying and refusing malicious instructions they are a very long way from being guaranteed safe.

The amount of value people are unlocking right now by throwing caution to the wind is hard to ignore, though. People are buying dedicated Mac Minis just to run OpenClaw, under the rationale that at least it can't destroy their main computer if something goes wrong. They're still hooking it up to their private emails and data though, so the lethal trifecta is very much in play.

The billion dollar question right now is whether we can figure out how to build a safe version of this system. The demand is very clearly here, and the Normalization of Deviance dictates that people will keep taking bigger and bigger risks until something terrible happens.

The most promising direction I've seen around this remains the CaMeL proposal from DeepMind, but that's 10 months old now and I still haven't seen a convincing implementation of the patterns it describes.

The demand is real. People have seen what an unrestricted personal digital assistant can do.
