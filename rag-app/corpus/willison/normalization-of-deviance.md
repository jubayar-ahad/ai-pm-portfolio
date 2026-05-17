# The Normalization of Deviance in AI

Posted 10th December 2025 by Simon Willison.

This thought-provoking essay from Johann Rehberger directly addresses something that has been a concern for quite a while: in the absence of any headline-grabbing examples of prompt injection vulnerabilities causing real economic harm, is anyone going to care?

Johann describes the concept of the "Normalization of Deviance" as directly applying to this question.

Coined by Diane Vaughan, the key idea here is that organizations that get away with "deviance" — ignoring safety protocols or otherwise relaxing their standards — will start baking that unsafe attitude into their culture. This can work fine, until it doesn't. The Space Shuttle Challenger disaster has been partially blamed on this class of organizational failure.

As Johann puts it:

> In the world of AI, we observe companies treating probabilistic, non-deterministic, and sometimes adversarial model outputs as if they were reliable, predictable, and safe.
>
> Vendors are normalizing trusting LLM output, but current understanding violates the assumption of reliability.
>
> The model will not consistently follow instructions, stay aligned, or maintain context integrity. This is especially true if there is an attacker in the loop (e.g. indirect prompt injection).
>
> However, we see more and more systems allowing untrusted output to take consequential actions. Most of the time it goes well, and over time vendors and organizations lower their guard or skip human oversight entirely, because "it worked last time."
>
> This dangerous bias is the fuel for normalization: organizations confuse the absence of a successful attack with the presence of robust security.
