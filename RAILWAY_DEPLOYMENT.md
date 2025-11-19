# Railway Deployment Guide

This guide will help you deploy DealFlow AI to Railway for production hosting.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. GitHub account (your code is already on GitHub)
3. All your API keys and credentials ready

## Step 1: Create a New Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `DealsParser` repository
5. Railway will automatically detect it's a Python project

## Step 2: Configure Environment Variables

Railway will need all your environment variables. Go to your project settings and add the following variables:

### Required Variables:

- `OPENAI_API_KEY` - Your OpenAI API key
- `AIRTABLE_PAT` - Your Airtable Personal Access Token
- `AIRTABLE_BASE_ID` - Your Airtable Base ID
- `AIRTABLE_TABLE_NAME` - Your Airtable deals table name
- `AIRTABLE_CONTACTS_TABLE` - Your Airtable contacts table name
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `S3_BUCKET` - Your S3 bucket name
- `S3_REGION` - Your S3 region (e.g., `us-east-1`)

### Optional Variables:

- `SMARTY_AUTH_ID` - Smarty Streets API auth ID (for address validation)
- `SMARTY_AUTH_TOKEN` - Smarty Streets API auth token
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `REDIRECT_URI` - Your Railway app URL (will be set automatically after deployment)

## Step 3: Deploy

1. Railway will automatically start building and deploying your app
2. The build process will:
   - Install Python dependencies from `requirements.txt`
   - Run the app using the command in `Procfile`
3. Once deployed, Railway will provide you with a public URL

## Step 4: Update Redirect URI

After deployment, update your `REDIRECT_URI` environment variable in Railway to match your new Railway URL:
- Format: `https://your-app-name.railway.app`

Also update this in your Google OAuth settings if you're using Google authentication.

## Step 5: Configure Custom Domain (Optional)

1. Go to your Railway project settings
2. Click on "Settings" → "Networking"
3. Add your custom domain
4. Follow Railway's instructions to configure DNS

## Monitoring & Logs

- View logs in real-time in the Railway dashboard
- Railway automatically restarts your app if it crashes
- Monitor resource usage in the Railway dashboard

## Key Differences from Streamlit Cloud

✅ **No sleep mode** - Your app stays running 24/7
✅ **Better performance** - More resources available
✅ **Custom domains** - Use your own domain name
✅ **Better logging** - Access to full application logs
✅ **Environment variables** - Easier to manage secrets
✅ **Auto-scaling** - Railway can scale based on traffic

## Troubleshooting

### App won't start
- Check that all required environment variables are set
- Review the logs in Railway dashboard
- Ensure `requirements.txt` has all dependencies

### Port errors
- Railway automatically sets the `PORT` environment variable
- The `Procfile` uses `$PORT` to bind to the correct port
- No manual port configuration needed

### Environment variable issues
- Make sure variable names match exactly (case-sensitive)
- Check that values don't have extra spaces
- Verify API keys are valid and have proper permissions

## Cost

Railway offers:
- **Free tier**: $5 credit per month (good for testing)
- **Pay-as-you-go**: Only pay for what you use
- **Hobby plan**: $20/month for predictable pricing

Check [railway.app/pricing](https://railway.app/pricing) for current pricing.

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)

