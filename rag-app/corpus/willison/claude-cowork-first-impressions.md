# First impressions of Claude Cowork, Anthropic's general agent

Posted 12th January 2026 by Simon Willison.

New from Anthropic today is Claude Cowork, a "research preview" that they describe as "Claude Code for the rest of your work". It's currently available only to Max subscribers ($100 or $200 per month plans) as part of the updated Claude Desktop macOS application. Update 16th January 2026: it's now also available to $20/month Claude Pro subscribers.

I've been saying for a while now that Claude Code is a "general agent" disguised as a developer tool. It can help you with any computer task that can be achieved by executing code or running terminal commands, which covers almost anything, provided you know what you're doing with it. What it really needs is a UI that doesn't involve the terminal and a name that doesn't scare away non-developers.

"Cowork" is a pretty solid choice on the name front.

## What it looks like

The interface for Cowork is a new tab in the Claude desktop app, called Cowork. It sits next to the existing Chat and Code tabs.

It looks very similar to the desktop interface for regular Claude Code. You start with a prompt, optionally attaching a folder of files. It then starts work.

I tried it out against my perpetually growing "blog-drafts" folder with the following prompt:

> Look at my drafts that were started within the last three months and then check that I didn't publish them on simonwillison.net using a search against content on that site and then suggest the ones that are most close to being ready

It started by running a command to find draft files modified in the last 90 days. That `/sessions/zealous-bold-ramanujan/mnt/blog-drafts` path instantly caught my eye. Anthropic say that Cowork can only access files you grant it access to — it looks to me like they're mounting those files into a containerized environment, which should mean we can trust Cowork not to be able to access anything outside of that sandbox.

It turns out I have 46 draft files from the past three months. Claude then went to work with its search tool, running 44 individual searches against `site:simonwillison.net` to figure out which of my drafts had already been published.

That's a good response. It found exactly what I needed to see, although those upgrade instructions are actually published elsewhere now (in the Datasette docs) and weren't actually intended for my blog.

## Isn't this just Claude Code?

I've seen a few people ask what the difference between this and regular Claude Code is. The answer is not a lot. As far as I can tell Claude Cowork is regular Claude Code wrapped in a less intimidating default interface and with a filesystem sandbox configured for you without you needing to know what a "filesystem sandbox" is.

Update: It's more than just a filesystem sandbox — I had Claude Code reverse engineer the Claude app and it found out that Claude uses VZVirtualMachine — the Apple Virtualization Framework — and downloads and boots a custom Linux root filesystem.

I think that's a really smart product. Claude Code has an enormous amount of value that hasn't yet been unlocked for a general audience, and this seems like a pragmatic approach.

## The ever-present threat of prompt injection

With a feature like this, my first thought always jumps straight to security. How big is the risk that someone using this might be hit by hidden malicious instruction somewhere that break their computer or steal their data?

Anthropic touch on that directly in the announcement:

> You should also be aware of the risk of "prompt injections": attempts by attackers to alter Claude's plans through content it might encounter on the internet. We've built sophisticated defenses against prompt injections, but agent safety — that is, the task of securing Claude's real-world actions — is still an active area of development in the industry. These risks aren't new with Cowork, but it might be the first time you're using a more advanced tool that moves beyond a simple conversation. We recommend taking precautions, particularly while you learn how it works.

That help page includes the following tips. To minimize risks:

- Avoid granting access to local files with sensitive information, like financial documents.
- When using the Claude in Chrome extension, limit access to trusted sites.
- If you chose to extend Claude's default internet access settings, be careful to only extend internet access to sites you trust.
- Monitor Claude for suspicious actions that may indicate prompt injection.

I do not think it is fair to tell regular non-programmer users to watch out for "suspicious actions that may indicate prompt injection".

I'm sure they have some impressive mitigations going on behind the scenes. I recently learned that the summarization applied by the WebFetch function in Claude Code and now in Cowork is partly intended as a prompt injection protection layer.

But Anthropic are being honest here with their warnings: they can attempt to filter out potential attacks all they like but the one thing they can't provide is guarantees that no future attack will be found that sneaks through their defenses and steals your data.

The problem with prompt injection remains that until there's a high profile incident it's really hard to get people to take it seriously. I myself have all sorts of Claude Code usage that could cause havoc if a malicious injection got in. Cowork does at least run in a filesystem sandbox by default, which is more than can be said for my `claude --dangerously-skip-permissions` habit.

## This is still a strong signal of the future

Security worries aside, Cowork represents something really interesting. This is a general agent that looks well positioned to bring the wildly powerful capabilities of Claude Code to a wider audience.

I would be very surprised if Gemini and OpenAI don't follow suit with their own offerings in this category.
