# har2llm

Process HAR (HTTP Archive) files into clean, LLM-readable summaries.

## Installation

```bash
git clone https://github.com/mdev34-lab/har2llm
pip install .
```

Or for development:

```bash
git clone https://github.com/mdev34-lab/har2llm
pip install -e .
```

## Usage

### Command Line

```bash
har2llm input.har -o output.txt
```

### Python API

```python
from har2llm import process_har

result = process_har('input.har')
print(result)
```

## Features

- **Header Filtering**: Removes verbose browser headers (User-Agent, Accept-Encoding, etc.) and extracts only meaningful request headers
- **URL Simplification**: Replaces UUIDs and numeric IDs with placeholders (`{UUID}`, `{ID}`) to group similar API endpoints
- **Body Summarization**: Truncates large JSON bodies while preserving structure
- **Sequence Compression**:合并 consecutive duplicate requests into a single entry with a repeat count
- **LLM-Optimized Output**: Produces a clean, readable format ideal for feeding to LLMs or for documentation

## Example

Input: A HAR file with 100+ browser requests

Output:
```
# GLOBAL HEADERS (Common to 80%+ of requests)
  authorization: Bearer xxx
  x-api-key: xxx

# REQUEST LOG
## GET api.example.com/users/{ID}
  Query: {"page": 1}
  <- Response 200: [{"id": 1, "name": "Alice"}... (+49 more items)]

## POST api.example.com/users [Repeated 3x]
  Headers: {"content-type": "application/json"}
  Body: {"name": "New User", "email": "user@example.com"}
  <- Response 201: {"id": 42, "success": true}
```

## Requirements

- Python 3.9+
- No external dependencies

## License

MIT
