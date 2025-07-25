# Zip Session Functionality Guide

## Overview

The CSV Query Tool now supports saving and loading sessions as zip files, similar to the old project. This functionality allows you to preserve your entire work session including:

- SQLite database with all tables and data
- Query history with organized groups and queries
- Current CSV data and headers
- SQL editor content
- Python editor content

## How to Use

### Saving a Session

1. **File Menu**: Go to `File -> Save Session`
2. **Choose Location**: Select where to save your session zip file
3. **File Extension**: The file will be saved with a `.zip` extension
4. **Confirmation**: You'll see a success message when the session is saved

### Loading a Session

1. **File Menu**: Go to `File -> Open Session`
2. **Select File**: Choose a previously saved session zip file
3. **Automatic Loading**: The application will automatically:
   - Restore the SQLite database connection
   - Load all tables and data
   - Restore query history
   - Load CSV data into the editor
   - Restore SQL and Python editor content
4. **Confirmation**: You'll see a success message when the session is loaded

## Session Contents

Each session zip file contains:

### 1. `session_db.sqlite`
- Complete SQLite database with all tables
- All imported CSV data
- Custom tables created during the session

### 2. `history.json`
- Query history organized in groups
- Saved SQL queries with names and parameters
- Task numbers and metadata

### 3. `session.json`
- Current CSV data and headers
- SQL editor content
- Python editor content
- Session metadata

## Benefits

- **Complete Preservation**: Everything from your work session is saved
- **Portability**: Share sessions with colleagues or move between computers
- **Backup**: Create backups of important work sessions
- **Organization**: Keep different projects in separate session files
- **Compatibility**: Similar to the old project's session format

## Technical Details

- Sessions use ZIP compression for efficient storage
- Database backup uses SQLite's built-in backup functionality
- Temporary files are automatically cleaned up
- UTF-8 encoding ensures proper handling of international characters

## Testing

A test session (`test_session.zip`) has been created with sample data. You can load this session to test the functionality:

1. Open the CSV Query Tool
2. Go to File -> Open Session
3. Select `test_session.zip`
4. Verify that test data, queries, and code are loaded correctly

## Troubleshooting

- **File Not Found**: Ensure the session zip file exists and is accessible
- **Corrupted Session**: Check that the zip file is not corrupted
- **Permission Issues**: Ensure you have read/write permissions for the session file location
- **Database Errors**: If database loading fails, check the error message in the terminal

## Migration from JSON Sessions

If you have old JSON session files, you'll need to:
1. Load the JSON session data manually
2. Recreate your work environment
3. Save as a new zip session

The new zip format is more comprehensive and preserves database state, which JSON sessions could not do.