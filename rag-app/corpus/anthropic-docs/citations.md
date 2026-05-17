# Citations

This feature is eligible for Zero Data Retention (ZDR). When your organization has a ZDR arrangement, data sent through this feature is not stored after the API response is returned.

Claude is capable of providing detailed citations when answering questions about documents, helping you track and verify information sources in responses.

All active models support citations, with the exception of Haiku 3.

Here's an example of how to use citations with the Messages API:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": "The grass is green. The sky is blue.",
                    },
                    "title": "My Document",
                    "context": "This is a trustworthy document.",
                    "citations": {"enabled": True},
                },
                {"type": "text", "text": "What color is the grass and sky?"},
            ],
        }
    ],
)
print(response)
```

## Comparison with prompt-based approaches

In comparison with prompt-based citations solutions, the citations feature has the following advantages:

- **Cost savings**: If your prompt-based approach asks Claude to output direct quotes, you may see cost savings due to the fact that `cited_text` does not count towards your output tokens.
- **Better citation reliability**: Because citations are parsed into the respective response formats and `cited_text` is extracted, citations are guaranteed to contain valid pointers to the provided documents.
- **Improved citation quality**: In evaluations, the citations feature was found to be significantly more likely to cite the most relevant quotes from documents as compared to purely prompt-based approaches.

## How citations work

Integrate citations with Claude in these steps:

1. **Provide document(s) and enable citations.** Include documents in any of the supported formats: PDFs, plain text, or custom content documents. Set `citations.enabled=true` on each of your documents. Currently, citations must be enabled on all or none of the documents within a request. Only text citations are currently supported and image citations are not yet possible.

2. **Documents get processed.** Document contents are "chunked" in order to define the minimum granularity of possible citations. For PDFs, text is extracted and content is chunked into sentences. For plain text documents, content is chunked into sentences that can be cited from. For custom content documents, your provided content blocks are used as-is and no further chunking is done.

3. **Claude provides cited response.** Responses may now include multiple text blocks where each text block can contain a claim that Claude is making and a list of citations that support the claim. Citations reference specific locations in source documents. For PDFs, citations include the page number range (1-indexed). For plain text documents, citations include the character index range (0-indexed). For custom content documents, citations include the content block index range (0-indexed) corresponding to the original content list provided.

By default, plain text and PDF documents are automatically chunked into sentences. If you need more control over citation granularity (e.g., for bullet points or transcripts), use custom content documents instead.

For example, if you want Claude to be able to cite specific sentences from your RAG chunks, you should put each RAG chunk into a plain text document. Otherwise, if you do not want any further chunking to be done, or if you want to customize any additional chunking, you can put RAG chunks into custom content document(s).

### Citable vs non-citable content

- Text found within a document's `source` content can be cited from.
- `title` and `context` are optional fields that will be passed to the model but not used towards cited content.
- `title` is limited in length so you may find the `context` field to be useful in storing any document metadata as text or stringified json.

### Citation indices

- Document indices are 0-indexed from the list of all document content blocks in the request (spanning across all messages).
- Character indices are 0-indexed with exclusive end indices.
- Page numbers are 1-indexed with exclusive end page numbers.
- Content block indices are 0-indexed with exclusive end indices from the `content` list provided in the custom content document.

### Token costs

- Enabling citations incurs a slight increase in input tokens due to system prompt additions and document chunking.
- However, the citations feature is very efficient with output tokens. Under the hood, the model is outputting citations in a standardized format that are then parsed into cited text and document location indices. The `cited_text` field is provided for convenience and does not count towards output tokens.
- When passed back in subsequent conversation turns, `cited_text` is also not counted towards input tokens.

### Feature compatibility

Citations works in conjunction with other API features including prompt caching, token counting, and batch processing.

**Citations and Structured Outputs are incompatible.** If you enable citations on any user-provided document (Document blocks or RequestSearchResultBlock) and also include the `output_config.format` parameter (or the deprecated `output_format` parameter), the API will return a 400 error. This is because citations require interleaving citation blocks with text output, which is incompatible with the strict JSON schema constraints of structured outputs.

## Using Prompt Caching with Citations

Citations and prompt caching can be used together effectively. The citation blocks generated in responses cannot be cached directly, but the source documents they reference can be cached. To optimize performance, apply `cache_control` to your top-level document content blocks.

## Document Types

Three document types are supported for citations. Documents can be provided directly in the message (base64, text, or URL) or uploaded via the Files API and referenced by `file_id`:

| Type | Best for | Chunking | Citation format |
|---|---|---|---|
| Plain text | Simple text documents, prose | Sentence | Character indices (0-indexed) |
| PDF | PDF files with text content | Sentence | Page numbers (1-indexed) |
| Custom content | Lists, transcripts, special formatting, more granular citations | No additional chunking | Block indices (0-indexed) |

.csv, .xlsx, .docx, .md, and .txt files are not supported as document blocks. Convert these to plain text and include directly in message content.

### Plain text documents

Plain text documents are automatically chunked into sentences. You can provide them inline or by reference with their `file_id`. An example citation looks like:

```python
{
    "type": "char_location",
    "cited_text": "The exact text being cited",
    "document_index": 0,
    "document_title": "Document Title",
    "start_char_index": 0,
    "end_char_index": 50,
}
```

### PDF documents

PDF documents can be provided as base64-encoded data or by `file_id`. PDF text is extracted and chunked into sentences. As image citations are not yet supported, PDFs that are scans of documents and do not contain extractable text will not be citable.

### Custom content documents

Custom content documents give you control over citation granularity. No additional chunking is done and chunks are provided to the model according to the content blocks provided.

## Response Structure

When citations are enabled, responses include multiple text blocks with citations. Each text block carries a `citations` list with the cited text, the document index, the document title, and either character indices, page numbers, or block indices depending on document type.

For streaming responses, a `citations_delta` type is included that contains a single citation to be added to the `citations` list on the current `text` content block.
