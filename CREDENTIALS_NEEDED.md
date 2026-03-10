# Spira Instance Credentials Needed

To test the Spira API integration with your actual instance, please provide the following information:

## Required Information

1. **Spira Instance URL**
   - Format: `https://your-company.spiraservice.net`
   - Example: `https://internal-dermot.spiraservice.net`
   - This is the URL you use to access Spira in your browser

2. **Username**
   - Your Spira login username
   - Example: `dermot.canniffe` or `admin`

3. **API Key (RSS Token)**
   - Format: `{00000000-0000-0000-0000-000000000000}` (with curly braces)
   - How to get it:
     - Log into Spira
     - Click your profile (top right)
     - Go to "RSS Tokens" or "API Keys"
     - Copy the key (include the `{` and `}`)

4. **Project ID**
   - The numeric ID of your Spira project
   - You can find this in the URL when viewing a project
   - Example: If URL is `https://spira.../1/Project/...`, the project ID is `1`

5. **Test Set ID** (Optional for initial testing)
   - The numeric ID of a test set where test runs will be recorded
   - You can find this in the URL when viewing a test set
   - Example: If URL is `https://spira.../TestSet/10.aspx`, the test set ID is `10`

6. **Test Case ID** (Optional - for testing test run creation)
   - The numeric ID of a test case to record results against
   - Example: `123`

## How to Provide This Information

### Option 1: Create .env file (Recommended)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```bash
   SPIRA_URL=https://internal-dermot.spiraservice.net
   SPIRA_USERNAME=your_username
   SPIRA_API_KEY={your-api-key-here}
   SPIRA_PROJECT_ID=1
   SPIRA_TEST_SET_ID=10
   ```

3. Run the connection test:
   ```bash
   python test_spira_connection.py
   ```

### Option 2: Provide in Chat

You can also just paste the values here in chat, and I'll help you test the connection. For example:

```
Spira URL: https://internal-dermot.spiraservice.net
Username: dermot.canniffe
API Key: {12345678-1234-1234-1234-123456789012}
Project ID: 1
Test Set ID: 10
```

## What We'll Test

Once you provide the credentials, we can:

1. ✅ Test authentication with your Spira instance
2. ✅ Verify the API client can connect
3. ✅ Get real API responses to validate our implementation
4. ✅ (Optional) Create a test run to verify end-to-end functionality
5. ✅ Test evidence upload if you have sample files

## Security Notes

- Your `.env` file is already in `.gitignore` and won't be committed
- API keys are masked in logs
- If you provide credentials in chat, I won't store them permanently
- You can regenerate your API key in Spira at any time

## Next Steps

After providing credentials, we can:
- Run `test_spira_connection.py` to verify connectivity
- Test creating actual test runs in your Spira instance
- Validate the complete integration workflow
- Test with your actual test result files
