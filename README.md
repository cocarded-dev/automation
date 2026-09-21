# Etsy Order Fulfillment Automation

Automated order fulfillment system for Etsy shop with personalization capabilities and supplier integration.

## Features

- **Etsy Integration**: Automatically fetches new orders via Etsy API
- **Smart Classification**: Classifies orders based on personalization requirements and customer location
- **US Orders**: Downloads shipping labels automatically
- **International Orders**: Extracts IOSS numbers and order values
- **Personalization**: Automated PSD file editing for personalized items
- **Supplier Integration**: Automated form submission to supplier (cardtrophy.com)
- **Scheduling**: Runs daily at 6 PM (configurable)
- **Catalog Management**: Google Sheets integration for product catalog

## Architecture

```
┌─────────────────┐
│   Etsy API      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Order Processor │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Catalog │ │ Image        │
│ (Google │ │ Processor    │
│ Sheets) │ └──────────────┘
└─────────┘         │
                    ▼
           ┌────────────────┐
           │ Supplier       │
           │ Automation     │
           └────────────────┘
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Etsy Developer Account
- Google Cloud Project (for Sheets API)
- Chrome/Chromium browser

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Etsy API Setup

1. Go to [Etsy Developer Portal](https://www.etsy.com/developers)
2. Create a new app
3. Get API Key and Shared Secret
4. Generate Access Token using OAuth
5. Add credentials to `.env` file

### 4. Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create OAuth 2.0 credentials
4. Download credentials.json
5. Create a Google Sheet with the following structure:

**Sheet Name: "Catalog"**

| listing_id | sku | product_name | has_personalization | psd_file_url | file_variant | hologram_type | product_url |
|------------|-----|--------------|---------------------|--------------|--------------|---------------|-------------|
| 123456789  | SKU1 | Product A   | true                | https://...  | single       | standard      | https://...  |

### 5. Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
ETSY_API_KEY=your_api_key
ETSY_SHARED_SECRET=your_shared_secret
ETSY_SHOP_ID=your_shop_id
ETSY_ACCESS_TOKEN=your_access_token
ETSY_ACCESS_TOKEN_SECRET=your_access_token_secret
GOOGLE_SHEET_ID=your_sheet_id
SUPPLIER_EMAIL=your_email
SUPPLIER_PASSWORD=your_password
```

### 6. Google Sheets Authentication

Run the script once to authenticate:

```bash
python -c "from google_sheets_catalog import GoogleSheetsCatalog; GoogleSheetsCatalog()"
```

This will open a browser window for OAuth authentication.

### 7. Testing

Test the workflow without actual checkout:

```bash
python main.py
```

The script will:
1. Fetch new orders
2. Process personalization
3. Prepare supplier orders
4. Add items to cart (STOP before checkout)

### 8. Production Deployment

For cloud deployment, consider:
- **GitHub Actions** (free)
- **Render.com** (free tier)
- **Railway.app** (free tier)
- **Heroku** (paid)

## Workflow

1. **Scheduled Run**: Script runs at configured time (default 6 PM)
2. **Order Fetching**: Retrieves new orders from Etsy
3. **Classification**: Determines if personalization needed and customer location
4. **US Orders**: Downloads shipping labels
5. **International Orders**: Extracts address, IOSS number, order value
6. **Personalization**: Edits PSD files with customer details
7. **Supplier Processing**: 
   - Navigates to product page
   - Selects hologram type
   - Uploads printing file
   - Uploads label (US) or fills international details
   - Adds to cart
8. **Checkout**: Processes all cart items with saved payment

## File Structure

```
project-tracker/
├── main.py                      # Main entry point and scheduler
├── config.py                    # Configuration management
├── etsy_api.py                  # Etsy API integration
├── google_sheets_catalog.py     # Google Sheets catalog management
├── image_processor.py           # PSD editing and image processing
├── supplier_automation.py       # Supplier website automation
├── order_processor.py           # Main order processing logic
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Your actual credentials (not in git)
├── processed_orders.json        # Track processed orders
├── output/                      # Generated files (labels, PNGs)
└── temp/                        # Temporary files
```

## Customization

### Photopea Integration

The system currently uses local PSD editing as a fallback. To integrate Photopea:

1. Check Photopea API availability
2. Add API key to `.env`
3. Modify `image_processor.py` to use Photopea API

### Supplier Form Fields

Update `supplier_automation.py` if the supplier website form structure changes:

- CSS selectors for form fields
- Field names and IDs
- Button selectors

### Scheduling

Change the schedule time in `.env`:

```env
SCHEDULE_TIME=18:00  # 6 PM in 24-hour format
TIMEZONE=America/New_York
```

## Troubleshooting

### Etsy API Issues
- Verify API credentials in `.env`
- Check Etsy API status
- Ensure access token is valid

### Google Sheets Issues
- Re-authenticate if token expires
- Check sheet ID is correct
- Verify sheet structure matches expected format

### Supplier Automation Issues
- Check website structure hasn't changed
- Verify login credentials
- Update CSS selectors if website changes

### Image Processing Issues
- Ensure PSD files are accessible
- Check file permissions
- Verify Pillow and psd-tools are installed

## Security Notes

- Never commit `.env` file to version control
- Use strong, unique passwords
- Rotate API keys regularly
- Limit API permissions to minimum required
- Consider using secret management services for production

## Future Enhancements

- [ ] Email notification processing
- [ ] Order confirmation tracking
- [ ] Error handling and retry logic
- [ ] Webhook support for real-time processing
- [ ] Dashboard for monitoring
- [ ] Multi-supplier support
- [ ] Advanced personalization templates

## License

This project is for personal/commercial use. Ensure compliance with Etsy's API terms of service and supplier website terms of use.
