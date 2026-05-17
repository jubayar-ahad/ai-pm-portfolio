# Models & Pricing

Cursor supports all frontier coding models from OpenAI, Anthropic, Google, and more. Every individual plan includes two usage pools so you can pick the right balance of intelligence, speed, and cost.

## Usage pools

There are two separate usage pools for individual plans, each resetting with your monthly billing cycle:

- **Auto + Composer**: Significantly more included usage when Auto or Composer 2 is selected. Designed for everyday agentic coding at a lower cost.
- **API**: Charged at the model's API price. Individual plans include at least $20 of API usage each month (more on higher tiers) with the option to pay for additional usage as needed.

Both pools are visible in your editor settings and on your usage dashboard.

## Auto + Composer pool

Auto allows Cursor to select models that balance intelligence, cost efficiency, and reliability. It is useful for everyday tasks.

### Auto pricing

| Token type          | Price per 1M tokens |
| :------------------ | :------------------ |
| Input + Cache Write | $1.25               |
| Output              | $6.00               |
| Cache Read          | $0.25               |

### Composer pricing

Composer 2 is Cursor's own model, trained to be highly capable for agentic coding. Both Auto and Composer 2 draw from this pool.

## API pool

When you select a specific model (or use Premium routing), usage is drawn from the API pool at that model's API rate.

### Model pricing

All prices are per million tokens, sourced from each provider's API pricing. The models table lists pricing for options from Anthropic, Cursor, Google, OpenAI, xAI, and Moonshot, including variants with different pricing tiers based on capability and speed.

### Premium routing

Premium allows Cursor to select the most capable models for you, recommended for the most complex tasks. The Cursor team selects Premium models based on internal benchmarks, evaluations, and user feedback.

Premium pricing is based on the selected model's API rate. Check your usage page to see cost and model selection at the request level.

## Plans

All individual plans include unlimited tab completions, extended agent usage limits on all models, access to Bugbot, and access to Cloud Agents.

| Plan         | Price   | API usage included | Auto + Composer         |
| :----------- | :------ | :----------------- | :---------------------- |
| **Pro**      | $20/mo  | $20                | Generous included usage |
| **Pro Plus** | $60/mo  | $70                | Generous included usage |
| **Ultra**    | $200/mo | $400               | Generous included usage |

Since different models have different API costs, your model selection affects how quickly your included usage is consumed.

### How much usage do I need?

- **Daily Tab users**: Always stay within $20
- **Limited Agent users**: Often stay within the included $20
- **Daily Agent users**: Typically $60–$100/mo total usage
- **Power users (multiple agents/automation)**: Often $200+/mo total usage

### What happens when I reach my limit?

When you exceed your included monthly usage, you can either:

- **Add on-demand usage**: Continue at the same API rates with pay-as-you-go billing
- **Upgrade your plan**: Move to a higher tier for more included usage

On-demand usage is billed monthly at the same rates. Requests are never downgraded in quality or speed.

### Teams

There are two teams plans: Teams ($40/user/mo) and Enterprise (Custom).

Team plans provide additional features like privacy mode enforcement, admin dashboard with usage stats, centralized team billing, and SAML/OIDC SSO.

We recommend Teams for any customer that is happy self-serving. We recommend Enterprise for customers that need priority support, pooled usage, invoicing, SCIM, or advanced security controls.

Learn more about Teams pricing.

## Cursor Token Rate

On Teams plans, non-Auto agent requests include a Cursor Token Rate of $0.25 per million tokens. This rate applies on top of model API pricing for included usage, on-demand usage, and BYOK usage. Auto is exempt from the Cursor Token Rate.

## Max Mode

Max Mode extends the context window to the maximum a model supports. More context gives models deeper understanding of your codebase, leading to better results on complex tasks. The models table above shows each model's maximum context size.

Max Mode uses token-based pricing at the model's API rate, so it consumes usage faster than the default context window. On current individual plans, Max Mode is billed at the model's API rate. On Teams plans, non-Auto requests include the Cursor Token Rate. On legacy request-based plans, Max Mode adds a 20% surcharge.

## FAQ

### Where are models hosted?

Models are hosted on US, Canada, & Iceland based infrastructure by the model's provider, a trusted partner, or Cursor directly.

When Privacy Mode is enabled, neither Cursor nor model providers store your data. All data is deleted after each request. For details see our Privacy Policy and Security pages.

### Where can I find pricing terms?

For enterprise pricing details, billing terms, and fee calculations, see the Pricing Policy.
