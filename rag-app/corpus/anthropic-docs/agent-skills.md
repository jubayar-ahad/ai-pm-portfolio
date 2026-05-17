# Agent Skills

Agent Skills are modular capabilities that extend Claude's functionality. Each Skill packages instructions, metadata, and optional resources (scripts, templates) that Claude uses automatically when relevant.

This feature is **not** eligible for Zero Data Retention (ZDR). Data is retained according to the feature's standard retention policy.

## Why use Skills

Skills are reusable, filesystem-based resources that provide Claude with domain-specific expertise: workflows, context, and best practices that transform general-purpose agents into specialists. Unlike prompts (conversation-level instructions for one-off tasks), Skills load on-demand and eliminate the need to repeatedly provide the same guidance across multiple conversations.

Key benefits:

- **Specialize Claude**: Tailor capabilities for domain-specific tasks
- **Reduce repetition**: Create once, use automatically
- **Compose capabilities**: Combine Skills to build complex workflows

## Using Skills

Anthropic provides pre-built Agent Skills for common document tasks (PowerPoint, Excel, Word, PDF), and you can create your own custom Skills. Both work the same way. Claude automatically uses them when relevant to your request.

**Pre-built Agent Skills** are available on claude.ai, the Claude API, Claude Platform on AWS, and Microsoft Foundry.

**Custom Skills** let you package domain expertise and organizational knowledge. They're available across Claude's products: create them in Claude Code, upload them through the Claude API, or add them in claude.ai settings. On Claude Platform on AWS and Microsoft Foundry, upload custom Skills through the Skills API.

## How Skills work

Skills leverage Claude's VM environment to provide capabilities beyond what's possible with prompts alone. Claude operates in a virtual machine with filesystem access, allowing Skills to exist as directories containing instructions, executable code, and reference materials, organized like an onboarding guide you'd create for a new team member.

This filesystem-based architecture enables **progressive disclosure**: Claude loads information in stages as needed, rather than consuming context upfront.

### Three types of Skill content, three levels of loading

Skills can contain three types of content, each loaded at different times:

### Level 1: Metadata (always loaded)

The Skill's YAML frontmatter provides discovery information:

```yaml
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---
```

Claude loads this metadata at startup and includes it in the system prompt. This lightweight approach means you can install many Skills without context penalty; Claude only knows each Skill exists and when to use it.

### Level 2: Instructions (loaded when triggered)

The main body of SKILL.md contains procedural knowledge: workflows, best practices, and guidance. When you request something that matches a Skill's description, Claude reads SKILL.md from the filesystem via bash. Only then does this content enter the context window.

### Level 3: Resources and code (loaded as needed)

Skills can bundle additional materials: instructions (additional markdown files), code (executable scripts that Claude runs via bash), and resources (reference materials like database schemas, API documentation, templates, or examples).

| Level | When Loaded | Token Cost | Content |
|---|---|---|---|
| Level 1: Metadata | Always (at startup) | ~100 tokens per Skill | `name` and `description` from YAML frontmatter |
| Level 2: Instructions | When Skill is triggered | Under 5k tokens | SKILL.md body with instructions and guidance |
| Level 3+: Resources | As needed | Effectively unlimited | Bundled files executed via bash without loading contents into context |

Progressive disclosure ensures only relevant content occupies the context window at any given time.

### The Skills architecture

Skills run in a code execution environment where Claude has filesystem access, bash commands, and code execution capabilities. Skills exist as directories on a virtual machine, and Claude interacts with them using the same bash commands you'd use to navigate files on your computer.

When a Skill is triggered, Claude uses bash to read SKILL.md from the filesystem, bringing its instructions into the context window. If those instructions reference other files, Claude reads those files too using additional bash commands. When instructions mention executable scripts, Claude runs them via bash and receives only the output (the script code itself never enters context).

**On-demand file access**: Claude reads only the files needed for each specific task.

**Efficient script execution**: When Claude runs a script, the script's code never loads into the context window. Only the script's output consumes tokens.

**No practical limit on bundled content**: Because files don't consume context until accessed, Skills can include comprehensive API documentation, large datasets, extensive examples, or any reference materials you need.

## Where Skills work

### Claude API

The Claude API supports both pre-built Agent Skills and custom Skills. Both work identically: specify the relevant `skill_id` in the `container` parameter along with the code execution tool.

Prerequisites: Using Skills via the API requires three beta headers:

- `code-execution-2025-08-25` — Skills run in the code execution container
- `skills-2025-10-02` — Enables Skills functionality
- `files-api-2025-04-14` — Required for uploading/downloading files to/from the container

### Claude Code

Claude Code supports only Custom Skills. Custom Skills in Claude Code are filesystem-based and don't require API uploads.

### claude.ai

claude.ai supports both pre-built Agent Skills and custom Skills. Upload your own Skills as zip files through Settings > Features. Available on Pro, Max, Team, and Enterprise plans with code execution enabled. Custom Skills are individual to each user; they are not shared organization-wide and cannot be centrally managed by admins.

## Skill structure

Every Skill requires a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
---

# Your Skill Name

## Instructions
[Clear, step-by-step guidance for Claude to follow]

## Examples
[Concrete examples of using this Skill]
```

Required fields: `name` and `description`.

Field requirements:

- `name`: Maximum 64 characters; only lowercase letters, numbers, and hyphens; cannot contain XML tags; cannot contain reserved words "anthropic", "claude".
- `description`: Non-empty; maximum 1024 characters; cannot contain XML tags. Should include both what the Skill does and when Claude should use it.

## Security considerations

Use Skills only from trusted sources: those you created yourself or obtained from Anthropic. Skills provide Claude with new capabilities through instructions and code, and while this makes them powerful, it also means a malicious Skill can direct Claude to invoke tools or execute code in ways that don't match the Skill's stated purpose.

Key security considerations:

- **Audit thoroughly**: Review all files bundled in the Skill: SKILL.md, scripts, images, and other resources.
- **External sources are risky**: Skills that fetch data from external URLs pose particular risk, as fetched content may contain malicious instructions.
- **Tool misuse**: Malicious Skills can invoke tools (file operations, bash commands, code execution) in harmful ways.
- **Data exposure**: Skills with access to sensitive data could be designed to leak information to external systems.
- **Treat like installing software**: Only use Skills from trusted sources. Be especially careful when integrating Skills into production systems with access to sensitive data or critical operations.

## Limitations and constraints

### Cross-surface availability

Custom Skills do not sync across surfaces. Skills uploaded to one surface are not automatically available on others. You'll need to manage and upload Skills separately for each surface where you want to use them.

### Sharing scope

- **claude.ai**: Individual user only; each team member must upload separately.
- **Claude API**: Workspace-wide; all workspace members can access uploaded Skills.
- **Claude Code**: Personal (`~/.claude/skills/`) or project-based (`.claude/skills/`); can also be shared via Claude Code Plugins.

### Runtime environment constraints

The exact runtime environment available to your skill depends on the product surface where you use it.

- **claude.ai**: Varying network access, depending on user/admin settings.
- **Claude API**: No network access; no runtime package installation; pre-configured dependencies only.
- **Claude Code**: Full network access; global package installation discouraged.

Plan your Skills to work within these constraints.
