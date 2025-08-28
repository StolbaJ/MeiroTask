# ShowAds Data Connector

A robust Python application that processes customer data from CSV files, validates it according to business rules, and reliably sends it to the ShowAds API for web banner display.

## Features

- **CSV Processing**: Efficiently processes large CSV files with millions of records using chunked reading
- **Data Validation**: Comprehensive validation of customer data including name format, age limits, UUID cookies, and banner IDs
- **API Integration**: Robust integration with ShowAds API including authentication, token management, and retry logic
- **Configurable**: Runtime-configurable age limits and processing parameters without redeployment
- **Production Ready**: Comprehensive logging, error handling, and monitoring capabilities
- **Containerized**: Docker support for easy deployment and scaling
- **Well Tested**: Comprehensive test suite with high code coverage

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
├── main.py                 # Entry point and CLI interface
├── config.py              # Configuration management
├── models.py              # Data models and validation
├── csv_processing.py       # CSV processing and data validation
├── showads_cli.py      # ShowAds API client
├── data_connector.py      # Main orchestration logic
└── tests/                 # Comprehensive test suite
```

## Requirements

- Python 3.13
- Docker (optional, for containerized deployment)

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Or build and run manually:
```bash
docker build -t showads-connector .
docker run -v $(pwd)/data:/app/data showads-connector /app/data/data.csv
```

## Usage

### Command Line Interface

```bash
python main.py [OPTIONS] CSV_FILE

Arguments:
  CSV_FILE                    Path to the CSV file containing customer data

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}
                             Set the logging level (default: INFO)
  --min-age INTEGER          Minimum age for customer validation
  --max-age INTEGER          Maximum age for customer validation  
  --batch-size INTEGER       Batch size for API requests (max 1000)
  -h, --help                 Show this message and exit
```

The application can be configured through environment variables or command line arguments:

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHOWADS_API_URL` | `https://golang-assignment-968918017632.europe-west3.run.app` | ShowAds API base URL |
| `PROJECT_KEY` | `meiro-data-connector-project` | Project key for API authentication |
| `MIN_AGE` | `18` | Minimum age for customer validation |
| `MAX_AGE` | `120` | Maximum age for customer validation |
| `BATCH_SIZE` | `1000` | Number of records to process in each API batch |
| `MAX_RETRIES` | `3` | Maximum number of retry attempts for API calls |
| `RETRY_DELAY` | `1` | Base delay between retries (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

## CSV File Format

The CSV file should contain the following columns:

| Column | Type | Description | Validation |
|--------|------|-------------|------------|
| `Name` | string | Customer name | Only letters and spaces |
| `Age` | integer | Customer age | Must be within MIN_AGE and MAX_AGE |
| `Cookie` | string | Customer cookie | Must be valid UUID format |
| `Banner_id` | integer | Banner ID | Must be between 0 and 99 |

### Sample CSV Data included in repository


## API Integration

The application integrates with the ShowAds API using three endpoints:

### Authentication
- **POST** `/auth` - Obtain access token (24h expiry)
- Automatic token refresh when expired

### Banner Display
- **POST** `/banners/show` - Single customer banner request
- **POST** `/banners/show/bulk` - Bulk banner requests (max 1000 per batch)

The client includes:
- Automatic authentication and token management
- Retry logic with exponential backoff
- Rate limiting and error handling
- Comprehensive logging of API interactions

## Data Validation

The application performs comprehensive validation:

### Name Validation
- Must contain only letters and spaces
- Leading/trailing whitespace is trimmed

### Age Validation  
- Must be integer within configurable MIN_AGE and MAX_AGE range
- Default range: 18-120 years

### Cookie Validation
- Must be valid UUID format
- Validated using Python's UUID library

### Banner ID Validation
- Must be integer between 0 and 99 (inclusive)

**Invalid records are skipped and logged for debugging purposes.**

## Logging

The application provides comprehensive logging:

- **INFO**: General operation status, statistics, and completion messages
- **DEBUG**: Detailed processing information, API calls, and chunk processing
- **WARNING**: Recoverable errors, retries, and validation failures
- **ERROR**: Non-recoverable errors and failures

Logs are output to stdout/stderr for container compatibility.

## Error Handling

The application handles various error scenarios:

- **CSV Processing Errors**: File not found, parsing errors, empty files
- **Validation Errors**: Invalid data formats, out-of-range values
- **API Errors**: Network failures, authentication issues, rate limiting
- **Configuration Errors**: Invalid settings, missing required values

All errors are logged with appropriate context for debugging.

## Testing

The application includes a comprehensive test suite:

```bash
# Run all tests
python -m pytest

### Test Coverage

The test suite is divided into two categories:

**Unit Tests** (`@pytest.mark.unit`):
- **test_models.py** - Data validation models (Customer, API requests/responses)
- **test_config.py** - Configuration management and validation
- **test_csv_processor.py** - CSV processing and data validation logic
- **test_showads_client.py** - ShowAds API client with mocked HTTP calls

**Integration Tests** (`@pytest.mark.integration`):
- **test_data_connector.py** - End-to-end orchestration of CSV processing → validation → API submission

## Performance

The application is optimized for performance:

- **Chunked Processing**: Handles large CSV files without memory issues
- **Batch API Calls**: Reduces API overhead with bulk requests
- **Efficient Validation**: Fast validation using Pydantic models
- **Connection Pooling**: Reuses HTTP connections for better performance

## Monitoring

The application provides monitoring capabilities:

- **Processing Statistics**: Total records, validation success rate
- **API Metrics**: Success/failure rates, response times
- **Error Tracking**: Detailed error logging and categorization

## Deployment

### Production Deployment

1. Build the production image:
```bash
docker compose up --build
```
### Test Deployment

```bash
docker compose --profile dev up  --build
```



